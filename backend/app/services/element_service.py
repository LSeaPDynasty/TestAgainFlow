"""Service helpers for element endpoints."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from app.models.screen import Screen
from app.repositories.element_repo import ElementRepository
from app.repositories.screen_repo import ScreenRepository
from app.schemas.element import ElementCreate, ElementResponse, ElementUpdate, LocatorSchema


@dataclass
class ServiceValidationError:
    code: int
    message: str
    data: Optional[dict] = None


def list_elements(
    db: Session,
    *,
    skip: int,
    limit: int,
    search: Optional[str],
    screen_id: Optional[int],
    locator_type: Optional[str],
):
    repo = ElementRepository(db)
    return repo.list_with_details(
        skip=skip,
        limit=limit,
        search=search,
        screen_id=screen_id,
        locator_type=locator_type,
    )


def get_element(db: Session, element_id: int) -> tuple[Optional[ElementResponse], Optional[ServiceValidationError]]:
    repo = ElementRepository(db)
    element = repo.get_with_locators(element_id)
    if not element:
        return None, ServiceValidationError(code=4004, message="Element not found")
    return _build_element_response(db, element), None


def create_element(db: Session, element_in: ElementCreate) -> tuple[Optional[ElementResponse], Optional[ServiceValidationError]]:
    element_repo = ElementRepository(db)
    screen_repo = ScreenRepository(db)

    if not element_in.name or not element_in.name.strip():
        return None, ServiceValidationError(code=4001, message="Element name cannot be empty")
    if not element_in.locators or len(element_in.locators) == 0:
        return None, ServiceValidationError(code=4001, message="Element must have at least one locator")
    if not screen_repo.get(element_in.screen_id):
        return None, ServiceValidationError(code=4004, message="Screen not found")
    if element_repo.get_by_name_in_screen(element_in.name, element_in.screen_id):
        return None, ServiceValidationError(code=4009, message="Element with this name already exists in the screen")

    element = element_repo.create_with_locators(element_in.model_dump())
    return _build_element_response(db, element), None


def update_element(
    db: Session,
    *,
    element_id: int,
    element_in: ElementUpdate,
) -> tuple[Optional[ElementResponse], Optional[ServiceValidationError]]:
    repo = ElementRepository(db)
    element = repo.get(element_id)
    if not element:
        return None, ServiceValidationError(code=4004, message="Element not found")

    if element_in.name and element_in.name != element.name:
        existing = repo.get_by_name_in_screen(element_in.name, element.screen_id)
        if existing and existing.id != element_id:
            return None, ServiceValidationError(code=4009, message="Element with this name already exists in the screen")

    update_data = {k: v for k, v in element_in.model_dump().items() if v is not None}
    updated = repo.update_with_locators(element_id, update_data)
    return _build_element_response(db, updated), None


def delete_element(db: Session, element_id: int) -> Optional[ServiceValidationError]:
    repo = ElementRepository(db)
    step_count = repo.check_step_usage(element_id)
    if step_count > 0:
        return ServiceValidationError(
            code=4022,
            message="Element is referenced by steps",
            data={"referenced_by_steps_count": step_count},
        )
    if not repo.delete(element_id):
        return ServiceValidationError(code=4004, message="Element not found")
    return None


async def test_element_locator(
    db: Session,
    *,
    element_id: int,
    device_serial: str,
    locator_index: int,
) -> tuple[Optional[dict], Optional[ServiceValidationError]]:
    try:
        repo = ElementRepository(db)
        element = repo.get_with_locators(element_id)
        if not element:
            return None, ServiceValidationError(code=404, message="Element not found")
        if not element.locators:
            return None, ServiceValidationError(code=400, message="Element has no locators")
        if locator_index >= len(element.locators):
            return None, ServiceValidationError(code=400, message="Locator index out of range")

        locator = element.locators[locator_index]
        from app.services.executor_bridge import ExecutorBridgeError, request_executor

        try:
            result = await request_executor(
                "test_element",
                {
                    "device_serial": device_serial,
                    "locator_type": locator.type,
                    "locator_value": locator.value,
                },
                request_prefix=f"test_element_{element_id}",
                timeout_seconds=30.0,
                device_serial=device_serial,
            )
        except ExecutorBridgeError as exc:
            return None, ServiceValidationError(code=exc.http_code, message=exc.message)

        element_result = result.payload.get("result", {})
        return {
            "found": element_result.get("found", False),
            "locator_type": locator.type,
            "locator_value": locator.value,
            "bounds": element_result.get("bounds"),
            "screenshot_url": element_result.get("screenshot_url"),
            "executor_id": result.executor_id,
            "request_id": result.request_id,
        }, None
    except Exception as exc:
        return None, ServiceValidationError(code=500, message=f"Element test failed: {str(exc)}")


def _build_element_response(db: Session, element: object) -> ElementResponse:
    screen = db.query(Screen).get(element.screen_id)
    return ElementResponse(
        id=element.id,
        name=element.name,
        description=element.description,
        screen_id=element.screen_id,
        screen_name=screen.name if screen else "",
        locators=[
            LocatorSchema(id=loc.id, type=loc.type, value=loc.value, priority=loc.priority)
            for loc in element.locators
        ],
        created_at=element.created_at,
        updated_at=element.updated_at,
    )
