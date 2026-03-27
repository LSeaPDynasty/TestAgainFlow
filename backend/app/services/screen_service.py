"""Service helpers for screens endpoints."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from app.repositories.element_repo import ElementRepository
from app.repositories.screen_repo import ScreenRepository
from app.schemas.screen import ScreenCreate, ScreenDetailResponse, ScreenResponse, ScreenUpdate
from app.utils.exceptions import NotFoundError

logger = logging.getLogger(__name__)


@dataclass
class ServiceValidationError:
    code: int
    message: str
    data: Optional[dict] = None


def list_screens(
    db: Session,
    *,
    skip: int,
    limit: int,
    search: Optional[str],
    project_id: Optional[int],
):
    repo = ScreenRepository(db)
    return repo.list_with_element_counts(
        skip=skip,
        limit=limit,
        search=search,
        project_id=project_id,
    )


def get_screen_detail(db: Session, screen_id: int) -> ScreenDetailResponse:
    repo = ScreenRepository(db)
    screen = repo.get_with_elements(screen_id)
    if not screen:
        raise NotFoundError(f"Screen not found: id={screen_id}")

    elements = [{"id": e.id, "name": e.name} for e in screen.elements]
    return ScreenDetailResponse(
        id=screen.id,
        name=screen.name,
        activity=screen.activity,
        description=screen.description,
        project_id=screen.project_id,
        element_count=len(elements),
        elements=elements,
        created_at=screen.created_at,
        updated_at=screen.updated_at,
    )


def create_screen(db: Session, screen_in: ScreenCreate) -> tuple[Optional[ScreenResponse], Optional[ServiceValidationError]]:
    repo = ScreenRepository(db)
    if repo.get_by_name(screen_in.name):
        return None, ServiceValidationError(code=4009, message="Screen name already exists")

    screen = repo.create(screen_in.model_dump())
    return (
        ScreenResponse(
            id=screen.id,
            name=screen.name,
            activity=screen.activity,
            description=screen.description,
            project_id=screen.project_id,
            element_count=0,
            created_at=screen.created_at,
            updated_at=screen.updated_at,
        ),
        None,
    )


def update_screen(
    db: Session,
    *,
    screen_id: int,
    screen_in: ScreenUpdate,
) -> tuple[Optional[ScreenResponse], Optional[ServiceValidationError]]:
    repo = ScreenRepository(db)
    screen = repo.get(screen_id)
    if not screen:
        raise NotFoundError(f"Screen not found: id={screen_id}")

    if screen_in.name and screen_in.name != screen.name and repo.get_by_name(screen_in.name):
        return None, ServiceValidationError(code=4009, message="Screen name already exists")

    update_data = {k: v for k, v in screen_in.model_dump().items() if v is not None}
    updated = repo.update(screen_id, update_data)
    return (
        ScreenResponse(
            id=updated.id,
            name=updated.name,
            activity=updated.activity,
            description=updated.description,
            project_id=updated.project_id,
            element_count=repo.get_element_count(screen_id),
            created_at=updated.created_at,
            updated_at=updated.updated_at,
        ),
        None,
    )


def delete_screen(db: Session, screen_id: int) -> Optional[ServiceValidationError]:
    """Delete screen (cascade delete all elements)"""
    repo = ScreenRepository(db)
    element_repo = ElementRepository(db)

    # 记录元素数量用于日志
    element_count = element_repo.count_by_screen(screen_id)
    logger.info(f"Deleting screen {screen_id} with {element_count} elements (cascade delete)")

    if not repo.delete(screen_id):
        raise NotFoundError(f"Screen not found: id={screen_id}")
    return None


def list_screen_elements(db: Session, screen_id: int) -> list[dict]:
    screen_repo = ScreenRepository(db)
    if not screen_repo.get(screen_id):
        raise NotFoundError(f"Screen not found: id={screen_id}")

    element_repo = ElementRepository(db)
    elements = element_repo.list_by_screen(screen_id)
    result = []
    for elem in elements:
        elem_full = element_repo.get_with_locators(elem.id)
        result.append(
            {
                "id": elem.id,
                "name": elem.name,
                "description": elem.description,
                "locators": [
                    {
                        "id": loc.id,
                        "type": loc.type,
                        "value": loc.value,
                        "priority": loc.priority,
                    }
                    for loc in elem_full.locators
                ]
                if elem_full
                else [],
            }
        )
    return result
