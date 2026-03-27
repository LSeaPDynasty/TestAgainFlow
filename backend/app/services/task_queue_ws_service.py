"""Service helpers for task queue websocket endpoint."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable

from app.schemas.ws_events import (
    WsErrorEvent,
    WsPongEvent,
    WsRegisteredEvent,
    WsTaskCompleteEvent,
    WsTaskDataEvent,
    WsTaskLogEvent,
    WsTaskScreenshotsEvent,
    WsTaskStatusUpdateEvent,
)

from app.models.run_log import RunLog
from app.models.screenshot import RunScreenshot
from app.repositories.run_history_repo import RunHistoryRepository
from app.services.run_orchestrator import (
    RUN_STATUS_CANCELLED,
    RUN_STATUS_FAILED,
    RUN_STATUS_PAUSED,
    RUN_STATUS_QUEUED,
    RUN_STATUS_RUNNING,
    RUN_STATUS_STOPPED,
    RUN_STATUS_SUCCESS,
    get_run_orchestrator,
)

HEARTBEAT_TIMEOUT_SECONDS = 180

FINAL_EXECUTOR_TASK_STATUSES = {
    "completed",
    "success",
    "failed",
    "fail",
    "cancelled",
    "stopped",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ConnectionManager:
    """Tracks executor websocket connections."""

    def __init__(self):
        self.active_connections: Dict[str, Any] = {}
        self._inflight_tasks: Dict[str, set[str]] = {}
        self._last_seen: Dict[str, float] = {}

    async def connect(self, executor_id: str, websocket) -> None:
        await websocket.accept()
        self.active_connections[executor_id] = websocket
        self._inflight_tasks[executor_id] = set()
        self._last_seen[executor_id] = datetime.now(timezone.utc).timestamp()

    def disconnect(self, executor_id: str) -> set[str]:
        self.active_connections.pop(executor_id, None)
        self._last_seen.pop(executor_id, None)
        return self._inflight_tasks.pop(executor_id, set())

    def touch(self, executor_id: str) -> None:
        self._last_seen[executor_id] = datetime.now(timezone.utc).timestamp()

    def is_stale(self, executor_id: str, timeout_seconds: int = HEARTBEAT_TIMEOUT_SECONDS) -> bool:
        last_seen = self._last_seen.get(executor_id)
        if last_seen is None:
            return True
        return (datetime.now(timezone.utc).timestamp() - last_seen) > timeout_seconds

    def mark_task_dispatched(self, executor_id: str, task_id: str) -> None:
        if executor_id in self._inflight_tasks:
            self._inflight_tasks[executor_id].add(task_id)

    def mark_task_finished(self, executor_id: str, task_id: str) -> None:
        if executor_id in self._inflight_tasks:
            self._inflight_tasks[executor_id].discard(task_id)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        disconnected = []
        for executor_id, connection in self.active_connections.items():
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(executor_id)
        for executor_id in disconnected:
            self.disconnect(executor_id)

    def total_inflight(self) -> int:
        return sum(len(tasks) for tasks in self._inflight_tasks.values())


def save_log(task_id: str, log_data: Dict[str, Any], db_session_factory) -> None:
    with db_session_factory() as db:
        run_log = RunLog(
            task_id=task_id,
            level=log_data.get("level", "INFO"),
            message=log_data.get("message", ""),
            timestamp=log_data.get("timestamp", 0),
            testcase_id=log_data.get("testcase_id"),
            testcase_name=log_data.get("testcase_name"),
            testcase_result=log_data.get("testcase_result"),
        )
        db.add(run_log)
        db.commit()


def save_screenshots(task_id: str, screenshots: list[Dict[str, Any]], db_session_factory) -> None:
    with db_session_factory() as db:
        for screenshot in screenshots:
            db.add(
                RunScreenshot(
                    task_id=task_id,
                    filename=screenshot.get("filename", ""),
                    filepath=screenshot.get("filepath", ""),
                    step_name=screenshot.get("step_name", ""),
                    timestamp=screenshot.get("timestamp", ""),
                    created_at=datetime.now(timezone.utc),
                )
            )
        db.commit()


def normalize_runtime_status(status: str) -> str:
    value = (status or "").lower()
    mapping = {
        "pending": RUN_STATUS_QUEUED,
        "queued": RUN_STATUS_QUEUED,
        "running": RUN_STATUS_RUNNING,
        "paused": RUN_STATUS_PAUSED,
        "stopped": RUN_STATUS_STOPPED,
        "cancelled": RUN_STATUS_CANCELLED,
        "pass": RUN_STATUS_SUCCESS,
        "success": RUN_STATUS_SUCCESS,
        "fail": RUN_STATUS_FAILED,
        "failed": RUN_STATUS_FAILED,
        "error": RUN_STATUS_FAILED,
        "timeout": RUN_STATUS_FAILED,
        "completed": RUN_STATUS_SUCCESS,
    }
    return mapping.get(value, RUN_STATUS_RUNNING)


def runtime_to_db_result(runtime_status: str) -> str:
    mapping = {
        RUN_STATUS_QUEUED: "pending",
        RUN_STATUS_RUNNING: "running",
        RUN_STATUS_PAUSED: "running",
        RUN_STATUS_STOPPED: "cancelled",
        RUN_STATUS_CANCELLED: "cancelled",
        RUN_STATUS_SUCCESS: "pass",
        RUN_STATUS_FAILED: "fail",
    }
    return mapping.get(runtime_status, "running")


def sync_runtime_and_db(task_id: str, status: str, db_session_factory) -> None:
    runtime_status = normalize_runtime_status(status)

    orchestrator = get_run_orchestrator()
    current = orchestrator.get_status(task_id)
    if current is None:
        orchestrator.ensure_task(task_id, status=runtime_status)
    else:
        orchestrator.transition(task_id, runtime_status)

    with db_session_factory() as db:
        repo = RunHistoryRepository(db)
        run = repo.get_by_task_id(task_id)
        if not run:
            return
        run.result = runtime_to_db_result(runtime_status)
        if runtime_status in {
            RUN_STATUS_STOPPED,
            RUN_STATUS_CANCELLED,
            RUN_STATUS_SUCCESS,
            RUN_STATUS_FAILED,
        }:
            run.finished_at = datetime.now(timezone.utc)
        db.commit()


def require_fields(message: dict, required: Iterable[str]) -> str | None:
    for field in required:
        value = message.get(field)
        if value is None or value == "":
            return field
    return None


async def handle_ping(manager: ConnectionManager, executor_id: str, message: dict, websocket) -> None:
    manager.touch(executor_id)
    await websocket.send_json(WsPongEvent(timestamp=message.get("timestamp")).model_dump())


async def handle_get_task(message: dict, task_queue, websocket) -> None:
    task_id = message.get("task_id")
    if task_id:
        await websocket.send_json(
            WsTaskDataEvent(task_id=task_id, task_data=task_queue.get_task_data(task_id)).model_dump()
        )


async def handle_task_status(
    manager: ConnectionManager,
    executor_id: str,
    message: dict,
    task_queue,
    websocket,
    sync_runtime_and_db_cb,
) -> None:
    missing = require_fields(message, ["task_id", "status"])
    if missing:
        await websocket.send_json(
            WsErrorEvent(code="missing_field", message=f"Missing required field: {missing}").model_dump()
        )
        return

    task_id = message["task_id"]
    status = message["status"]
    task_queue.update_task_status(task_id, status, **message.get("data", {}))
    if status.lower() in FINAL_EXECUTOR_TASK_STATUSES:
        manager.mark_task_finished(executor_id, task_id)
    sync_runtime_and_db_cb(task_id, status)
    await manager.broadcast(
        WsTaskStatusUpdateEvent(task_id=task_id, status=status, executor_id=executor_id).model_dump()
    )


async def handle_task_log(
    manager: ConnectionManager,
    executor_id: str,
    message: dict,
    websocket,
    save_log_cb,
) -> None:
    task_id = message.get("task_id")
    if not task_id:
        await websocket.send_json(
            WsErrorEvent(code="missing_field", message="Missing required field: task_id").model_dump()
        )
        return
    log_data = message.get("log") or {}
    save_log_cb(task_id, log_data)
    await manager.broadcast(
        WsTaskLogEvent(task_id=task_id, log=log_data, executor_id=executor_id).model_dump()
    )


async def handle_task_screenshots(
    manager: ConnectionManager,
    message: dict,
    websocket,
    save_screenshots_cb,
) -> None:
    task_id = message.get("task_id")
    if not task_id:
        await websocket.send_json(
            WsErrorEvent(code="missing_field", message="Missing required field: task_id").model_dump()
        )
        return
    screenshots = message.get("screenshots") or []
    save_screenshots_cb(task_id, screenshots)
    await manager.broadcast(
        WsTaskScreenshotsEvent(task_id=task_id, screenshots=screenshots).model_dump()
    )


async def handle_task_complete(
    manager: ConnectionManager,
    executor_id: str,
    message: dict,
    task_queue,
    websocket,
    sync_runtime_and_db_cb,
) -> None:
    task_id = message.get("task_id")
    if not task_id:
        await websocket.send_json(
            WsErrorEvent(code="missing_field", message="Missing required field: task_id").model_dump()
        )
        return
    result = message.get("result")
    task_queue.update_task_status(task_id, "completed", result=result)
    manager.mark_task_finished(executor_id, task_id)
    sync_runtime_and_db_cb(task_id, result or "completed")
    await manager.broadcast(
        WsTaskCompleteEvent(task_id=task_id, result=result, executor_id=executor_id).model_dump()
    )


async def handle_register(executor_id: str, message: dict, websocket) -> None:
    capabilities = message.get("capabilities", {})
    await websocket.send_json(
        WsRegisteredEvent(executor_id=executor_id, capabilities=capabilities).model_dump()
    )
