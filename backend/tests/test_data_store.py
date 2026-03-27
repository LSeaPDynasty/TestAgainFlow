"""Tests for data store APIs."""
from fastapi.testclient import TestClient


class TestDataStoreGetAll:
    def test_get_all_data_empty(self, client: TestClient):
        """测试获取空的全部数据存储"""
        response = client.get("/api/v1/data-store")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert "data" in body


class TestDataStoreGetEnv:
    def test_get_env_data_success(self, client: TestClient):
        """测试获取环境数据"""
        response = client.get("/api/v1/data-store/production")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert isinstance(body["data"], dict)

    def test_get_env_data_with_nested_path(self, client: TestClient):
        """测试获取嵌套路径的环境数据"""
        response = client.get("/api/v1/data-store/production/config")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0


class TestDataStoreUpdate:
    def test_update_env_data_success(self, client: TestClient):
        """测试更新环境数据"""
        response = client.put(
            "/api/v1/data-store/production",
            json={"data": {"api_url": "https://api.example.com", "timeout": 30}}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert "updated successfully" in body["message"]


class TestDataStoreDelete:
    def test_delete_env_success(self, client: TestClient):
        """测试删除环境"""
        # 首先创建数据
        client.put(
            "/api/v1/data-store/temp",
            json={"data": {"test": "value"}}
        )

        # 然后删除
        response = client.delete("/api/v1/data-store/temp")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0

    def test_delete_env_not_found(self, client: TestClient):
        """测试删除不存在的环境"""
        response = client.delete("/api/v1/data-store/nonexistent")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert "not found" in body["message"]
