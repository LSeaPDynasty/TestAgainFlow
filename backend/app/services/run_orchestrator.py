"""In-memory run orchestration and state machine."""
from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Dict, List, Optional
import time


RUN_STATUS_QUEUED = "queued"
RUN_STATUS_RUNNING = "running"
RUN_STATUS_PAUSED = "paused"
RUN_STATUS_STOPPED = "stopped"
RUN_STATUS_CANCELLED = "cancelled"
RUN_STATUS_SUCCESS = "success"
RUN_STATUS_FAILED = "failed"


FINAL_STATUSES = {
    RUN_STATUS_STOPPED,
    RUN_STATUS_CANCELLED,
    RUN_STATUS_SUCCESS,
    RUN_STATUS_FAILED,
}


ALLOWED_TRANSITIONS = {
    RUN_STATUS_QUEUED: {
        RUN_STATUS_RUNNING,
        RUN_STATUS_PAUSED,
        RUN_STATUS_STOPPED,
        RUN_STATUS_CANCELLED,
        RUN_STATUS_FAILED,
    },
    RUN_STATUS_RUNNING: {
        RUN_STATUS_PAUSED,
        RUN_STATUS_STOPPED,
        RUN_STATUS_CANCELLED,
        RUN_STATUS_SUCCESS,
        RUN_STATUS_FAILED,
    },
    RUN_STATUS_PAUSED: {
        RUN_STATUS_RUNNING,
        RUN_STATUS_STOPPED,
        RUN_STATUS_CANCELLED,
        RUN_STATUS_FAILED,
    },
    RUN_STATUS_STOPPED: set(),
    RUN_STATUS_CANCELLED: set(),
    RUN_STATUS_SUCCESS: set(),
    RUN_STATUS_FAILED: set(),
}


@dataclass
class TaskRuntime:
    status: str = RUN_STATUS_QUEUED
    targets: List[Dict[str, Any]] = field(default_factory=list)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    result: Dict[str, Any] = field(default_factory=dict)
    updated_at: float = field(default_factory=time.time)


class RunOrchestrator:
    """Tracks runtime task state and enforces status transitions."""

    def __init__(self) -> None:
        self._tasks: Dict[str, TaskRuntime] = {}
        self._lock = Lock()

    def create_task(self, task_id: str, targets: List[Dict[str, Any]]) -> None:
        with self._lock:
            self._tasks[task_id] = TaskRuntime(
                status=RUN_STATUS_QUEUED,
                targets=targets,
                logs=[],
                result={},
                updated_at=time.time(),
            )

    def ensure_task(
        self, task_id: str, *, status: str, targets: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """Create task snapshot when only persisted status is available."""
        with self._lock:
            if task_id in self._tasks:
                return
            self._tasks[task_id] = TaskRuntime(
                status=status,
                targets=targets or [],
                logs=[],
                result={},
                updated_at=time.time(),
            )

    def get_status(self, task_id: str) -> Optional[str]:
        with self._lock:
            task = self._tasks.get(task_id)
            return task.status if task else None

    def get_task(self, task_id: str) -> Optional[TaskRuntime]:
        with self._lock:
            return self._tasks.get(task_id)

    def append_log(self, task_id: str, event: Dict[str, Any]) -> None:
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task.logs.append(event)
                task.updated_at = time.time()

    def transition(
        self,
        task_id: str,
        new_status: str,
        *,
        result: Optional[Dict[str, Any]] = None,
    ) -> bool:
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False

            if new_status == task.status:
                return True

            allowed = ALLOWED_TRANSITIONS.get(task.status, set())
            if new_status not in allowed:
                return False

            task.status = new_status
            if result is not None:
                task.result = result
            task.updated_at = time.time()
            return True

    def is_final(self, task_id: str) -> bool:
        status = self.get_status(task_id)
        return status in FINAL_STATUSES

    def list_statuses(self) -> Dict[str, str]:
        with self._lock:
            return {task_id: task.status for task_id, task in self._tasks.items()}

    def cleanup_expired(self, ttl_seconds: int = 21600) -> int:
        """Remove finished tasks whose snapshots are older than ttl_seconds."""
        now = time.time()
        removed = 0
        with self._lock:
            to_remove = [
                task_id
                for task_id, task in self._tasks.items()
                if task.status in FINAL_STATUSES and (now - task.updated_at) > ttl_seconds
            ]
            for task_id in to_remove:
                del self._tasks[task_id]
                removed += 1
        return removed


_run_orchestrator: Optional[RunOrchestrator] = None


def get_run_orchestrator() -> RunOrchestrator:
    global _run_orchestrator
    if _run_orchestrator is None:
        _run_orchestrator = RunOrchestrator()
    return _run_orchestrator
