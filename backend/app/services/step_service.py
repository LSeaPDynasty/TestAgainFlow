"""Service helpers for steps endpoints."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app.models.element import Element
from app.models.screen import Screen
from app.models.step import Step
from app.repositories.element_repo import ElementRepository
from app.repositories.screen_repo import ScreenRepository
from app.repositories.step_repo import StepRepository
from app.schemas.step import AssertConfigSchema, StepCreate, StepResponse, StepUpdate, TagSchema
from app.utils.exceptions import NotFoundError

VALID_ACTIONS = {
    "click",
    "long_press",
    "input",
    "swipe",
    "hardware_back",
    "wait_element",
    "wait_time",
    "assert_text",
    "assert_exists",
    "assert_not_exists",
    "assert_color",
    "repeat",
    "break_if",
    "set",
    "call",
    "start_activity",
    "screenshot",
    "py_step",
}
DEVICE_ACTIONS = {"click", "long_press", "input", "swipe"}


@dataclass
class ServiceValidationError:
    code: int
    message: str
    data: Optional[dict] = None


def parse_tag_ids(tag_ids: Optional[str]) -> Optional[list[int]]:
    if not tag_ids:
        return None
    return [int(t) for t in tag_ids.split(",") if t.strip().isdigit()]


def list_steps(
    db: Session,
    *,
    skip: int,
    limit: int,
    search: Optional[str],
    screen_id: Optional[int],
    action_type: Optional[str],
    tag_ids: Optional[list[int]],
    project_id: Optional[int] = None,
):
    repo = StepRepository(db)
    return repo.list_with_details(
        skip=skip,
        limit=limit,
        search=search,
        screen_id=screen_id,
        action_type=action_type,
        tag_ids=tag_ids,
        project_id=project_id,
    )


def get_step_response(db: Session, step_id: int) -> Optional[StepResponse]:
    repo = StepRepository(db)
    step = repo.get_with_details(step_id)
    if not step:
        return None
    return build_step_response(db, step)


def create_step(db: Session, step_in: StepCreate) -> tuple[Optional[StepResponse], Optional[ServiceValidationError]]:
    step_repo = StepRepository(db)
    screen_repo = ScreenRepository(db)
    element_repo = ElementRepository(db)

    if not screen_repo.get(step_in.screen_id):
        return None, ServiceValidationError(code=4004, message="Screen not found")

    if step_in.element_id:
        element = element_repo.get(step_in.element_id)
        if not element:
            return None, ServiceValidationError(code=4004, message="Element not found")
        if element.screen_id != step_in.screen_id:
            return (
                None,
                ServiceValidationError(
                    code=4001,
                    message="Element does not belong to the specified screen",
                ),
            )

    if step_in.action_type not in VALID_ACTIONS:
        return None, ServiceValidationError(code=4001, message=f"Invalid action_type: {step_in.action_type}")

    if step_in.action_type in DEVICE_ACTIONS and not step_in.element_id:
        return (
            None,
            ServiceValidationError(
                code=4001,
                message=f"{step_in.action_type} action requires element_id",
            ),
        )

    if step_in.assert_config and step_in.assert_config.on_fail not in ["continue", "stop", "skip"]:
        return None, ServiceValidationError(code=4001, message="on_fail must be continue/stop/skip")

    step = step_repo.create(step_in.model_dump(exclude={"tag_ids"}))
    if step_in.tag_ids:
        step_repo.set_tags(step.id, step_in.tag_ids)

    return build_step_response(db, step), None


def update_step(
    db: Session,
    *,
    step_id: int,
    step_in: StepUpdate,
) -> tuple[Optional[StepResponse], Optional[ServiceValidationError]]:
    step_repo = StepRepository(db)
    step = step_repo.get(step_id)
    if not step:
        return None, ServiceValidationError(code=4004, message=f"Step not found: id={step_id}")

    if step_in.screen_id and not db.query(Screen).get(step_in.screen_id):
        return None, ServiceValidationError(code=4004, message="Screen not found")

    if step_in.element_id and step_in.screen_id:
        element = db.query(Element).get(step_in.element_id)
        if element and element.screen_id != step_in.screen_id:
            return (
                None,
                ServiceValidationError(
                    code=4001,
                    message="Element does not belong to the specified screen",
                ),
            )

    update_data = {
        k: v
        for k, v in step_in.model_dump().items()
        if v is not None and k != "tag_ids"
    }
    updated = step_repo.update(step_id, update_data)
    if step_in.tag_ids is not None:
        step_repo.set_tags(step_id, step_in.tag_ids)
    return build_step_response(db, updated), None


def delete_step(db: Session, step_id: int) -> Optional[ServiceValidationError]:
    repo = StepRepository(db)
    flow_count = repo.check_flow_usage(step_id)
    if flow_count > 0:
        return ServiceValidationError(
            code=4022,
            message="Step is referenced by flows",
            data={"referenced_by_flows_count": flow_count},
        )
    if not repo.delete(step_id):
        return ServiceValidationError(code=4004, message=f"Step not found: id={step_id}")
    return None


def build_step_response(db: Session, step: Step) -> StepResponse:
    step_full = (
        db.query(Step)
        .options(joinedload(Step.screen), joinedload(Step.element), joinedload(Step.tags))
        .get(step.id)
    )
    if not step_full:
        raise NotFoundError(f"Step not found: id={step.id}")

    return StepResponse(
        id=step.id,
        name=step.name,
        description=step.description,
        screen_id=step.screen_id,
        action_type=step.action_type,
        element_id=step.element_id,
        action_value=step.action_value,
        assert_config=AssertConfigSchema(**step.assert_config) if step.assert_config else None,
        wait_after_ms=step.wait_after_ms,
        screen_name=step_full.screen.name if step_full.screen else "",
        element_name=step_full.element.name if step_full.element else None,
        tags=[TagSchema(id=t.id, name=t.name) for t in step_full.tags],
        created_at=step.created_at,
        updated_at=step.updated_at,
    )
