"""Tests for run logs APIs."""
from fastapi.testclient import TestClient


class TestRunLogs:
    def test_get_run_logs_empty(self, client: TestClient):
        """测试获取空的运行日志"""
        response = client.get("/api/v1/run-logs/test-task-id")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"] == []

    def test_get_run_logs_with_task_id(self, client: TestClient):
        """测试根据任务ID获取运行日志"""
        response = client.get("/api/v1/run-logs/task-123")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert isinstance(body["data"], list)
