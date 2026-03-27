"""Scheduler API tests."""
from fastapi.testclient import TestClient


def test_scheduler_config_roundtrip(client: TestClient):
    response = client.get("/api/v1/scheduler/config")
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert "max_inflight_tasks" in body["data"]

    response = client.put(
        "/api/v1/scheduler/config",
        json={"max_inflight_tasks": 3, "default_priority": 2, "enabled": True},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["max_inflight_tasks"] == 3
    assert body["data"]["default_priority"] == 2
