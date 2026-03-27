"""Task queue websocket endpoint for executors."""
from __future__ import annotations

import asyncio
import json
import logging
from contextlib import contextmanager

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.database import SessionLocal
from app.schemas.ws_events import (
    WsConnectedEvent,
    WsErrorEvent,
    WsNewTaskEvent,
    WsQueueStatusEvent,
)
from app.services.task_queue_ws_service import (
    ConnectionManager,
    HEARTBEAT_TIMEOUT_SECONDS,
    handle_get_task as service_handle_get_task,
    handle_ping as service_handle_ping,
    handle_register as service_handle_register,
    handle_task_complete as service_handle_task_complete,
    handle_task_log as service_handle_task_log,
    handle_task_screenshots as service_handle_task_screenshots,
    handle_task_status as service_handle_task_status,
    save_log as _save_log_impl,
    save_screenshots as _save_screenshots_impl,
    sync_runtime_and_db as _sync_runtime_and_db_impl,
    utc_now_iso as _utc_now_iso,
)
from app.services.scheduler_service import can_dispatch
from app.utils.task_queue import get_task_queue

logger = logging.getLogger(__name__)
router = APIRouter(tags=["task_queue_ws"])


@contextmanager
def _db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


manager = ConnectionManager()


@router.websocket("/ws/task-queue")
async def task_queue_websocket(websocket: WebSocket):
    """Executor websocket endpoint."""
    task_queue = get_task_queue()
    executor_id = f"executor_{id(websocket)}"
    task_pusher: asyncio.Task | None = None
    heartbeat_guard: asyncio.Task | None = None

    try:
        await manager.connect(executor_id, websocket)
        await websocket.send_json(
            WsConnectedEvent(
                message="Connected to TestFlow task queue",
                executor_id=executor_id,
                timestamp=_utc_now_iso(),
            ).model_dump()
        )
        await websocket.send_json(
            WsQueueStatusEvent(queue_size=task_queue.get_queue_size(), status="ready").model_dump()
        )
        task_pusher = asyncio.create_task(push_tasks(websocket, task_queue, executor_id))
        heartbeat_guard = asyncio.create_task(_monitor_executor_heartbeat(websocket, executor_id))

        while True:
            try:
                data = await websocket.receive_text()
                manager.touch(executor_id)
                message = json.loads(data)
                await handle_executor_message(executor_id, message, task_queue, websocket)
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_json(
                    WsErrorEvent(code="invalid_json", message="Invalid JSON payload").model_dump()
                )
            except Exception as exc:
                logger.error("Failed to process websocket message: %s", exc)
                await websocket.send_json(
                    WsErrorEvent(code="message_processing_failed", message=str(exc)).model_dump()
                )
    finally:
        if task_pusher is not None:
            task_pusher.cancel()
        if heartbeat_guard is not None:
            heartbeat_guard.cancel()
        inflight = manager.disconnect(executor_id)
        for task_id in inflight:
            task_queue.requeue(task_id)


async def push_tasks(websocket: WebSocket, task_queue, executor_id: str):
    """Push queued tasks to connected executor."""
    try:
        while executor_id in manager.active_connections:
            if not can_dispatch(manager.total_inflight()):
                await asyncio.sleep(0.2)
                continue
            task_id = await task_queue.get(timeout=5.0)
            if not task_id:
                continue
            task_data = task_queue.get_task_data(task_id)
            if task_data:
                try:
                    await websocket.send_json(
                        WsNewTaskEvent(task_id=task_id, task_data=task_data).model_dump()
                    )
                    manager.mark_task_dispatched(executor_id, task_id)
                    task_queue.update_task_status(task_id, "dispatched", executor_id=executor_id)
                    logger.info("Task dispatched task_id=%s executor_id=%s", task_id, executor_id)
                except Exception:
                    task_queue.requeue(task_id)
                    raise
    except asyncio.CancelledError:
        return
    except Exception as exc:
        logger.error("Task push failed for %s: %s", executor_id, exc)


async def _monitor_executor_heartbeat(websocket: WebSocket, executor_id: str) -> None:
    try:
        while executor_id in manager.active_connections:
            await asyncio.sleep(10)
            if manager.is_stale(executor_id, timeout_seconds=HEARTBEAT_TIMEOUT_SECONDS):
                logger.warning("Executor heartbeat timeout executor_id=%s", executor_id)
                await websocket.close(code=1011)
                return
    except asyncio.CancelledError:
        return
    except Exception as exc:
        logger.error("Heartbeat monitor failed executor_id=%s error=%s", executor_id, exc)


def _save_log(task_id: str, log_data: dict) -> None:
    _save_log_impl(task_id, log_data, _db_session)


def _save_screenshots(task_id: str, screenshots: list[dict]) -> None:
    _save_screenshots_impl(task_id, screenshots, _db_session)


def _sync_runtime_and_db(task_id: str, status: str) -> None:
    _sync_runtime_and_db_impl(task_id, status, _db_session)


async def handle_executor_message(
    executor_id: str,
    message: dict,
    task_queue,
    websocket: WebSocket,
):
    """Dispatch executor messages by message type."""
    message_type = message.get("type")
    logger.info("Message received executor_id=%s message_type=%s", executor_id, message_type)
    handlers = {
        "ping": _handle_ping,
        "get_task": _handle_get_task,
        "task_status": _handle_task_status,
        "task_log": _handle_task_log,
        "task_screenshots": _handle_task_screenshots,
        "task_complete": _handle_task_complete,
        "register": _handle_register,
    }
    handler = handlers.get(message_type)
    if handler is None:
        await websocket.send_json(
            WsErrorEvent(code="unknown_message_type", message=f"Unknown message type: {message_type}").model_dump()
        )
        return
    try:
        await handler(executor_id, message, task_queue, websocket)
    except Exception as exc:
        logger.error("Handler failed for %s: %s", message_type, exc)
        await websocket.send_json(
            WsErrorEvent(code="handler_failed", message=str(exc)).model_dump()
        )


async def _handle_ping(executor_id: str, message: dict, task_queue, websocket: WebSocket):
    del task_queue
    await service_handle_ping(manager, executor_id, message, websocket)


async def _handle_get_task(executor_id: str, message: dict, task_queue, websocket: WebSocket):
    del executor_id
    await service_handle_get_task(message, task_queue, websocket)


async def _handle_task_status(executor_id: str, message: dict, task_queue, websocket: WebSocket):
    await service_handle_task_status(
        manager,
        executor_id,
        message,
        task_queue,
        websocket,
        _sync_runtime_and_db,
    )


async def _handle_task_log(executor_id: str, message: dict, task_queue, websocket: WebSocket):
    del task_queue
    try:
        await service_handle_task_log(manager, executor_id, message, websocket, _save_log)
    except Exception as exc:
        logger.error("Failed to persist run log: %s", exc)


async def _handle_task_screenshots(executor_id: str, message: dict, task_queue, websocket: WebSocket):
    del executor_id, task_queue
    try:
        await service_handle_task_screenshots(manager, message, websocket, _save_screenshots)
    except Exception as exc:
        logger.error("Failed to persist screenshots: %s", exc)


async def _handle_task_complete(executor_id: str, message: dict, task_queue, websocket: WebSocket):
    await service_handle_task_complete(
        manager,
        executor_id,
        message,
        task_queue,
        websocket,
        _sync_runtime_and_db,
    )


async def _handle_register(executor_id: str, message: dict, task_queue, websocket: WebSocket):
    del task_queue
    await service_handle_register(executor_id, message, websocket)
