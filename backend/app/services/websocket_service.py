"""WebSocket service for real-time executor updates."""
from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Awaitable, Callable, Dict, List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

import app.routers.executor_status as executor_status
from app.schemas.ws_events import (
    WsConnectedEvent,
    WsCurrentStatusEvent,
    WsErrorEvent,
    WsPongEvent,
    WsSubscribedEvent,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ws", tags=["websocket"])

PENDING_REQUEST_TTL_SECONDS = 60.0


@dataclass
class PendingRequestEntry:
    future: asyncio.Future
    expires_at: float


pending_test_requests: Dict[str, PendingRequestEntry] = {}
_pending_requests_lock = asyncio.Lock()  # 添加锁保护


async def register_pending_request(
    request_id: str, future: asyncio.Future, timeout_seconds: float = 30.0
) -> None:
    async with _pending_requests_lock:
        pending_test_requests[request_id] = PendingRequestEntry(
            future=future,
            expires_at=time.time() + max(timeout_seconds, 1.0),
        )


async def pop_pending_request(request_id: str) -> asyncio.Future | None:
    async with _pending_requests_lock:
        entry = pending_test_requests.pop(request_id, None)
        return entry.future if entry else None


async def resolve_pending_request(request_id: str, payload: dict) -> bool:
    future = await pop_pending_request(request_id)
    if future is None:
        return False
    if not future.done():
        future.set_result(payload)
    return True


async def cleanup_expired_pending_requests(now: float | None = None) -> int:
    async with _pending_requests_lock:
        ts = now or time.time()
        expired_ids = [
            request_id
            for request_id, entry in pending_test_requests.items()
            if entry.expires_at < ts
        ]
        for request_id in expired_ids:
            entry = pending_test_requests.pop(request_id, None)
            if entry and not entry.future.done():
                entry.future.cancel()
        return len(expired_ids)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ConnectionManager:
    """Tracks websocket connections grouped by client type."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_types: Dict[WebSocket, str] = {}
        self._lock = asyncio.Lock()  # 添加线程安全锁

    async def connect(self, websocket: WebSocket, client_type: str = "general") -> None:
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
            self.connection_types[websocket] = client_type

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
            self.connection_types.pop(websocket, None)

    async def send_personal_message(self, message: dict, websocket: WebSocket) -> None:
        try:
            if websocket.client_state != WebSocketState.DISCONNECTED:  # 使用枚举值检查
                await websocket.send_json(message)
        except Exception:
            await self.disconnect(websocket)

    async def broadcast(self, message: dict, client_type: str | None = None) -> None:
        disconnected: List[WebSocket] = []
        async with self._lock:  # 使用锁保护连接列表
            connections_to_process = list(self.active_connections)

        for conn in connections_to_process:
            if client_type is not None and self.connection_types.get(conn) != client_type:
                continue
            try:
                if conn.client_state != WebSocketState.DISCONNECTED:  # 使用枚举值检查
                    await conn.send_json(message)
            except Exception:
                disconnected.append(conn)

        # 清理断开的连接
        for conn in disconnected:
            await self.disconnect(conn)

    async def send_status_update(self, status: str, data: dict | None = None) -> None:
        await self.broadcast(
            {
                "type": "status_update",
                "timestamp": datetime.now().isoformat(),
                "status": status,
                "data": data or {},
            },
            "executor",
        )

    async def send_task_update(self, task_id: str, task_data: dict) -> None:
        await self.broadcast(
            {
                "type": "task_update",
                "timestamp": datetime.now().isoformat(),
                "task_id": task_id,
                "data": task_data,
            },
            "executor",
        )

    async def send_log(self, level: str, message: str, module: str = "system") -> None:
        await self.broadcast(
            {
                "type": "log",
                "timestamp": datetime.now().isoformat(),
                "level": level,
                "module": module,
                "message": message,
            },
            "executor",
        )

    async def send_device_update(self, devices: list) -> None:
        await self.broadcast(
            {
                "type": "device_update",
                "timestamp": datetime.now().isoformat(),
                "devices": devices,
            },
            "executor",
        )

    def get_connection_count(self) -> int:
        return len(self.active_connections)


manager = ConnectionManager()


# 添加定期清理任务
async def start_cleanup_task():
    """启动定期清理过期请求的后台任务"""
    while True:
        try:
            await asyncio.sleep(60)  # 每分钟清理一次
            count = await cleanup_expired_pending_requests()
            if count > 0:
                logger.info(f"Cleaned up {count} expired pending requests")
        except Exception as e:
            logger.error(f"Cleanup task error: {e}")


# 启动清理任务
_cleanup_task = None


def get_cleanup_task():
    """获取清理任务实例"""
    global _cleanup_task
    if _cleanup_task is None:
        _cleanup_task = asyncio.create_task(start_cleanup_task())
    return _cleanup_task


async def _send_ws_error(websocket: WebSocket, code: str, message: str) -> None:
    await websocket.send_json(WsErrorEvent(code=code, message=message).model_dump())


async def _handle_ping(
    executor_id: str, client_type: str, websocket: WebSocket, message: dict
) -> None:
    executor_status.update_executor_heartbeat(executor_id)
    await websocket.send_json(WsPongEvent(timestamp=_utc_now_iso()).model_dump())


async def _handle_status_update(
    executor_id: str, client_type: str, websocket: WebSocket, message: dict
) -> None:
    executor_status.update_executor_status(executor_id, message)
    await manager.broadcast(message, "gui")


async def _handle_task_update(
    executor_id: str, client_type: str, websocket: WebSocket, message: dict
) -> None:
    if not message.get("task_id"):
        await _send_ws_error(websocket, "missing_field", "Missing required field: task_id")
        return
    task_data = message.get("data", {})
    task_data["task_id"] = message.get("task_id")
    executor_status.update_executor_task(executor_id, task_data)
    await manager.broadcast(message, "gui")


async def _handle_log(
    executor_id: str, client_type: str, websocket: WebSocket, message: dict
) -> None:
    log_message = dict(message)
    log_message.setdefault("timestamp", _utc_now_iso())
    log_message.setdefault("module", "executor")
    log_message.setdefault("level", "INFO")
    await manager.broadcast(log_message, "gui")


async def _handle_device_update(
    executor_id: str, client_type: str, websocket: WebSocket, message: dict
) -> None:
    devices = message.get("devices", [])
    db = None
    try:
        from app.database import SessionLocal
        from app.routers.devices import register_engine_devices

        db = SessionLocal()
        result = await register_engine_devices(devices, db)
        if hasattr(result, "data") and result.data:
            await manager.broadcast(result.data, "gui")
    except Exception as exc:
        logger.error("Device registration failed: %s", exc)
        await _send_ws_error(websocket, "device_update_failed", str(exc))
    finally:
        if db is not None:
            try:
                db.close()
            except Exception as e:
                logger.error("Error closing database session: %s", e)


async def _handle_subscribe(
    executor_id: str, client_type: str, websocket: WebSocket, message: dict
) -> None:
    new_type = message.get("client_type", client_type)
    async with manager._lock:  # 使用锁保护
        manager.connection_types[websocket] = new_type
    await websocket.send_json(
        WsSubscribedEvent(timestamp=_utc_now_iso(), client_type=new_type).model_dump()
    )


async def _handle_get_status(
    executor_id: str, client_type: str, websocket: WebSocket, message: dict
) -> None:
    await websocket.send_json(
        WsCurrentStatusEvent(
            timestamp=_utc_now_iso(),
            connection_count=manager.get_connection_count(),
        ).model_dump()
    )


async def _handle_test_result(
    executor_id: str, client_type: str, websocket: WebSocket, message: dict
) -> None:
    request_id = message.get("request_id")
    if request_id:
        await resolve_pending_request(request_id, message)


Handler = Callable[[str, str, WebSocket, dict], Awaitable[None]]


MESSAGE_HANDLERS: Dict[str, Handler] = {
    "ping": _handle_ping,
    "status_update": _handle_status_update,
    "task_update": _handle_task_update,
    "log": _handle_log,
    "device_update": _handle_device_update,
    "subscribe": _handle_subscribe,
    "get_status": _handle_get_status,
    "test_device_result": _handle_test_result,
    "test_element_result": _handle_test_result,
    "dom_result": _handle_test_result,
}


@router.websocket("/executor")
async def websocket_executor_endpoint(websocket: WebSocket, client_type: str = "executor"):
    """Main websocket endpoint used by executor and GUI clients."""
    executor_id = f"executor_{id(websocket)}"
    await manager.connect(websocket, client_type)
    executor_status.register_executor(executor_id, {"connected_at": _utc_now_iso()})

    try:
        logger.info("WebSocket connected executor_id=%s client_type=%s", executor_id, client_type)
        await websocket.send_json(
            WsConnectedEvent(
                message=f"Connected to TestFlow WebSocket ({client_type})",
                timestamp=_utc_now_iso(),
                executor_id=executor_id,
                server_info={
                    "connection_count": manager.get_connection_count(),
                    "client_type": client_type,
                    "executor_id": executor_id,
                },
            ).model_dump()
        )

        while True:
            try:
                await cleanup_expired_pending_requests()
                raw = await websocket.receive_text()
                message = json.loads(raw)
                message_type = message.get("type")
                logger.info(
                    "WebSocket message executor_id=%s client_type=%s message_type=%s",
                    executor_id,
                    client_type,
                    message_type,
                )
                handler = MESSAGE_HANDLERS.get(message_type)
                if handler is None:
                    await _send_ws_error(
                        websocket, "unknown_message_type", f"Unknown message type: {message_type}"
                    )
                    continue
                try:
                    await handler(executor_id, client_type, websocket, message)
                except Exception as exc:
                    logger.error("WebSocket handler %s failed: %s", message_type, exc)
                    await _send_ws_error(websocket, "handler_failed", str(exc))
            except json.JSONDecodeError:
                await _send_ws_error(websocket, "invalid_json", "Invalid JSON format")
            except Exception as exc:
                logger.error("WebSocket message loop error: %s", exc)
                break  # 退出循环，触发finally清理
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected executor_id=%s", executor_id)
    except Exception as exc:
        logger.error("WebSocket endpoint error: %s", exc)
    finally:
        # 确保资源被正确清理
        try:
            await manager.disconnect(websocket)
        except Exception as e:
            logger.error("Error disconnecting websocket: %s", e)

        try:
            executor_status.unregister_executor(executor_id)
        except Exception as e:
            logger.error("Error unregistering executor: %s", e)

        try:
            await cleanup_expired_pending_requests()
        except Exception as e:
            logger.error("Error cleaning up pending requests: %s", e)
