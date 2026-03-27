"""Screens router."""
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db_session
from app.schemas.common import ApiResponse, PaginatedResponse
from app.schemas.screen import ScreenCreate, ScreenDetailResponse, ScreenResponse, ScreenUpdate
from app.services.screen_service import (
    create_screen as create_screen_service,
    delete_screen as delete_screen_service,
    get_screen_detail,
    list_screen_elements,
    list_screens as list_screens_service,
    update_screen as update_screen_service,
)
from app.utils.pagination import calculate_offset
from app.utils.response import error, ok

router = APIRouter(prefix="/screens", tags=["screens"])


@router.get("", response_model=ApiResponse[PaginatedResponse[ScreenResponse]])
def list_screens(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    search: str = Query(None),
    project_id: Optional[int] = Query(None),
    db: Session = Depends(get_db_session),
):
    """Get screen list."""
    results, total = list_screens_service(
        db,
        skip=calculate_offset(page, page_size),
        limit=page_size,
        search=search,
        project_id=project_id,
    )
    return ok(data=PaginatedResponse(items=results, total=total, page=page, page_size=page_size))


@router.get("/{screen_id}", response_model=ApiResponse[ScreenDetailResponse])
def get_screen(screen_id: int, db: Session = Depends(get_db_session)):
    """Get screen by ID."""
    return ok(data=get_screen_detail(db, screen_id))


@router.post("", response_model=ApiResponse[ScreenResponse])
def create_screen(screen_in: ScreenCreate, db: Session = Depends(get_db_session)):
    """Create screen."""
    response, validation_error = create_screen_service(db, screen_in)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(data=response, message="Screen created successfully")


@router.put("/{screen_id}", response_model=ApiResponse[ScreenResponse])
def update_screen(screen_id: int, screen_in: ScreenUpdate, db: Session = Depends(get_db_session)):
    """Update screen."""
    response, validation_error = update_screen_service(db, screen_id=screen_id, screen_in=screen_in)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(data=response, message="Screen updated successfully")


@router.delete("/{screen_id}", response_model=ApiResponse)
def delete_screen(screen_id: int, db: Session = Depends(get_db_session)):
    """Delete screen."""
    validation_error = delete_screen_service(db, screen_id)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(message="Screen deleted successfully")


@router.get("/{screen_id}/elements", response_model=ApiResponse[List])
def get_screen_elements(screen_id: int, db: Session = Depends(get_db_session)):
    """Get all elements in a screen."""
    return ok(data=list_screen_elements(db, screen_id))
