"""Service layer for backend <-> executor request/response interactions."""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional


class ExecutorBridgeError(Exception):
    """Structured bridge error with API-compatible status code."""

    def __init__(self, message: str, http_code: int = 500) -> None:
        super().__init__(message)
        self.message = message
        self.http_code = http_code


@dataclass
class ExecutorRequestResult:
    request_id: str
    executor_id: str
    payload: Dict[str, Any]


def _pick_executor_id(device_serial: Optional[str] = None) -> str:
    from app.routers import executor_status

    if not executor_status.active_executors:
        raise ExecutorBridgeError("No online executor available", http_code=503)

    if device_serial:
        for executor_id, info in executor_status.active_executors.items():
            for task in info.get("tasks", []):
                if task.get("device_serial") == device_serial:
                    return executor_id

    return next(iter(executor_status.active_executors.keys()))


async def request_executor(
    request_type: str,
    payload: Dict[str, Any],
    *,
    request_prefix: str,
    timeout_seconds: float = 30.0,
    device_serial: Optional[str] = None,
) -> ExecutorRequestResult:
    """Send request to executor and wait for a correlated response."""
    from app.routers.websocket import (
        manager,
        pop_pending_request,
        register_pending_request,
    )

    executor_id = _pick_executor_id(device_serial=device_serial)
    request_id = f"{request_prefix}_{int(time.time() * 1000)}"
    future = asyncio.get_running_loop().create_future()
    register_pending_request(request_id, future, timeout_seconds=timeout_seconds)

    request_message = {
        "type": request_type,
        "request_id": request_id,
        **payload,
    }
    await manager.broadcast(request_message, "executor")

    try:
        response_payload = await asyncio.wait_for(future, timeout=timeout_seconds)
        return ExecutorRequestResult(
            request_id=request_id,
            executor_id=executor_id,
            payload=response_payload,
        )
    except asyncio.TimeoutError as exc:
        pop_pending_request(request_id)
        raise ExecutorBridgeError(
            f"Executor request timeout: {request_type}", http_code=408
        ) from exc
