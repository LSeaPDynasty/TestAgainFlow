"""Tests for executor status APIs."""
from fastapi.testclient import TestClient


class TestExecutorStatus:
    def test_get_executor_status(self, client: TestClient):
        """测试获取执行器状态"""
        response = client.get("/api/v1/executor/status")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert isinstance(body["data"], dict)


class TestExecutorTasks:
    def test_get_active_tasks(self, client: TestClient):
        """测试获取活动任务"""
        response = client.get("/api/v1/executor/tasks")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert isinstance(body["data"], list)


class TestExecutorDevices:
    def test_get_executor_devices(self, client: TestClient):
        """测试获取执行器设备"""
        response = client.get("/api/v1/executor/devices")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert isinstance(body["data"], list)
