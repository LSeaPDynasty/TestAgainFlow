"""Steps router."""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db_session
from app.schemas.common import ApiResponse, ErrorCode, PaginatedResponse
from app.schemas.step import StepCreate, StepResponse, StepUpdate
from app.services.step_service import (
    create_step as create_step_service,
    delete_step as delete_step_service,
    get_step_response,
    list_steps as list_steps_service,
    parse_tag_ids,
    update_step as update_step_service,
)
from app.utils.pagination import calculate_offset
from app.utils.response import error, ok

router = APIRouter(prefix="/steps", tags=["steps"])


@router.get("", response_model=ApiResponse[PaginatedResponse[StepResponse]])
def list_steps(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    search: str = Query(None),
    screen_id: int = Query(None),
    action_type: str = Query(None),
    tag_ids: str = Query(None),
    project_id: Optional[int] = Query(None),
    db: Session = Depends(get_db_session),
):
    """Get step list."""
    results, total = list_steps_service(
        db,
        skip=calculate_offset(page, page_size),
        limit=page_size,
        search=search,
        screen_id=screen_id,
        action_type=action_type,
        tag_ids=parse_tag_ids(tag_ids),
        project_id=project_id,
    )
    return ok(data=PaginatedResponse(items=results, total=total, page=page, page_size=page_size))


@router.get("/{step_id}", response_model=ApiResponse[StepResponse])
def get_step(step_id: int, db: Session = Depends(get_db_session)):
    """Get step by ID."""
    response = get_step_response(db, step_id)
    if not response:
        return error(code=ErrorCode.NOT_FOUND, message=f"Step not found: id={step_id}")
    return ok(data=response)


@router.post("", response_model=ApiResponse[StepResponse])
def create_step(step_in: StepCreate, db: Session = Depends(get_db_session)):
    """Create step."""
    response, validation_error = create_step_service(db, step_in)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(data=response, message="Step created successfully")


@router.put("/{step_id}", response_model=ApiResponse[StepResponse])
def update_step(step_id: int, step_in: StepUpdate, db: Session = Depends(get_db_session)):
    """Update step."""
    response, validation_error = update_step_service(db, step_id=step_id, step_in=step_in)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(data=response, message="Step updated successfully")


@router.delete("/{step_id}", response_model=ApiResponse)
def delete_step(step_id: int, db: Session = Depends(get_db_session)):
    """Delete step."""
    validation_error = delete_step_service(db, step_id)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(message="Step deleted successfully")
