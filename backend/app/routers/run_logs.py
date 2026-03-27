"""Run logs router."""
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db_session
from app.schemas.common import ApiResponse
from app.services.run_log_service import list_run_logs
from app.utils.response import ok

router = APIRouter(prefix="/run-logs", tags=["run-logs"])


@router.get("/{task_id}", response_model=ApiResponse[List])
def get_run_logs(task_id: str, db: Session = Depends(get_db_session)):
    """Get logs for a task."""
    return ok(data=list_run_logs(db, task_id))
