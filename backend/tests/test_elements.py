"""Elements API tests."""
from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services.executor_bridge import ExecutorBridgeError, ExecutorRequestResult


class TestElementsList:
    def test_get_elements_empty_db(self, client: TestClient):
        response = client.get("/api/v1/elements")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["items"] == []

    def test_get_elements_with_data(self, client: TestClient, db: Session, screen, element):
        from tests.factories import TestDataFactory

        TestDataFactory.create_element(db, screen_id=screen.id, name="usernameInput")

        response = client.get("/api/v1/elements")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["total"] == 2


class TestElementsCRUD:
    def test_create_element(self, client: TestClient, screen):
        response = client.post(
            "/api/v1/elements",
            json={
                "name": "submitBtn",
                "description": "submit",
                "screen_id": screen.id,
                "locators": [{"type": "resource-id", "value": "app:id/submit", "priority": 1}],
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["name"] == "submitBtn"

    def test_update_element(self, client: TestClient, element):
        response = client.put(
            f"/api/v1/elements/{element.id}",
            json={"name": "loginButton"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["name"] == "loginButton"

    def test_delete_element(self, client: TestClient, element):
        response = client.delete(f"/api/v1/elements/{element.id}")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0


class TestElementsLocatorTest:
    def test_test_element_success(self, client: TestClient, element, monkeypatch):
        async def _fake_request(*args, **kwargs):
            return ExecutorRequestResult(
                request_id="req_1",
                executor_id="executor_1",
                payload={"result": {"found": True, "bounds": {"left": 1, "top": 2}}},
            )

        monkeypatch.setattr("app.services.executor_bridge.request_executor", _fake_request)

        response = client.post(
            f"/api/v1/elements/{element.id}/test",
            json={"device_serial": "abc123def456", "locator_index": 0},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["found"] is True
        assert body["data"]["executor_id"] == "executor_1"

    def test_test_element_not_found(self, client: TestClient, element, monkeypatch):
        async def _fake_request(*args, **kwargs):
            return ExecutorRequestResult(
                request_id="req_2",
                executor_id="executor_1",
                payload={"result": {"found": False}},
            )

        monkeypatch.setattr("app.services.executor_bridge.request_executor", _fake_request)

        response = client.post(
            f"/api/v1/elements/{element.id}/test",
            json={"device_serial": "abc123def456", "locator_index": 0},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["found"] is False

    def test_test_element_no_executor(self, client: TestClient, element, monkeypatch):
        async def _raise(*args, **kwargs):
            raise ExecutorBridgeError("No online executor available", http_code=503)

        monkeypatch.setattr("app.services.executor_bridge.request_executor", _raise)

        response = client.post(
            f"/api/v1/elements/{element.id}/test",
            json={"device_serial": "abc123def456", "locator_index": 0},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 503
