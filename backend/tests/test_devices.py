"""Tests for device APIs."""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.services.executor_bridge import ExecutorBridgeError, ExecutorRequestResult


class TestDeviceConnection:
    def test_test_device_connection_success(self, client: TestClient, device, monkeypatch):
        async def _fake_request(*args, **kwargs):
            return ExecutorRequestResult(
                request_id="req_d1",
                executor_id="executor_1",
                payload={"results": {"connection": "success", "message": "ok"}},
            )

        monkeypatch.setattr("app.services.executor_bridge.request_executor", _fake_request)

        response = client.post(f"/api/v1/devices/{device.serial}/test")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["online"] is True
        assert body["data"]["executor_id"] == "executor_1"

    def test_test_device_connection_no_executor(self, client: TestClient, device, monkeypatch):
        async def _raise(*args, **kwargs):
            raise ExecutorBridgeError("No online executor available", http_code=503)

        monkeypatch.setattr("app.services.executor_bridge.request_executor", _raise)

        response = client.post(f"/api/v1/devices/{device.serial}/test")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 503
