"""Tests for executor bridge service."""
from __future__ import annotations

import pytest

from app.services.executor_bridge import ExecutorBridgeError, request_executor


@pytest.fixture(autouse=True)
def _reset_state():
    from app.routers import executor_status
    from app.routers import websocket

    executor_status.active_executors.clear()
    websocket.pending_test_requests.clear()
    yield
    executor_status.active_executors.clear()
    websocket.pending_test_requests.clear()


@pytest.mark.asyncio
async def test_request_executor_no_executor_raises():
    with pytest.raises(ExecutorBridgeError) as exc_info:
        await request_executor("test_device", {"serial": "abc"}, request_prefix="unit")
    assert exc_info.value.http_code == 503


@pytest.mark.asyncio
async def test_request_executor_success(monkeypatch):
    from app.routers import executor_status
    from app.routers import websocket

    executor_status.active_executors["executor_1"] = {"tasks": []}

    async def _fake_broadcast(message, client_type):
        assert client_type == "executor"
        websocket.resolve_pending_request(
            message["request_id"],
            {"results": {"connection": "success", "message": "ok"}},
        )

    monkeypatch.setattr(websocket.manager, "broadcast", _fake_broadcast)

    result = await request_executor(
        "test_device",
        {"serial": "abc123"},
        request_prefix="unit",
        timeout_seconds=2.0,
        device_serial="abc123",
    )
    assert result.executor_id == "executor_1"
    assert result.payload["results"]["connection"] == "success"
