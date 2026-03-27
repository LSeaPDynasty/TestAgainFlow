"""
Element Matcher Service - Hybrid matching strategy
Combines strict, fuzzy, and AI semantic matching
"""
import hashlib
import json
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from difflib import SequenceMatcher
import re

from app.models.element import Element, Locator
from app.models.screen import Screen
from app.repositories.element_repo import ElementRepository
from app.services.ai.base import AIMessage, ProviderType
from app.services.ai.config_service import AIConfigService
from app.services.ai.prompts import build_element_match_prompt, build_element_name_suggestion_prompt


def extract_json_from_response(content: str) -> dict:
    """
    Extract JSON from AI response, handling markdown code blocks

    Args:
        content: Raw AI response content

    Returns:
        Parsed JSON dictionary
    """
    content = content.strip()

    # Check if content is wrapped in markdown code blocks
    if content.startswith("```"):
        # Try to extract JSON from ```json ... ``` blocks
        match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if match:
            content = match.group(1)
        else:
            # Fallback: remove all backticks and language markers
            content = content.strip('`').strip()
            if content.lower().startswith('json'):
                content = content[4:].strip()

    return json.loads(content)


class ElementMatcher:
    """
    Element intelligent matching service

    Uses three-stage matching:
    1. Strict match: resource-id or exact text match
    2. Fuzzy match: text similarity using Levenshtein distance
    3. AI semantic match: LLM determines functional similarity
    """

    # Similarity threshold for fuzzy matching
    FUZZY_THRESHOLD = 0.7

    # Similarity threshold for AI semantic matching
    SEMANTIC_THRESHOLD = 0.6

    def __init__(self, db: Session):
        self.db = db
        self.element_repo = ElementRepository(db)
        self.ai_config_service = AIConfigService(db)

    async def find_similar_elements(
        self,
        dom_element: Dict,
        screen_id: Optional[int],
        project_id: Optional[int],
        threshold: float = 0.7
    ) -> Dict:
        """
        Find similar elements using hybrid matching strategy

        Args:
            dom_element: DOM element from viewer (text, resource-id, class, etc.)
            screen_id: Target screen ID
            project_id: Project ID
            threshold: Minimum similarity threshold

        Returns:
            Dict with matches and recommendations
        """
        results = {
            "matches": [],
            "can_create_new": True,
            "best_match": None,
            "search_summary": {
                "strict_matches": 0,
                "fuzzy_matches": 0,
                "ai_analyzed": 0
            }
        }

        # Stage 1: Strict matching
        strict_matches = await self._strict_match(dom_element, screen_id, project_id)
        results["search_summary"]["strict_matches"] = len(strict_matches)

        if strict_matches:
            # Perfect match found
            for match in strict_matches:
                results["matches"].append({
                    "element_id": match["element"].id,
                    "element_name": match["element"].name,
                    "similarity_score": 1.0,
                    "match_type": "strict",
                    "reason": match["reason"],
                    "locators": match["locators"]
                })

            results["best_match"] = results["matches"][0]
            results["can_create_new"] = True
            return results

        # Stage 2: Fuzzy matching
        fuzzy_matches = await self._fuzzy_match(dom_element, screen_id, project_id, threshold)
        results["search_summary"]["fuzzy_matches"] = len(fuzzy_matches)

        # Add fuzzy matches above threshold
        for match in fuzzy_matches:
            results["matches"].append({
                "element_id": match["element"].id,
                "element_name": match["element"].name,
                "similarity_score": match["score"],
                "match_type": "fuzzy",
                "reason": match["reason"],
                "locators": match["locators"]
            })

        # Stage 3: AI semantic matching (if fuzzy matches insufficient or to verify)
        try:
            ai_result = await self._ai_semantic_match(dom_element, screen_id, project_id, threshold)
            results["search_summary"]["ai_analyzed"] = 1

            if ai_result["best_match_id"]:
                # Check if already in matches
                existing = next(
                    (m for m in results["matches"] if m["element_id"] == ai_result["best_match_id"]),
                    None
                )

                if not existing:
                    results["matches"].append({
                        "element_id": ai_result["best_match_id"],
                        "element_name": ai_result.get("element_name", ""),
                        "similarity_score": ai_result.get("similarity_score", 0.0),
                        "match_type": "semantic",
                        "reason": ai_result.get("reasoning", ""),
                        "locators": ai_result.get("locators", [])
                    })

            # Always include AI recommendation (whether reusing or creating new)
            results["ai_recommendation"] = {
                "recommendation": ai_result.get("recommendation", "create_new"),
                "suggested_name": ai_result.get("suggested_name"),
                "suggested_locators": ai_result.get("suggested_locators", [])
            }

            # Also add top-level fields for frontend access
            results["suggested_name"] = ai_result.get("suggested_name")
            results["reasoning"] = ai_result.get("reasoning", "")

        except Exception as e:
            # AI matching failed, continue with what we have
            results["ai_error"] = str(e)

        # Sort by similarity score
        results["matches"].sort(key=lambda x: x["similarity_score"], reverse=True)

        # Set best match
        if results["matches"]:
            results["best_match"] = results["matches"][0]

        return results

    async def _strict_match(
        self,
        dom_element: Dict,
        screen_id: Optional[int],
        project_id: Optional[int]
    ) -> List[Dict]:
        """Stage 1: Strict matching by resource-id or exact text"""
        matches = []

        # Get resource-id from dom element
        resource_id = dom_element.get("resource-id", "")
        text = dom_element.get("text", "")

        # Search by locators
        if resource_id:
            # Find elements with resource-id locator
            elements_with_resource_id = self._search_by_locator("resource-id", resource_id, project_id)
            for element in elements_with_resource_id:
                if screen_id is None or element.screen_id == screen_id:
                    matches.append({
                        "element": element,
                        "reason": f"Exact resource-id match: {resource_id}",
                        "locators": self._get_element_locators(element)
                    })

        if not matches and text:
            # Find elements with text locator
            elements_with_text = self._search_by_locator("text", text, project_id)
            for element in elements_with_text:
                if screen_id is None or element.screen_id == screen_id:
                    matches.append({
                        "element": element,
                        "reason": f"Exact text match: {text}",
                        "locators": self._get_element_locators(element)
                    })

        return matches

    async def _fuzzy_match(
        self,
        dom_element: Dict,
        screen_id: Optional[int],
        project_id: Optional[int],
        threshold: float
    ) -> List[Dict]:
        """Stage 2: Fuzzy matching by text similarity"""
        matches = []
        text = dom_element.get("text", "")

        if not text:
            return matches

        # Get all elements in project (or screen)
        filters = {"project_id": project_id} if project_id else {}
        all_elements = self.element_repo.list(limit=1000, filters=filters)

        for element in all_elements:
            if screen_id and element.screen_id != screen_id:
                continue

            # Check text similarity
            element_text = self._get_element_text(element)
            if element_text:
                similarity = SequenceMatcher(None, text.lower(), element_text.lower()).ratio()

                if similarity >= threshold:
                    matches.append({
                        "element": element,
                        "score": similarity,
                        "reason": f"Text similarity: {similarity:.2%} between '{text}' and '{element_text}'",
                        "locators": self._get_element_locators(element)
                    })

        # Sort by score
        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches

    async def _ai_semantic_match(
        self,
        dom_element: Dict,
        screen_id: Optional[int],
        project_id: Optional[int],
        threshold: float
    ) -> Dict:
        """Stage 3: AI semantic matching"""
        # Get candidate elements (top 10 from fuzzy or recent)
        candidates = await self._get_ai_candidates(dom_element, screen_id, project_id, limit=10)

        if not candidates:
            # No candidates, ask AI to suggest new element
            return await self._ai_suggest_new(dom_element, screen_id, project_id)

        # Get screen context
        screen_context = None
        if screen_id:
            screen = self.db.get(Screen, screen_id)
            if screen:
                screen_context = f"Screen: {screen.name}, Activity: {screen.activity or 'N/A'}"

        # Build prompt
        prompt = build_element_match_prompt(dom_element, candidates, screen_context)

        # Call AI
        try:
            provider = self.ai_config_service.get_provider()
            messages = [AIMessage(role="user", content=prompt)]
            response, stats = await provider.chat_completion(
                messages=messages,
                temperature=0.3  # Lower temperature for more consistent results
            )

            # Parse response
            result = extract_json_from_response(response.content)

            # Add element name for the best match
            if result.get("best_match_id"):
                for candidate in candidates:
                    if candidate["id"] == result["best_match_id"]:
                        result["element_name"] = candidate["name"]
                        result["locators"] = candidate.get("locators", [])
                        break

            return result

        except Exception as e:
            raise Exception(f"AI semantic matching failed: {str(e)}")

    async def _ai_suggest_new(
        self,
        dom_element: Dict,
        screen_id: Optional[int],
        project_id: Optional[int]
    ) -> Dict:
        """Ask AI to suggest new element configuration"""
        screen_context = None
        if screen_id:
            screen = self.db.get(Screen, screen_id)
            if screen:
                screen_context = f"Screen: {screen.name}, Activity: {screen.activity or 'N/A'}"

        prompt = build_element_name_suggestion_prompt(dom_element, screen_context)

        try:
            provider = self.ai_config_service.get_provider()
            messages = [AIMessage(role="user", content=prompt)]
            response, stats = await provider.chat_completion(
                messages=messages,
                temperature=0.3
            )

            suggestion = extract_json_from_response(response.content)

            return {
                "best_match_id": None,
                "match_type": "none",
                "similarity_score": 0.0,
                "confidence": "high",
                "reasoning": "No existing elements found. AI suggested creating a new element.",
                "recommendation": "create_new",
                **suggestion
            }

        except Exception as e:
            # Fallback to basic suggestion
            return {
                "best_match_id": None,
                "match_type": "none",
                "similarity_score": 0.0,
                "confidence": "low",
                "reasoning": f"AI suggestion failed: {str(e)}",
                "recommendation": "create_new",
                "suggested_name": self._generate_basic_name(dom_element),
                "suggested_locators": self._generate_basic_locators(dom_element)
            }

    async def _get_ai_candidates(
        self,
        dom_element: Dict,
        screen_id: Optional[int],
        project_id: Optional[int],
        limit: int
    ) -> List[Dict]:
        """Get candidate elements for AI analysis"""
        candidates = []

        # Get recent elements from same screen or project
        filters = {}
        if project_id:
            filters["project_id"] = project_id

        elements = self.element_repo.list(limit=limit, filters=filters)

        for element in elements:
            candidates.append({
                "id": element.id,
                "name": element.name,
                "description": element.description or "",
                "locators": self._get_element_locators(element)
            })

        return candidates

    def _search_by_locator(
        self,
        locator_type: str,
        value: str,
        project_id: Optional[int]
    ) -> List[Element]:
        """Search elements by locator"""
        # Query for elements with matching locator
        stmt = select(Element).join(Locator).where(
            and_(
                Locator.type == locator_type,
                Locator.value == value
            )
        )

        if project_id:
            stmt = stmt.where(Element.project_id == project_id)

        return list(self.db.execute(stmt).scalars().all())

    def _get_element_locators(self, element: Element) -> List[Dict]:
        """Get element locators as list of dicts"""
        element_with_locators = self.element_repo.get_with_locators(element.id)
        if not element_with_locators:
            return []

        return [
            {
                "type": loc.type,
                "value": loc.value,
                "priority": loc.priority
            }
            for loc in element_with_locators.locators
        ]

    def _get_element_text(self, element: Element) -> Optional[str]:
        """Extract text value from element locators"""
        element_with_locators = self.element_repo.get_with_locators(element.id)
        if not element_with_locators:
            return None

        for locator in element_with_locators.locators:
            if locator.type == "text":
                return locator.value

        return None

    def _generate_basic_name(self, dom_element: Dict) -> str:
        """Generate basic element name from DOM element"""
        text = dom_element.get("text", "")
        class_name = dom_element.get("class", "")

        # Clean class name
        if class_name:
            class_type = class_name.split(".")[-1].replace("View", "").replace("Layout", "")
        else:
            class_type = "element"

        # Generate name
        if text:
            # Convert text to snake_case
            name_text = re.sub(r'[^\w\s]', '', text).strip().lower().replace(' ', '_')
            return f"{name_text}_{class_type}"
        else:
            return f"{class_type}"

    def _generate_basic_locators(self, dom_element: Dict) -> List[Dict]:
        """Generate basic locators from DOM element"""
        locators = []
        priority = 1

        # resource-id (highest priority if available)
        resource_id = dom_element.get("resource-id", "")
        if resource_id and resource_id and not resource_id.startswith("android:id/"):
            locators.append({
                "type": "resource-id",
                "value": resource_id,
                "priority": priority
            })
            priority += 1

        # text
        text = dom_element.get("text", "")
        if text:
            locators.append({
                "type": "text",
                "value": text,
                "priority": priority
            })
            priority += 1

        # content-desc
        content_desc = dom_element.get("content-desc", "")
        if content_desc:
            locators.append({
                "type": "content-desc",
                "value": content_desc,
                "priority": priority
            })
            priority += 1

        # xpath (fallback)
        xpath = dom_element.get("xpath", "")
        if xpath:
            locators.append({
                "type": "xpath",
                "value": xpath,
                "priority": priority
            })

        return locators

    def _generate_request_hash(self, data: Dict) -> str:
        """Generate hash for caching"""
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()


# Import at the end
from sqlalchemy import select, and_
