"""Executor status router."""
import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db_session
from app.services import executor_status_service
from app.utils.response import error, ok

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/executor", tags=["executor"])


@router.get("/status")
async def get_status():
    """Get executor status."""
    try:
        data = await executor_status_service.get_executor_status()
        return ok(data=data)
    except Exception as e:
        logger.error(f"Failed to get executor status: {e}", exc_info=True)
        return error(code=5000, message="Failed to get executor status")


@router.get("/tasks")
async def get_active_tasks():
    """Get active executor tasks."""
    try:
        data = await executor_status_service.get_active_tasks()
        return ok(data=data)
    except Exception as e:
        logger.error(f"Failed to get active tasks: {e}", exc_info=True)
        return error(code=5001, message="Failed to get active tasks")


@router.get("/devices")
async def get_executor_devices(db: Session = Depends(get_db_session)):
    """Get devices connected to executors."""
    try:
        data = await executor_status_service.get_executor_devices(db)
        return ok(data=data)
    except Exception as e:
        logger.error(f"Failed to get executor devices: {e}", exc_info=True)
        return error(code=5002, message="Failed to get executor devices")


async def register_executor(executor_id: str, connection_info: Dict[str, Any]) -> bool:
    """Register an executor. Returns True if successful."""
    try:
        result = await executor_status_service.register_executor(
            executor_id, connection_info
        )
        if not result:
            logger.warning(f"Executor registration failed: limit reached for {executor_id}")
        return result
    except Exception as e:
        logger.error(f"Failed to register executor {executor_id}: {e}", exc_info=True)
        return False


async def unregister_executor(executor_id: str) -> bool:
    """Unregister an executor. Returns True if executor existed."""
    try:
        return await executor_status_service.unregister_executor(executor_id)
    except Exception as e:
        logger.error(f"Failed to unregister executor {executor_id}: {e}", exc_info=True)
        return False


async def update_executor_heartbeat(executor_id: str) -> bool:
    """Update executor heartbeat. Returns True if executor exists."""
    try:
        return await executor_status_service.update_executor_heartbeat(executor_id)
    except Exception as e:
        logger.error(f"Failed to update heartbeat for {executor_id}: {e}", exc_info=True)
        return False


async def update_executor_status(executor_id: str, status_data: Dict[str, Any]) -> None:
    """Update executor status."""
    try:
        await executor_status_service.update_executor_status(executor_id, status_data)
    except Exception as e:
        logger.error(f"Failed to update status for {executor_id}: {e}", exc_info=True)


async def update_executor_task(executor_id: str, task_data: Dict[str, Any]) -> None:
    """Update executor task."""
    try:
        await executor_status_service.update_executor_task(executor_id, task_data)
    except Exception as e:
        logger.error(f"Failed to update task for {executor_id}: {e}", exc_info=True)


__all__ = [
    "router",
    "register_executor",
    "unregister_executor",
    "update_executor_heartbeat",
    "update_executor_status",
    "update_executor_task",
]
