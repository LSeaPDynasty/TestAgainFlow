"""Tests for /ws/executor websocket protocol behavior."""
from __future__ import annotations

import asyncio
import time

import pytest

from app.routers import websocket as websocket_router


@pytest.fixture(autouse=True)
def _reset_websocket_state():
    websocket_router.pending_test_requests.clear()
    websocket_router.manager.active_connections.clear()
    websocket_router.manager.connection_types.clear()
    yield
    websocket_router.pending_test_requests.clear()
    websocket_router.manager.active_connections.clear()
    websocket_router.manager.connection_types.clear()


def test_executor_websocket_protocol_errors_and_status(client):
    with client.websocket_connect("/ws/executor") as ws:
        connected = ws.receive_json()
        assert connected["type"] == "connected"
        assert connected["executor_id"]

        ws.send_text("{invalid_json")
        invalid_json = ws.receive_json()
        assert invalid_json["type"] == "error"
        assert invalid_json["code"] == "invalid_json"

        ws.send_json({"type": "unknown_message"})
        unknown_type = ws.receive_json()
        assert unknown_type["type"] == "error"
        assert unknown_type["code"] == "unknown_message_type"

        ws.send_json({"type": "task_update", "data": {"status": "running"}})
        missing_field = ws.receive_json()
        assert missing_field["type"] == "error"
        assert missing_field["code"] == "missing_field"

        ws.send_json({"type": "subscribe", "client_type": "gui"})
        subscribed = ws.receive_json()
        assert subscribed["type"] == "subscribed"
        assert subscribed["client_type"] == "gui"

        ws.send_json({"type": "get_status"})
        current_status = ws.receive_json()
        assert current_status["type"] == "current_status"
        assert current_status["connection_count"] >= 1

        ws.send_json({"type": "ping"})
        pong = ws.receive_json()
        assert pong["type"] == "pong"


@pytest.mark.asyncio
async def test_cleanup_expired_pending_requests_cancels_future():
    future = asyncio.get_running_loop().create_future()
    websocket_router.register_pending_request("expired_1", future, timeout_seconds=1.0)

    removed = websocket_router.cleanup_expired_pending_requests(now=time.time() + 10.0)
    assert removed == 1
    assert future.cancelled()
    assert "expired_1" not in websocket_router.pending_test_requests


@pytest.mark.asyncio
async def test_resolve_pending_request_sets_result_and_removes_entry():
    future = asyncio.get_running_loop().create_future()
    websocket_router.register_pending_request("req_1", future, timeout_seconds=30.0)

    resolved = websocket_router.resolve_pending_request("req_1", {"ok": True})
    assert resolved is True
    assert future.done()
    assert future.result() == {"ok": True}
    assert "req_1" not in websocket_router.pending_test_requests
