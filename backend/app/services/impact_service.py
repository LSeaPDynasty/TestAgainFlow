"""Service helpers for impact analysis endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from sqlalchemy.orm import Session

from app.models.flow import Flow, FlowStep
from app.models.screen import Screen
from app.models.step import Step
from app.models.testcase import Testcase, TestcaseFlow
from app.repositories.element_repo import ElementRepository
from app.repositories.flow_repo import FlowRepository
from app.repositories.screen_repo import ScreenRepository
from app.repositories.step_repo import StepRepository
from app.schemas.impact import HealthCheckResponse, ImpactResponse
from app.utils.exceptions import NotFoundError


def _find_steps_using_element(db: Session, element_id: int) -> List[dict]:
    steps = db.query(Step).filter(Step.element_id == element_id).all()
    return [{"id": s.id, "name": s.name} for s in steps]


def _find_flows_using_steps(db: Session, step_ids: List[int]) -> List[dict]:
    if not step_ids:
        return []
    flow_steps = db.query(FlowStep).filter(FlowStep.step_id.in_(step_ids)).all()
    seen: Dict[int, dict] = {}
    for fs in flow_steps:
        flow = db.query(Flow).get(fs.flow_id)
        if flow and flow.id not in seen:
            seen[flow.id] = {"id": flow.id, "name": flow.name}
    return list(seen.values())


def _find_testcases_using_flows(db: Session, flow_ids: List[int]) -> List[dict]:
    if not flow_ids:
        return []
    testcase_flows = db.query(TestcaseFlow).filter(TestcaseFlow.flow_id.in_(flow_ids)).all()
    seen: Dict[int, dict] = {}
    for tc_flow in testcase_flows:
        testcase = db.query(Testcase).get(tc_flow.testcase_id)
        if testcase and testcase.id not in seen:
            seen[testcase.id] = {"id": testcase.id, "name": testcase.name}
    return list(seen.values())


def analyze_element_impact(db: Session, element_id: int) -> ImpactResponse:
    elem_repo = ElementRepository(db)
    element = elem_repo.get(element_id)
    if not element:
        raise NotFoundError(f"Element not found: id={element_id}")

    affected_steps = _find_steps_using_element(db, element_id)
    affected_flows = _find_flows_using_steps(db, [s["id"] for s in affected_steps])
    affected_testcases = _find_testcases_using_flows(db, [f["id"] for f in affected_flows])

    return ImpactResponse(
        element_id=element_id,
        element_name=element.name,
        affected_steps=affected_steps,
        affected_flows=affected_flows,
        affected_testcases=affected_testcases,
        total_affected=len(affected_steps) + len(affected_flows) + len(affected_testcases),
    )


def analyze_screen_impact(db: Session, screen_id: int) -> ImpactResponse:
    screen_repo = ScreenRepository(db)
    screen = screen_repo.get(screen_id)
    if not screen:
        raise NotFoundError(f"Screen not found: id={screen_id}")

    elem_repo = ElementRepository(db)
    elements = elem_repo.list_by_screen(screen_id)

    all_steps: List[dict] = []
    all_flows: List[dict] = []
    all_testcases: List[dict] = []
    for element in elements:
        steps = _find_steps_using_element(db, element.id)
        flows = _find_flows_using_steps(db, [s["id"] for s in steps])
        testcases = _find_testcases_using_flows(db, [f["id"] for f in flows])
        all_steps.extend(steps)
        all_flows.extend(flows)
        all_testcases.extend(testcases)

    unique_steps = {s["id"]: s for s in all_steps}
    unique_flows = {f["id"]: f for f in all_flows}
    unique_testcases = {t["id"]: t for t in all_testcases}

    return ImpactResponse(
        screen_id=screen_id,
        screen_name=screen.name,
        affected_steps=list(unique_steps.values()),
        affected_flows=list(unique_flows.values()),
        affected_testcases=list(unique_testcases.values()),
        total_affected=len(unique_steps) + len(unique_flows) + len(unique_testcases),
    )


def analyze_step_impact(db: Session, step_id: int) -> ImpactResponse:
    step_repo = StepRepository(db)
    step = step_repo.get(step_id)
    if not step:
        raise NotFoundError(f"Step not found: id={step_id}")

    affected_flows = _find_flows_using_steps(db, [step_id])
    affected_testcases = _find_testcases_using_flows(db, [f["id"] for f in affected_flows])

    return ImpactResponse(
        step_id=step_id,
        step_name=step.name,
        affected_flows=affected_flows,
        affected_testcases=affected_testcases,
        total_affected=len(affected_flows) + len(affected_testcases),
    )


def analyze_flow_impact(db: Session, flow_id: int) -> ImpactResponse:
    flow_repo = FlowRepository(db)
    flow = flow_repo.get(flow_id)
    if not flow:
        raise NotFoundError(f"Flow not found: id={flow_id}")

    affected_testcases = _find_testcases_using_flows(db, [flow_id])
    calling_flows = flow_repo.check_flow_call_usage(flow_id)

    return ImpactResponse(
        flow_id=flow_id,
        flow_name=flow.name,
        affected_flows=calling_flows,
        affected_testcases=affected_testcases,
        total_affected=len(calling_flows) + len(affected_testcases),
    )


def start_health_check_task() -> HealthCheckResponse:
    task_id = f"health_check_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    return HealthCheckResponse(task_id=task_id, status="running")
