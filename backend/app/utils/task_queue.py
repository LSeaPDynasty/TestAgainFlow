"""In-memory task queue used by backend/executor integration."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from itertools import count

logger = logging.getLogger(__name__)

FINAL_TASK_STATUSES = {
    "completed",
    "success",
    "failed",
    "fail",
    "cancelled",
    "stopped",
}


class TaskQueue:
    """A lightweight in-memory queue with task metadata."""

    def __init__(self):
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._status: Dict[str, str] = {}
        self._listeners: List[asyncio.Queue] = []
        self._sequence = count()

    def _store_task(self, task_id: str, task_data: Dict[str, Any], priority: int) -> None:
        self._tasks[task_id] = {
            **task_data,
            "task_id": task_id,
            "queued_at": datetime.utcnow().isoformat(),
            "priority": priority,
        }
        self._status[task_id] = "queued"

    def _notify_listeners(self, message: Dict[str, Any]) -> None:
        for listener in self._listeners:
            try:
                listener.put_nowait(message)
            except Exception as exc:
                logger.error("Failed to notify listener: %s", exc)

    async def put(self, task_id: str, task_data: Dict[str, Any], priority: int = 5) -> bool:
        """Put task asynchronously."""
        try:
            normalized_priority = max(1, min(10, int(priority)))
            self._store_task(task_id, task_data, normalized_priority)
            await self._queue.put((normalized_priority, next(self._sequence), task_id))
            self._notify_listeners(
                {"type": "task_queued", "task_id": task_id, "task_data": task_data}
            )
            logger.info("Task queued: %s", task_id)
            return True
        except Exception as exc:
            logger.error("Failed to queue task %s: %s", task_id, exc)
            return False

    def put_nowait(self, task_id: str, task_data: Dict[str, Any], priority: int = 5) -> bool:
        """Put task synchronously without event-loop management."""
        try:
            normalized_priority = max(1, min(10, int(priority)))
            self._store_task(task_id, task_data, normalized_priority)
            self._queue.put_nowait((normalized_priority, next(self._sequence), task_id))
            self._notify_listeners(
                {"type": "task_queued", "task_id": task_id, "task_data": task_data}
            )
            logger.info("Task queued: %s", task_id)
            return True
        except Exception as exc:
            logger.error("Failed to queue task %s: %s", task_id, exc)
            return False

    async def get(self, timeout: float = 1.0) -> Optional[str]:
        """Get task id from queue with timeout."""
        try:
            _, _, task_id = await asyncio.wait_for(self._queue.get(), timeout=timeout)
            if task_id in self._status:
                self._status[task_id] = "picked_up"
            logger.info("Task picked up: %s", task_id)
            return task_id
        except asyncio.TimeoutError:
            return None

    def get_task_data(self, task_id: str) -> Optional[Dict[str, Any]]:
        return self._tasks.get(task_id)

    def update_task_status(self, task_id: str, status: str, **kwargs) -> None:
        if task_id in self._status:
            self._status[task_id] = status
            self._notify_listeners(
                {
                    "type": "task_status_update",
                    "task_id": task_id,
                    "status": status,
                    **kwargs,
                }
            )
            logger.info("Task status update: %s -> %s", task_id, status)

    def get_status(self, task_id: str) -> Optional[str]:
        return self._status.get(task_id)

    def get_all_statuses(self) -> Dict[str, str]:
        return self._status.copy()

    def get_queue_size(self) -> int:
        return self._queue.qsize()

    def add_listener(self, listener: asyncio.Queue) -> None:
        self._listeners.append(listener)

    def remove_listener(self, listener: asyncio.Queue) -> None:
        if listener in self._listeners:
            self._listeners.remove(listener)

    def requeue(self, task_id: str) -> bool:
        """Put an existing task back to queue when delivery fails."""
        task_data = self._tasks.get(task_id)
        if not task_data:
            return False
        current_status = (self._status.get(task_id) or "").lower()
        if current_status in FINAL_TASK_STATUSES:
            return False
        try:
            self._status[task_id] = "queued"
            priority = int(task_data.get("priority", 5))
            self._queue.put_nowait((priority, next(self._sequence), task_id))
            self._notify_listeners(
                {
                    "type": "task_requeued",
                    "task_id": task_id,
                    "task_data": task_data,
                }
            )
            logger.warning("Task requeued: %s", task_id)
            return True
        except Exception as exc:
            logger.error("Failed to requeue task %s: %s", task_id, exc)
            return False

    def clear(self) -> None:
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        self._tasks.clear()
        self._status.clear()


_task_queue: Optional[TaskQueue] = None


def get_task_queue() -> TaskQueue:
    global _task_queue
    if _task_queue is None:
        _task_queue = TaskQueue()
    return _task_queue
