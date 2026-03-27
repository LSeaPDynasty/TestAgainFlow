"""Suites router."""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db_session
from app.schemas.common import ApiResponse, ErrorCode, PaginatedResponse
from app.schemas.suite import (
    SuiteCreate,
    SuiteDetailResponse,
    SuiteResponse,
    SuiteToggleRequest,
    SuiteUpdate,
)
from app.services.suite_service import (
    create_suite as create_suite_service,
    delete_suite as delete_suite_service,
    get_suite_detail,
    list_suites as list_suites_service,
    toggle_suite as toggle_suite_service,
    update_suite as update_suite_service,
)
from app.utils.pagination import calculate_offset
from app.utils.response import error, ok

router = APIRouter(prefix="/suites", tags=["suites"])


@router.get("", response_model=ApiResponse[PaginatedResponse[SuiteResponse]])
def list_suites(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    project_id: Optional[int] = Query(None),
    db: Session = Depends(get_db_session),
):
    """Get suite list."""
    results, total = list_suites_service(
        db,
        skip=calculate_offset(page, page_size),
        limit=page_size,
        project_id=project_id,
    )
    return ok(data=PaginatedResponse(items=results, total=total, page=page, page_size=page_size))


@router.get("/{suite_id}", response_model=ApiResponse[SuiteDetailResponse])
def get_suite(suite_id: int, db: Session = Depends(get_db_session)):
    """Get suite by ID."""
    response = get_suite_detail(db, suite_id)
    if not response:
        return error(code=ErrorCode.NOT_FOUND, message=f"Suite not found: id={suite_id}")
    return ok(data=response)


@router.post("", response_model=ApiResponse[SuiteResponse])
def create_suite(suite_in: SuiteCreate, db: Session = Depends(get_db_session)):
    """Create suite."""
    response, validation_error = create_suite_service(db, suite_in)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(data=response, message="Suite created successfully")


@router.put("/{suite_id}", response_model=ApiResponse[SuiteResponse])
def update_suite(suite_id: int, suite_in: SuiteUpdate, db: Session = Depends(get_db_session)):
    """Update suite."""
    response, validation_error = update_suite_service(db, suite_id=suite_id, suite_in=suite_in)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(data=response, message="Suite updated successfully")


@router.delete("/{suite_id}", response_model=ApiResponse)
def delete_suite(suite_id: int, db: Session = Depends(get_db_session)):
    """Delete suite."""
    validation_error = delete_suite_service(db, suite_id)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(message="Suite deleted successfully")


@router.patch("/{suite_id}/toggle", response_model=ApiResponse[SuiteResponse])
def toggle_suite(suite_id: int, req: SuiteToggleRequest, db: Session = Depends(get_db_session)):
    """Toggle suite enabled state."""
    response, validation_error = toggle_suite_service(db, suite_id=suite_id, req=req)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(data=response, message="Suite state updated")
