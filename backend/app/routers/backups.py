"""Backups router."""
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db_session
from app.schemas.backup import BackupCreate, BackupResponse, RestoreRequest, RestoreResponse
from app.schemas.common import ApiResponse, ErrorCode
from app.services.backup_service import (
    create_backup as create_backup_service,
    delete_backup as delete_backup_service,
    list_backups as list_backups_service,
    restore_backup as restore_backup_service,
    run_backup,
)
from app.utils.response import error, ok

router = APIRouter(prefix="/backups", tags=["backups"])


@router.get("", response_model=ApiResponse[List[BackupResponse]])
def list_backups(resource: str = Query(None, description="Filter by resource type"), db: Session = Depends(get_db_session)):
    """List backups."""
    return ok(data=list_backups_service(db, resource))


@router.post("", response_model=ApiResponse[BackupResponse])
def create_backup(backup_in: BackupCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db_session)):
    """Create backup."""
    response = create_backup_service(db, backup_in)
    background_tasks.add_task(run_backup, response.id, backup_in.resource)
    return ok(data=response, message="Backup created")


@router.post("/{backup_id}/restore", response_model=ApiResponse[RestoreResponse])
def restore_backup(backup_id: str, req: RestoreRequest, db: Session = Depends(get_db_session)):
    """Restore from backup."""
    if not req.confirm:
        return error(code=ErrorCode.VALIDATION_ERROR, message="Confirmation required")
    return ok(data=restore_backup_service(), message="Backup restored successfully")


@router.delete("/{backup_id}", response_model=ApiResponse)
def delete_backup(backup_id: str, db: Session = Depends(get_db_session)):
    """Delete backup."""
    delete_backup_service(db, backup_id)
    return ok(message="Backup deleted successfully")
