"""
History router - execution history
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db_session
from app.services.history_service import (
    get_history_statistics,
    list_history_records,
    parse_history_date_filters,
)
from app.schemas.history import *
from app.schemas.common import ApiResponse, PaginatedResponse, ErrorCode
from app.utils.response import ok, error
from app.utils.pagination import calculate_offset

router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=ApiResponse[PaginatedResponse[HistoryResponse]])
def list_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    result: str = Query(None),
    testcase_name: str = Query(None),
    date_from: str = Query(None),
    date_to: str = Query(None),
    db: Session = Depends(get_db_session)
):
    """Get execution history"""
    skip = calculate_offset(page, page_size)
    parsed = parse_history_date_filters(date_from, date_to)
    if parsed.error_message:
        return error(code=ErrorCode.VALIDATION_ERROR, message=parsed.error_message)

    results, total = list_history_records(
        db,
        skip=skip,
        limit=page_size,
        result=result,
        testcase_name=testcase_name,
        date_from=parsed.date_from,
        date_to=parsed.date_to,
    )

    response_data = PaginatedResponse(
        items=results,
        total=total,
        page=page,
        page_size=page_size
    )
    return ok(data=response_data)


@router.get("/stats", response_model=ApiResponse[HistoryStats])
def get_statistics(
    days: int = Query(7, ge=1, le=90, description="Days for statistics"),
    db: Session = Depends(get_db_session)
):
    """Get execution statistics"""
    return ok(data=get_history_statistics(db, days=days))
