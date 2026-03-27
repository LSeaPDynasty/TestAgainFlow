"""Tests for suite APIs."""
from fastapi.testclient import TestClient


class TestSuitesList:
    def test_list_suites_empty(self, client: TestClient):
        """测试获取空的测试套件列表"""
        response = client.get("/api/v1/suites")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["total"] == 0
        assert body["data"]["items"] == []

    def test_list_suites_with_data(self, client: TestClient, suite):
        """测试获取测试套件列表"""
        response = client.get("/api/v1/suites")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["total"] == 1
        assert len(body["data"]["items"]) == 1
        assert body["data"]["items"][0]["name"] == "LoginSuite"

    def test_list_suites_pagination(self, client: TestClient, db):
        """测试测试套件列表分页"""
        from app.models.suite import Suite
        for i in range(5):
            suite = Suite(
                name=f"Suite_{i}",
                description=f"Test suite {i}",
                enabled=True
            )
            db.add(suite)
        db.commit()

        response = client.get("/api/v1/suites?page=1&page_size=3")
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["total"] == 5
        assert len(body["data"]["items"]) == 3


class TestSuitesCreate:
    def test_create_suite_success(self, client: TestClient):
        """测试成功创建测试套件"""
        response = client.post(
            "/api/v1/suites",
            json={
                "name": "UserManagement",
                "description": "User management test suite",
                "enabled": True
            }
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["name"] == "UserManagement"

    def test_create_suite_duplicate_name(self, client: TestClient, suite):
        """测试创建重复名称的测试套件"""
        response = client.post(
            "/api/v1/suites",
            json={
                "name": "LoginSuite",
                "description": "Duplicate name",
                "enabled": True
            }
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0


class TestSuitesGet:
    def test_get_suite_success(self, client: TestClient, suite):
        """测试获取单个测试套件"""
        response = client.get(f"/api/v1/suites/{suite.id}")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["name"] == "LoginSuite"

    def test_get_suite_not_found(self, client: TestClient):
        """测试获取不存在的测试套件"""
        response = client.get("/api/v1/suites/99999")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0


class TestSuitesUpdate:
    def test_update_suite_success(self, client: TestClient, suite):
        """测试更新测试套件"""
        response = client.put(
            f"/api/v1/suites/{suite.id}",
            json={
                "name": "LoginSuiteUpdated",
                "description": "Updated description",
                "enabled": False
            }
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["name"] == "LoginSuiteUpdated"

    def test_update_suite_not_found(self, client: TestClient):
        """测试更新不存在的测试套件"""
        response = client.put(
            "/api/v1/suites/99999",
            json={"name": "test", "description": "test", "enabled": True}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0


class TestSuitesDelete:
    def test_delete_suite_success(self, client: TestClient, db):
        """测试删除测试套件"""
        from app.models.suite import Suite
        suite = Suite(
            name="to_delete",
            description="Will be deleted",
            enabled=True
        )
        db.add(suite)
        db.commit()
        db.refresh(suite)

        response = client.delete(f"/api/v1/suites/{suite.id}")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0

    def test_delete_suite_not_found(self, client: TestClient):
        """测试删除不存在的测试套件"""
        response = client.delete("/api/v1/suites/99999")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0


class TestSuitesToggle:
    def test_toggle_suite_success(self, client: TestClient, suite):
        """测试切换测试套件启用状态"""
        response = client.patch(
            f"/api/v1/suites/{suite.id}/toggle",
            json={"enabled": False}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["enabled"] is False

    def test_toggle_suite_not_found(self, client: TestClient):
        """测试切换不存在的测试套件状态"""
        response = client.patch(
            "/api/v1/suites/99999/toggle",
            json={"enabled": False}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0
