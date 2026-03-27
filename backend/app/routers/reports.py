"""
Reports router
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db_session
from app.services.reporting import get_report_summary as build_report_summary
from app.schemas.report import *
from app.schemas.common import ApiResponse
from app.utils.response import ok

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/summary", response_model=ApiResponse[HistoryStats])
def get_report_summary(
    date_from: str = Query(None, description="Start date (ISO format)"),
    date_to: str = Query(None, description="End date (ISO format)"),
    suite_id: int = Query(None, description="Filter by suite"),
    db: Session = Depends(get_db_session)
):
    """Get report summary data"""
    return ok(data=build_report_summary(db, date_from=date_from, date_to=date_to, suite_id=suite_id))
