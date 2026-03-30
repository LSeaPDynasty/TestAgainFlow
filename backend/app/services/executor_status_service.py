"""Service helpers for executor status."""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.repositories.device_repo import DeviceRepository

# Constants for configuration
MAX_EXECUTORS = 100  # Maximum number of executors to track
EXECUTOR_TTL_SECONDS = 3600  # Executor TTL in seconds (1 hour)
TASK_CLEANUP_INTERVAL = 300  # Task cleanup interval in seconds (5 minutes)

# Completed task states that should be cleaned up
COMPLETED_TASK_STATES = {"completed", "failed", "cancelled", "stopped", "success"}


@dataclass
class ExecutorInfo:
    """Thread-safe executor information container."""
    status: str = "connected"
    connected_at: str = ""
    last_heartbeat: str = ""
    active_tasks: int = 0
    queue_size: int = 0
    tasks: list = field(default_factory=list)
    created_at: float = field(default_factory=time.time)


class ExecutorRegistry:
    """Thread-safe registry for executor status with automatic cleanup."""

    def __init__(self):
        self._executors: Dict[str, ExecutorInfo] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task: asyncio.Task | None = None

    def start_cleanup_task(self) -> None:
        """Start background cleanup task."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())

    async def _periodic_cleanup(self) -> None:
        """Periodically clean up expired executors and completed tasks."""
        while True:
            try:
                await asyncio.sleep(TASK_CLEANUP_INTERVAL)
                await self.cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception:
                # Log error but continue cleanup loop
                pass

    async def cleanup_expired(self) -> Dict[str, int]:
        """Clean up expired executors and completed tasks.
        Returns statistics about what was cleaned.
        """
        now = time.time()
        removed_executors = 0
        cleaned_tasks = 0

        async with self._lock:
            # Remove expired executors
            expired_ids = []
            for executor_id, info in self._executors.items():
                # Remove executor if TTL exceeded
                if (now - info.created_at) > EXECUTOR_TTL_SECONDS:
                    expired_ids.append(executor_id)
                    continue

                # Clean up completed tasks within active executors
                original_task_count = len(info.tasks)
                info.tasks = [
                    t for t in info.tasks
                    if t.get("status") not in COMPLETED_TASK_STATES
                ]
                cleaned_tasks += original_task_count - len(info.tasks)
                info.active_tasks = len(info.tasks)

            # Remove expired executors
            for executor_id in expired_ids:
                del self._executors[executor_id]
                removed_executors += 1

        return {"removed_executors": removed_executors, "cleaned_tasks": cleaned_tasks}

    async def get_all(self) -> Dict[str, Dict[str, Any]]:
        """Get all executors as dict (for backward compatibility)."""
        async with self._lock:
            return {
                executor_id: {
                    "status": info.status,
                    "connected_at": info.connected_at,
                    "last_heartbeat": info.last_heartbeat,
                    "active_tasks": info.active_tasks,
                    "queue_size": info.queue_size,
                    "tasks": info.tasks,
                }
                for executor_id, info in self._executors.items()
            }

    async def register(
        self,
        executor_id: str,
        connection_info: Dict[str, Any]
    ) -> bool:
        """Register a new executor. Returns False if limit reached."""
        async with self._lock:
            if len(self._executors) >= MAX_EXECUTORS:
                return False

            self._executors[executor_id] = ExecutorInfo(
                status="connected",
                connected_at=connection_info.get("connected_at", ""),
                last_heartbeat=connection_info.get("connected_at", ""),
                active_tasks=0,
                queue_size=0,
                tasks=[],
            )
            return True

    async def unregister(self, executor_id: str) -> bool:
        """Unregister an executor. Returns True if existed."""
        async with self._lock:
            if executor_id in self._executors:
                del self._executors[executor_id]
                return True
            return False

    async def update_heartbeat(self, executor_id: str) -> bool:
        """Update executor heartbeat. Returns True if executor exists."""
        async with self._lock:
            if executor_id in self._executors:
                self._executors[executor_id].last_heartbeat = (
                    datetime.now(timezone.utc).isoformat()
                )
                return True
            return False

    async def update_status(
        self,
        executor_id: str,
        status_data: Dict[str, Any]
    ) -> None:
        """Update executor status, creating if not exists."""
        async with self._lock:
            if executor_id not in self._executors:
                await self.register(executor_id, status_data)

            info = self._executors[executor_id]
            info.status = status_data.get("status", "unknown")
            info.active_tasks = status_data.get("active_tasks", 0)
            info.queue_size = status_data.get("queue_size", 0)
            info.last_heartbeat = status_data.get("updated_at", info.last_heartbeat)

    async def update_task(self, executor_id: str, task_data: Dict[str, Any]) -> None:
        """Update executor task, maintaining only active tasks."""
        async with self._lock:
            if executor_id not in self._executors:
                self._executors[executor_id] = ExecutorInfo(tasks=[])

            info = self._executors[executor_id]
            task_id = task_data.get("task_id")

            # Update existing task or append new one
            updated = False
            for index, task in enumerate(info.tasks):
                if task.get("task_id") == task_id:
                    info.tasks[index] = task_data
                    updated = True
                    break

            if not updated:
                info.tasks.append(task_data)

            # Keep only active tasks
            info.tasks = [
                t for t in info.tasks
                if t.get("status") in ["running", "pending"]
            ]
            info.active_tasks = len(info.tasks)

    async def get_executor(self, executor_id: str) -> ExecutorInfo | None:
        """Get specific executor info."""
        async with self._lock:
            return self._executors.get(executor_id)

    async def count(self) -> int:
        """Get current executor count."""
        async with self._lock:
            return len(self._executors)


# Global registry instance
_registry = ExecutorRegistry()


# Backward compatibility: expose dict-like access (deprecated)
# These will be removed after migrating all callers
@property
def _active_executors_dict() -> Dict[str, Dict[str, Any]]:
    """Legacy dict access - DEPRECATED: use registry methods instead."""
    import warnings
    warnings.warn(
        "Direct dict access is deprecated. Use registry methods.",
        DeprecationWarning,
        stacklevel=2
    )
    # Return a snapshot (not thread-safe for writes)
    loop = asyncio.get_event_loop()
    if loop.is_running():
        return asyncio.create_task(_registry.get_all()).result()
    return asyncio.run(_registry.get_all())


# For backward compatibility during migration
active_executors: Dict[str, Dict[str, Any]] = {}
# Note: active_executors is deprecated. Use _registry methods instead.


async def get_executor_status() -> Dict[str, Any]:
    """Get executor status - thread-safe."""
    executors_dict = await _registry.get_all()

    if not executors_dict:
        return {"connected": False, "active_executors": 0, "executors": []}

    executors = []
    for executor_id, info in executors_dict.items():
        executors.append(
            {
                "id": executor_id,
                "status": info.get("status", "unknown"),
                "connected_at": info.get("connected_at"),
                "last_heartbeat": info.get("last_heartbeat"),
                "active_tasks": info.get("active_tasks", 0),
                "queue_size": info.get("queue_size", 0),
            }
        )
    return {"connected": True, "active_executors": len(executors_dict), "executors": executors}


async def get_active_tasks() -> Dict[str, Any]:
    """Get active tasks - thread-safe."""
    executors_dict = await _registry.get_all()
    tasks = []
    for executor_id, info in executors_dict.items():
        for task in info.get("tasks", []):
            tasks.append(
                {
                    "task_id": task.get("task_id"),
                    "executor_id": executor_id,
                    "status": task.get("status"),
                    "run_type": task.get("run_type"),
                    "target_id": task.get("target_id"),
                    "device_serial": task.get("device_serial"),
                    "started_at": task.get("started_at"),
                }
            )
    return {"total": len(tasks), "tasks": tasks}


async def get_executor_devices(db: Session) -> Dict[str, Any]:
    """Get executor devices - thread-safe."""
    executors_dict = await _registry.get_all()

    used_devices = {}
    for executor_id, info in executors_dict.items():
        for task in info.get("tasks", []):
            device_serial = task.get("device_serial")
            if device_serial:
                used_devices[device_serial] = {
                    "serial": device_serial,
                    "status": "in_use",
                    "in_use": True,
                    "current_executor": executor_id,
                    "current_task": task.get("task_id"),
                }

    device_repo = DeviceRepository(db)
    all_devices = device_repo.list()
    devices = []
    seen_serials = set()

    for serial, info in used_devices.items():
        seen_serials.add(serial)
        device = next((d for d in all_devices if d.serial == serial), None)
        if device:
            devices.append(
                {
                    "id": device.id,
                    "name": device.name,
                    "serial": device.serial,
                    "model": getattr(device, "model", "Unknown"),
                    "os_version": getattr(device, "os_version", "Unknown"),
                    "connection_type": device.connection_type,
                    "in_use": True,
                    "current_executor": info["current_executor"],
                    "current_task": info["current_task"],
                }
            )
        else:
            devices.append(
                {
                    "id": 0,
                    "name": serial,
                    "serial": serial,
                    "model": "Unknown",
                    "os_version": "Unknown",
                    "connection_type": "unknown",
                    "in_use": True,
                    "current_executor": info["current_executor"],
                    "current_task": info["current_task"],
                }
            )

    for device in all_devices:
        if device.serial not in seen_serials:
            devices.append(
                {
                    "id": device.id,
                    "name": device.name,
                    "serial": device.serial,
                    "model": getattr(device, "model", "Unknown"),
                    "os_version": getattr(device, "os_version", "Unknown"),
                    "connection_type": device.connection_type,
                    "in_use": False,
                    "current_executor": None,
                    "current_task": None,
                }
            )

    return {"total": len(devices), "devices": devices, "in_use_count": len(used_devices)}


async def register_executor(executor_id: str, connection_info: Dict[str, Any]) -> bool:
    """Register an executor - thread-safe.
    Returns True if registered, False if limit reached."""
    return await _registry.register(executor_id, connection_info)


async def unregister_executor(executor_id: str) -> bool:
    """Unregister an executor - thread-safe.
    Returns True if executor existed."""
    return await _registry.unregister(executor_id)


async def update_executor_heartbeat(executor_id: str) -> bool:
    """Update executor heartbeat - thread-safe.
    Returns True if executor exists."""
    return await _registry.update_heartbeat(executor_id)


async def update_executor_status(executor_id: str, status_data: Dict[str, Any]) -> None:
    """Update executor status - thread-safe."""
    await _registry.update_status(executor_id, status_data)


async def update_executor_task(executor_id: str, task_data: Dict[str, Any]) -> None:
    """Update executor task - thread-safe."""
    await _registry.update_task(executor_id, task_data)


def start_cleanup_task() -> None:
    """Start the background cleanup task. Call once at application startup."""
    _registry.start_cleanup_task()


async def cleanup_expired() -> Dict[str, int]:
    """Manually trigger cleanup of expired executors and tasks.
    Returns cleanup statistics."""
    return await _registry.cleanup_expired()
