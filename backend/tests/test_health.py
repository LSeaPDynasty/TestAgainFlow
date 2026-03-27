"""Tests for health check API."""
from fastapi.testclient import TestClient


class TestHealthCheck:
    def test_health_check_success(self, client: TestClient):
        """测试健康检查接口成功响应"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert "data" in body
        assert "message" in body

    def test_health_check_contains_system_info(self, client: TestClient):
        """测试健康检查返回系统信息"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        body = response.json()
        data = body["data"]
        # 验证返回的数据包含系统健康信息
        assert isinstance(data, dict)
