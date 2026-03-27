"""Batch import service for recursive testcase creation from JSON."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.models.element import Element, Locator
from app.models.flow import Flow, FlowStep
from app.models.screen import Screen
from app.models.step import Step
from app.models.testcase import Testcase, TestcaseFlow

VALID_PRIORITIES = {"P0", "P1", "P2", "P3"}
DEVICE_ACTIONS = {"click", "long_press", "input", "swipe"}


class BatchImportService:
    """Create testcase and all required dependencies from one JSON document."""

    def __init__(self, db: Session):
        self.db = db

    async def import_testcase_with_dependencies(
        self,
        testcase_data: Dict[str, Any],
        project_id: Optional[int],
    ) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "success": False,
            "testcase_id": None,
            "created": {
                "screens": [],
                "elements": [],
                "steps": [],
                "flows": [],
                "testcases": [],
            },
            "reused": {
                "screens": [],
                "elements": [],
                "steps": [],
                "flows": [],
                "testcases": [],
            },
            "errors": [],
        }

        try:
            testcase_name = self._extract_testcase_name(testcase_data)
            existing = self.db.execute(
                select(Testcase).where(Testcase.name == testcase_name)
            ).scalar_one_or_none()
            if existing:
                result["success"] = True
                result["testcase_id"] = existing.id
                result["reused"]["testcases"].append(testcase_name)
                self._dedupe_result_names(result)
                return result

            setup_defs, main_defs, teardown_defs = self._extract_flow_defs(testcase_data)
            if not main_defs:
                raise ValueError("At least one main flow is required")

            flow_ids = {"setup": [], "main": [], "teardown": []}
            for role, defs in (("setup", setup_defs), ("main", main_defs), ("teardown", teardown_defs)):
                for flow_def in defs:
                    flow_id = await self._get_or_create_flow(
                        flow_def=flow_def,
                        project_id=project_id,
                        result=result,
                    )
                    flow_ids[role].append(flow_id)

            testcase = self._create_testcase(
                testcase_data=testcase_data,
                project_id=project_id,
                flow_ids=flow_ids,
                result=result,
            )
            self.db.commit()

            result["success"] = True
            result["testcase_id"] = testcase.id
            self._dedupe_result_names(result)
            return result
        except Exception as exc:
            self.db.rollback()
            result["errors"].append(str(exc))
            self._dedupe_result_names(result)
            return result

    def _extract_testcase_name(self, testcase_data: Dict[str, Any]) -> str:
        name = testcase_data.get("name") or testcase_data.get("case_name") or testcase_data.get("testcase_name")
        if not name:
            raise ValueError("Testcase name is required")
        return str(name).strip()

    def _extract_flow_defs(
        self, testcase_data: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        # Preferred structure
        setup_defs = self._normalize_flow_list(testcase_data.get("setup_flows") or testcase_data.get("setup_flow"))
        main_defs = self._normalize_flow_list(testcase_data.get("main_flows") or testcase_data.get("main_flow"))
        teardown_defs = self._normalize_flow_list(
            testcase_data.get("teardown_flows") or testcase_data.get("teardown_flow")
        )

        # Backward compatibility with older shape
        if not main_defs and testcase_data.get("flow"):
            main_defs = self._normalize_flow_list(testcase_data.get("flow"))
        if not setup_defs and testcase_data.get("setup"):
            setup_defs = self._normalize_flow_list(testcase_data.get("setup"))
        if not teardown_defs and testcase_data.get("teardown"):
            teardown_defs = self._normalize_flow_list(testcase_data.get("teardown"))

        return setup_defs, main_defs, teardown_defs

    def _normalize_flow_list(self, value: Any) -> List[Dict[str, Any]]:
        if value is None:
            return []
        if isinstance(value, dict):
            return [value]
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        raise ValueError("Flow definition must be an object or list of objects")

    async def _get_or_create_flow(
        self,
        flow_def: Dict[str, Any],
        project_id: Optional[int],
        result: Dict[str, Any],
    ) -> int:
        flow_name = str(flow_def.get("name", "")).strip()
        if not flow_name:
            raise ValueError("Flow name is required")

        existing = self.db.execute(select(Flow).where(Flow.name == flow_name)).scalar_one_or_none()
        if existing:
            result["reused"]["flows"].append(flow_name)
            return existing.id

        flow = Flow(
            name=flow_name,
            description=flow_def.get("description"),
            flow_type="standard",
            requires=flow_def.get("requires") or [],
            default_params=flow_def.get("default_params"),
            project_id=project_id,
        )
        self.db.add(flow)
        self.db.flush()

        raw_steps = flow_def.get("steps")
        if raw_steps is None:
            raw_steps = flow_def.get("step", [])
        if not isinstance(raw_steps, list) or not raw_steps:
            raise ValueError(f"Flow '{flow_name}' must contain non-empty steps list")

        for idx, step_def in enumerate(raw_steps, start=1):
            if not isinstance(step_def, dict):
                raise ValueError(f"Flow '{flow_name}' has invalid step at index {idx}")
            step_id, override_value = await self._resolve_step(step_def, project_id, result)
            self.db.add(
                FlowStep(
                    flow_id=flow.id,
                    step_id=step_id,
                    order_index=idx,
                    override_value=override_value,
                )
            )

        result["created"]["flows"].append(flow_name)
        return flow.id

    async def _resolve_step(
        self,
        step_def: Dict[str, Any],
        project_id: Optional[int],
        result: Dict[str, Any],
    ) -> Tuple[int, Optional[str]]:
        # Allow referencing existing step by id directly.
        step_id = step_def.get("step_id")
        if isinstance(step_id, int):
            existing = self.db.get(Step, step_id)
            if not existing:
                raise ValueError(f"step_id not found: {step_id}")
            return existing.id, step_def.get("override_value")

        normalized = self._normalize_step(step_def, result)
        existing = self.db.execute(
            select(Step).where(
                and_(
                    Step.name == normalized["name"],
                    Step.screen_id == normalized["screen_id"],
                    Step.action_type == normalized["action_type"],
                )
            )
        ).scalar_one_or_none()
        if existing:
            result["reused"]["steps"].append(normalized["name"])
            return existing.id, normalized.get("override_value")

        step = Step(
            name=normalized["name"],
            description=normalized.get("description"),
            screen_id=normalized["screen_id"],
            action_type=normalized["action_type"],
            element_id=normalized.get("element_id"),
            action_value=normalized.get("action_value"),
            assert_config=normalized.get("assert_config"),
            wait_after_ms=normalized.get("wait_after_ms", 0),
            continue_on_error=1 if normalized.get("continue_on_error") else 0,
            project_id=project_id,
        )
        self.db.add(step)
        self.db.flush()
        result["created"]["steps"].append(normalized["name"])
        return step.id, normalized.get("override_value")

    def _normalize_step(self, step_def: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        # Compatibility mode for legacy format like {"click": {...}} / {"exists": {...}}
        if "action_type" not in step_def:
            if "click" in step_def:
                click_data = step_def.get("click") or {}
                locator_data = click_data.get("locator") or {}
                step_def = {
                    "name": step_def.get("name"),
                    "action_type": "click",
                    "screen_name": step_def.get("screen_name"),
                    "element": {
                        "name": locator_data.get("element"),
                        "locators": [self._normalize_legacy_locator(locator_data)],
                    }
                    if locator_data
                    else None,
                    "action_value": click_data.get("value"),
                    "wait_after_ms": step_def.get("wait_after_ms", 0),
                    "continue_on_error": step_def.get("continue_on_error", False),
                }
            elif "exists" in step_def:
                exists_data = step_def.get("exists") or {}
                locator_data = exists_data.get("locator") or {}
                step_def = {
                    "name": step_def.get("name"),
                    "action_type": "assert_exists",
                    "screen_name": step_def.get("screen_name"),
                    "element": {
                        "name": locator_data.get("element"),
                        "locators": [self._normalize_legacy_locator(locator_data)],
                    }
                    if locator_data
                    else None,
                    "assert_config": {
                        "type": "exists",
                        "expected": str(exists_data.get("expected", True)).lower(),
                        "on_fail": "stop",
                    },
                    "wait_after_ms": step_def.get("wait_after_ms", 0),
                    "continue_on_error": step_def.get("continue_on_error", False),
                }
            else:
                raise ValueError(f"Unsupported step format: {step_def}")

        name = str(step_def.get("name", "")).strip()
        if not name:
            raise ValueError("Step name is required")

        action_type = str(step_def.get("action_type", "")).strip()
        if not action_type:
            raise ValueError(f"Step '{name}' action_type is required")

        screen_ref = step_def.get("screen") or step_def.get("screen_name")
        if not screen_ref:
            raise ValueError(f"Step '{name}' screen/screen_name is required")
        screen_id = self._get_or_create_screen(screen_ref, result)

        element_id = None
        element_data = step_def.get("element")
        if element_data is not None:
            element_id = self._get_or_create_element(element_data, screen_id, result)
        elif action_type in DEVICE_ACTIONS:
            raise ValueError(f"Step '{name}' action_type '{action_type}' requires element")

        return {
            "name": name,
            "description": step_def.get("description"),
            "screen_id": screen_id,
            "action_type": action_type,
            "element_id": element_id,
            "action_value": step_def.get("action_value"),
            "assert_config": step_def.get("assert_config"),
            "wait_after_ms": int(step_def.get("wait_after_ms", 0) or 0),
            "continue_on_error": bool(step_def.get("continue_on_error", False)),
            "override_value": step_def.get("override_value"),
        }

    def _normalize_legacy_locator(self, locator_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": locator_data.get("type", "resource-id"),
            "value": locator_data.get("value", ""),
            "priority": 1,
        }

    def _get_or_create_screen(self, screen_ref: Any, result: Dict[str, Any]) -> int:
        if isinstance(screen_ref, str):
            screen_data = {"name": screen_ref}
        elif isinstance(screen_ref, dict):
            screen_data = screen_ref
        else:
            raise ValueError(f"Invalid screen definition: {screen_ref}")

        name = str(screen_data.get("name", "")).strip()
        if not name:
            raise ValueError("screen.name is required")

        existing = self.db.execute(select(Screen).where(Screen.name == name)).scalar_one_or_none()
        if existing:
            result["reused"]["screens"].append(name)
            return existing.id

        screen = Screen(
            name=name,
            activity=screen_data.get("activity"),
            description=screen_data.get("description"),
            project_id=screen_data.get("project_id"),
        )
        self.db.add(screen)
        self.db.flush()
        result["created"]["screens"].append(name)
        return screen.id

    def _get_or_create_element(self, element_def: Dict[str, Any], screen_id: int, result: Dict[str, Any]) -> int:
        if not isinstance(element_def, dict):
            raise ValueError("element must be an object")

        name = str(element_def.get("name", "")).strip()
        if not name:
            raise ValueError("element.name is required")

        existing = self.db.execute(
            select(Element).where(and_(Element.name == name, Element.screen_id == screen_id))
        ).scalar_one_or_none()
        if existing:
            result["reused"]["elements"].append(name)
            return existing.id

        locators = element_def.get("locators")
        if not isinstance(locators, list) or not locators:
            raise ValueError(f"element '{name}' must contain non-empty locators list")

        element = Element(
            name=name,
            description=element_def.get("description"),
            screen_id=screen_id,
            project_id=element_def.get("project_id"),
        )
        self.db.add(element)
        self.db.flush()

        for idx, loc in enumerate(locators, start=1):
            if not isinstance(loc, dict):
                raise ValueError(f"Invalid locator for element '{name}'")
            loc_type = str(loc.get("type", "")).strip()
            loc_value = str(loc.get("value", "")).strip()
            if not loc_type or not loc_value:
                raise ValueError(f"Locator type/value are required for element '{name}'")
            self.db.add(
                Locator(
                    element_id=element.id,
                    type=loc_type,
                    value=loc_value,
                    priority=int(loc.get("priority", idx)),
                )
            )

        self.db.flush()
        result["created"]["elements"].append(name)
        return element.id

    def _create_testcase(
        self,
        testcase_data: Dict[str, Any],
        project_id: Optional[int],
        flow_ids: Dict[str, List[int]],
        result: Dict[str, Any],
    ) -> Testcase:
        name = self._extract_testcase_name(testcase_data)
        priority = str(testcase_data.get("priority", "P2")).upper()
        if priority not in VALID_PRIORITIES:
            raise ValueError(f"Invalid priority '{priority}', must be one of P0/P1/P2/P3")

        timeout = int(testcase_data.get("timeout", 120))
        if timeout <= 0:
            raise ValueError("timeout must be greater than 0")

        testcase = Testcase(
            name=name,
            description=testcase_data.get("description"),
            priority=priority,
            timeout=timeout,
            params=testcase_data.get("params"),
            project_id=project_id,
        )
        self.db.add(testcase)
        self.db.flush()

        for role in ("setup", "main", "teardown"):
            for order, flow_id in enumerate(flow_ids[role], start=1):
                self.db.add(
                    TestcaseFlow(
                        testcase_id=testcase.id,
                        flow_id=flow_id,
                        flow_role=role,
                        order_index=order,
                        enabled=True,
                        params=None,
                    )
                )

        result["created"]["testcases"].append(name)
        return testcase

    def _dedupe_result_names(self, result: Dict[str, Any]) -> None:
        for bucket in ("created", "reused"):
            for key, values in result[bucket].items():
                if not isinstance(values, list):
                    continue
                result[bucket][key] = list(dict.fromkeys([v for v in values if v]))
