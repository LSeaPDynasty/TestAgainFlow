"""
Test Case Generator Service - AI-powered test case generation
Intelligent resource search and test case plan generation
"""
import json
import re
import hashlib
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, func

from app.models.element import Element
from app.models.step import Step
from app.models.flow import Flow
from app.models.screen import Screen
from app.models.project import Project
from app.repositories.element_repo import ElementRepository
from app.repositories.step_repo import StepRepository
from app.repositories.flow_repo import FlowRepository
from app.services.ai.base import AIMessage
from app.services.ai.config_service import AIConfigService
from app.services.ai.prompts import build_testcase_generation_prompt, build_step_generation_prompt


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


class TestcaseGenerator:
    """
    Test case AI generation service

    Features:
    - Intelligent resource search (elements, steps, flows)
    - AI analysis of test requirements
    - Smart recommendations (reuse vs create)
    - Complete test case structure generation
    """

    def __init__(self, db: Session):
        self.db = db
        self.element_repo = ElementRepository(db)
        self.step_repo = StepRepository(db)
        self.flow_repo = FlowRepository(db)
        self.ai_config_service = AIConfigService(db)

    async def generate_from_json(
        self,
        json_data: Dict,
        project_id: Optional[int]
    ) -> Dict:
        """
        Generate test case plan from JSON description

        Args:
            json_data: User-provided JSON with test case description
            project_id: Project ID to search for resources

        Returns:
            Dict with test case plan and recommendations
        """
        result = {
            "success": False,
            "plan": None,
            "recommendations": [],
            "resources_found": {
                "elements": 0,
                "steps": 0,
                "flows": 0
            },
            "missing_resources": {
                "elements": [],
                "steps": [],
                "flows": []
            }
        }

        # Extract keywords from JSON
        keywords = self._extract_keywords(json_data)

        # Search for existing resources
        resources = await self._search_resources(keywords, project_id)

        result["resources_found"] = {
            "elements": len(resources["elements"]),
            "steps": len(resources["steps"]),
            "flows": len(resources["flows"])
        }

        # Get project context
        project_context = await self._get_project_context(project_id)

        # Build prompt and call AI
        try:
            prompt = build_testcase_generation_prompt(
                json_data,
                resources["elements"],
                resources["steps"],
                resources["flows"],
                project_context
            )

            provider = self.ai_config_service.get_provider()
            messages = [AIMessage(role="user", content=prompt)]
            response, stats = await provider.chat_completion(
                messages=messages,
                temperature=0.4,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )

            # Parse AI response
            ai_result = extract_json_from_response(response.content)

            result["success"] = True
            result["plan"] = ai_result.get("testcase_plan")
            result["recommendations"] = ai_result.get("recommendations", [])
            result["analysis"] = ai_result.get("analysis", {})
            result["missing_resources"] = ai_result.get("missing_resources", {})
            result["ai_stats"] = {
                "input_tokens": stats.input_tokens,
                "output_tokens": stats.output_tokens,
                "cost_usd": stats.cost_usd,
                "latency_ms": stats.latency_ms
            }

        except Exception as e:
            result["error"] = str(e)
            # Fallback: basic plan without AI
            result["plan"] = self._generate_basic_plan(json_data, resources)

        return result

    async def generate_step(
        self,
        step_description: str,
        project_id: Optional[int]
    ) -> Dict:
        """
        Generate a single step from description

        Args:
            step_description: Natural language description of the step
            project_id: Project ID for element search

        Returns:
            Dict with step configuration
        """
        result = {
            "success": False,
            "step": None
        }

        try:
            # Search for elements
            keywords = self._extract_keywords_from_text(step_description)
            elements = await self._search_elements(keywords, project_id, limit=20)

            # Get project context
            project_context = await self._get_project_context(project_id)

            # Build prompt
            prompt = build_step_generation_prompt(step_description, elements, project_context)

            # Call AI
            provider = self.ai_config_service.get_provider()
            messages = [AIMessage(role="user", content=prompt)]
            response, stats = await provider.chat_completion(
                messages=messages,
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            # Parse response
            step_config = extract_json_from_response(response.content)

            result["success"] = True
            result["step"] = step_config

        except Exception as e:
            result["error"] = str(e)

        return result

    async def _search_resources(
        self,
        keywords: List[str],
        project_id: Optional[int]
    ) -> Dict:
        """Search for existing resources by keywords"""
        resources = {
            "elements": [],
            "steps": [],
            "flows": []
        }

        # Search elements
        if keywords:
            resources["elements"] = await self._search_elements(keywords, project_id)

        # Search steps
        if keywords:
            resources["steps"] = await self._search_steps(keywords, project_id)

        # Search flows
        if keywords:
            resources["flows"] = await self._search_flows(keywords, project_id)

        return resources

    async def _search_elements(
        self,
        keywords: List[str],
        project_id: Optional[int],
        limit: int = 50
    ) -> List[Dict]:
        """Search elements by keywords"""
        elements = []

        # Build search query
        filters = {}
        if project_id:
            filters["project_id"] = project_id

        # Search by name/description
        for keyword in keywords[:5]:  # Limit keywords
            matching = self.element_repo.list(
                limit=limit,
                filters={**filters, "name": keyword}
            )
            for el in matching:
                if el.id not in [e["id"] for e in elements]:
                    elements.append(self._serialize_element(el))

        # Fill up with recent elements if not enough
        if len(elements) < limit:
            recent = self.element_repo.list(
                skip=0,
                limit=limit - len(elements),
                filters=filters
            )
            for el in recent:
                if el.id not in [e["id"] for e in elements]:
                    elements.append(self._serialize_element(el))

        return elements[:limit]

    async def _search_steps(
        self,
        keywords: List[str],
        project_id: Optional[int],
        limit: int = 30
    ) -> List[Dict]:
        """Search steps by keywords"""
        steps = []

        filters = {}
        if project_id:
            filters["project_id"] = project_id

        for keyword in keywords[:5]:
            matching = self.step_repo.list(
                limit=limit,
                filters={**filters, "name": keyword}
            )
            for step in matching:
                if step.id not in [s["id"] for s in steps]:
                    steps.append(self._serialize_step(step))

        # Fill up with recent steps
        if len(steps) < limit:
            recent = self.step_repo.list(
                skip=0,
                limit=limit - len(steps),
                filters=filters
            )
            for step in recent:
                if step.id not in [s["id"] for s in steps]:
                    steps.append(self._serialize_step(step))

        return steps[:limit]

    async def _search_flows(
        self,
        keywords: List[str],
        project_id: Optional[int],
        limit: int = 20
    ) -> List[Dict]:
        """Search flows by keywords"""
        flows = []

        filters = {}
        if project_id:
            filters["project_id"] = project_id

        for keyword in keywords[:5]:
            matching = self.flow_repo.list(
                limit=limit,
                filters={**filters, "name": keyword}
            )
            for flow in matching:
                if flow.id not in [f["id"] for f in flows]:
                    flows.append(self._serialize_flow(flow))

        # Fill up with recent flows
        if len(flows) < limit:
            recent = self.flow_repo.list(
                skip=0,
                limit=limit - len(flows),
                filters=filters
            )
            for flow in recent:
                if flow.id not in [f["id"] for f in flows]:
                    flows.append(self._serialize_flow(flow))

        return flows[:limit]

    async def _get_project_context(self, project_id: Optional[int]) -> Optional[str]:
        """Get project context information"""
        if not project_id:
            return None

        project = self.db.get(Project, project_id)
        if not project:
            return None

        return f"Project: {project.name}\nDescription: {project.description or 'N/A'}"

    def _extract_keywords(self, json_data: Dict) -> List[str]:
        """Extract keywords from JSON data"""
        keywords = []

        # From testcase name
        name = json_data.get("testcase_name", "")
        keywords.extend(self._tokenize(name))

        # From description
        description = json_data.get("description", "")
        keywords.extend(self._tokenize(description))

        # From step descriptions
        steps_desc = json_data.get("steps_description", [])
        if isinstance(steps_desc, list):
            for desc in steps_desc:
                keywords.extend(self._tokenize(desc))

        # Remove duplicates and limit
        return list(set(keywords))[:20]

    def _extract_keywords_from_text(self, text: str) -> List[str]:
        """Extract keywords from text"""
        return self._tokenize(text)[:10]

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into keywords"""
        if not text:
            return []

        import re

        # Remove special chars, lowercase, split
        words = re.sub(r'[^\w\s]', ' ', text.lower()).split()

        # Filter common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        keywords = [w for w in words if len(w) > 2 and w not in stop_words]

        return keywords

    def _serialize_element(self, element: Element) -> Dict:
        """Serialize element for AI prompt"""
        el_with_locators = self.element_repo.get_with_locators(element.id)
        screen = self.db.get(Screen, element.screen_id)

        return {
            "id": element.id,
            "name": element.name,
            "description": element.description or "",
            "screen_name": screen.name if screen else "Unknown",
            "locators": [
                {"type": loc.type, "value": loc.value, "priority": loc.priority}
                for loc in el_with_locators.locators if el_with_locators
            ]
        }

    def _serialize_step(self, step: Step) -> Dict:
        """Serialize step for AI prompt"""
        return {
            "id": step.id,
            "name": step.name,
            "step_type": step.step_type,
            "description": step.description or "",
            "element_id": step.element_id
        }

    def _serialize_flow(self, flow: Flow) -> Dict:
        """Serialize flow for AI prompt"""
        # Get step count
        stmt = select(func.count(FlowStep.id)).where(FlowStep.flow_id == flow.id)
        steps_count = self.db.execute(stmt).scalar() or 0

        return {
            "id": flow.id,
            "name": flow.name,
            "description": flow.description or "",
            "steps_count": steps_count
        }

    def _generate_basic_plan(
        self,
        json_data: Dict,
        resources: Dict
    ) -> Dict:
        """Generate basic test case plan without AI (fallback)"""
        testcase_name = json_data.get("testcase_name", "Generated Test Case")
        description = json_data.get("description", "")

        # Generate basic structure
        return {
            "name": testcase_name,
            "description": description,
            "structure": {
                "approach": "inline_steps",
                "flow_steps": []
            }
        }

    def _generate_request_hash(self, data: Dict) -> str:
        """Generate hash for caching"""
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()


# Import at the end
from app.models.flow import FlowStep
