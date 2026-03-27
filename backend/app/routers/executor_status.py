"""Executor status router."""
from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db_session
from app.services import executor_status_service
from app.utils.response import error, ok

router = APIRouter(prefix="/executor", tags=["executor"])
active_executors = executor_status_service.active_executors


@router.get("/status")
def get_status():
    """Get executor status."""
    try:
        return ok(data=executor_status_service.get_executor_status())
    except Exception:
        return error(message="Failed to get executor status")


@router.get("/tasks")
def get_active_tasks():
    """Get active executor tasks."""
    try:
        return ok(data=executor_status_service.get_active_tasks())
    except Exception:
        return error(message="Failed to get active tasks")


@router.get("/devices")
def get_executor_devices(db: Session = Depends(get_db_session)):
    """Get devices connected to executors."""
    try:
        return ok(data=executor_status_service.get_executor_devices(db))
    except Exception:
        return error(code=500, message="Failed to get executor devices")


def register_executor(executor_id: str, connection_info: Dict[str, Any]):
    executor_status_service.register_executor(executor_id, connection_info)


def unregister_executor(executor_id: str):
    executor_status_service.unregister_executor(executor_id)


def update_executor_heartbeat(executor_id: str):
    executor_status_service.update_executor_heartbeat(executor_id)


def update_executor_status(executor_id: str, status_data: Dict[str, Any]):
    executor_status_service.update_executor_status(executor_id, status_data)


def update_executor_task(executor_id: str, task_data: Dict[str, Any]):
    executor_status_service.update_executor_task(executor_id, task_data)


__all__ = [
    "router",
    "register_executor",
    "unregister_executor",
    "update_executor_heartbeat",
    "update_executor_status",
    "update_executor_task",
]
