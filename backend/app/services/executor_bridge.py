"""Service layer for backend <-> executor request/response interactions."""
from __future__ import annotations

import asyncio
import logging
import re
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional

# Configure timeouts for different operation types
TIMEOUT_CONFIG = {
    "default": 30.0,
    "click": 10.0,
    "swipe": 10.0,
    "input": 15.0,
    "wait": 60.0,
    "screenshot": 15.0,
    "find_element": 15.0,
    "run_test": 300.0,  # 5 minutes for test execution
}

logger = logging.getLogger(__name__)


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


def _validate_request_prefix(prefix: str) -> str:
    """Validate and sanitize request prefix to prevent injection.
    Only allows alphanumeric, underscore, and hyphen.
    """
    if not prefix:
        raise ValueError("Request prefix cannot be empty")

    # Remove any characters that aren't alphanumeric, underscore, or hyphen
    sanitized = re.sub(r"[^a-zA-Z0-9_-]", "", prefix)

    if not sanitized:
        raise ValueError("Request prefix must contain valid characters")

    if len(sanitized) > 50:
        raise ValueError("Request prefix too long (max 50 characters)")

    return sanitized


def _get_timeout_for_operation(request_type: str) -> float:
    """Get timeout for specific operation type."""
    return TIMEOUT_CONFIG.get(request_type, TIMEOUT_CONFIG["default"])


def _pick_executor_id(device_serial: Optional[str] = None) -> str:
    from app.routers import executor_status

    # Use async-safe access - this needs to be called from async context
    # For now, we'll need to refactor this, but keeping compatibility
    import asyncio

    async def _get_executor() -> str:
        executors = await executor_status_service.get_all_executors()
        if not executors:
            raise ExecutorBridgeError("No online executor available", http_code=503)

        if device_serial:
            for executor_id, info in executors.items():
                for task in info.get("tasks", []):
                    if task.get("device_serial") == device_serial:
                        return executor_id

        return next(iter(executors.keys()))

    # This is a synchronous wrapper - the caller should be refactored to async
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # We're in async context, but this function is sync
            # This is a known issue that requires refactoring the call site
            # For now, fall back to the old behavior with a warning
            logger.warning("Synchronous _pick_executor_id called from async context")
            # Fallback to old behavior temporarily
            from app.services import executor_status_service
            executors = asyncio.run(executor_status_service._registry.get_all())
        else:
            executors = asyncio.run(executor_status_service._registry.get_all())

        if not executors:
            raise ExecutorBridgeError("No online executor available", http_code=503)

        if device_serial:
            for executor_id, info in executors.items():
                for task in info.get("tasks", []):
                    if task.get("device_serial") == device_serial:
                        return executor_id

        return next(iter(executors.keys()))
    except Exception as e:
        logger.error(f"Failed to pick executor: {e}")
        raise ExecutorBridgeError("No online executor available", http_code=503) from e


async def request_executor(
    request_type: str,
    payload: Dict[str, Any],
    *,
    request_prefix: str,
    timeout_seconds: Optional[float] = None,
    device_serial: Optional[str] = None,
) -> ExecutorRequestResult:
    """Send request to executor and wait for a correlated response.

    Args:
        request_type: Type of request (e.g., "click", "swipe", "run_test")
        payload: Request payload data
        request_prefix: Prefix for request ID (will be validated)
        timeout_seconds: Custom timeout (overrides default for operation type)
        device_serial: Optional device serial for executor selection

    Returns:
        ExecutorRequestResult with request_id, executor_id, and response payload

    Raises:
        ExecutorBridgeError: If request fails or times out
    """
    from app.routers.websocket import (
        manager,
        pop_pending_request,
        register_pending_request,
    )
    from app.services import executor_status_service

    # Validate and sanitize request prefix
    try:
        safe_prefix = _validate_request_prefix(request_prefix)
    except ValueError as e:
        raise ExecutorBridgeError(f"Invalid request prefix: {e}", http_code=400) from e

    # Determine timeout
    if timeout_seconds is None:
        timeout_seconds = _get_timeout_for_operation(request_type)

    # Pick executor (async-safe)
    executors = await executor_status_service._registry.get_all()
    if not executors:
        raise ExecutorBridgeError("No online executor available", http_code=503)

    executor_id = None
    if device_serial:
        for eid, info in executors.items():
            for task in info.get("tasks", []):
                if task.get("device_serial") == device_serial:
                    executor_id = eid
                    break
            if executor_id:
                break

    if executor_id is None:
        executor_id = next(iter(executors.keys()))

    # Generate unique request ID using UUID (guaranteed uniqueness)
    request_id = f"{safe_prefix}_{uuid.uuid4().hex}"

    future = asyncio.get_running_loop().create_future()
    register_pending_request(request_id, future, timeout_seconds=timeout_seconds)

    request_message = {
        "type": request_type,
        "request_id": request_id,
        **payload,
    }

    try:
        await manager.broadcast(request_message, "executor")
    except Exception as e:
        pop_pending_request(request_id)
        logger.error(f"Failed to broadcast request {request_id}: {e}")
        raise ExecutorBridgeError(
            f"Failed to send request to executor: {e}",
            http_code=503
        ) from e

    try:
        response_payload = await asyncio.wait_for(future, timeout=timeout_seconds)
        return ExecutorRequestResult(
            request_id=request_id,
            executor_id=executor_id,
            payload=response_payload,
        )
    except asyncio.TimeoutError as exc:
        pop_pending_request(request_id)
        logger.warning(
            f"Executor request timeout: {request_type} "
            f"(timeout={timeout_seconds}s, executor={executor_id})"
        )
        raise ExecutorBridgeError(
            f"Executor request timeout: {request_type}", http_code=408
        ) from exc
    except Exception as e:
        pop_pending_request(request_id)
        logger.error(f"Executor request failed: {e}", exc_info=True)
        raise ExecutorBridgeError(
            f"Executor request failed: {e}",
            http_code=500
        ) from e
