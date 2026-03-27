"""Tests for screen APIs."""
from fastapi.testclient import TestClient


class TestScreensList:
    def test_list_screens_empty(self, client: TestClient):
        """测试获取空的屏幕列表"""
        response = client.get("/api/v1/screens")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["total"] == 0
        assert body["data"]["items"] == []

    def test_list_screens_with_data(self, client: TestClient, screen):
        """测试获取屏幕列表"""
        response = client.get("/api/v1/screens")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["total"] == 1
        assert len(body["data"]["items"]) == 1
        assert body["data"]["items"][0]["name"] == "LoginPage"

    def test_list_screens_pagination(self, client: TestClient, db):
        """测试屏幕列表分页"""
        from app.models.screen import Screen
        for i in range(5):
            screen = Screen(
                name=f"Screen_{i}",
                activity=f"com.example.app.Activity{i}",
                description=f"Test screen {i}"
            )
            db.add(screen)
        db.commit()

        response = client.get("/api/v1/screens?page=1&page_size=3")
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["total"] == 5
        assert len(body["data"]["items"]) == 3

    def test_list_screens_search(self, client: TestClient, db):
        """测试搜索屏幕"""
        from app.models.screen import Screen
        screen1 = Screen(name="LoginScreen", activity="com.app.Login", description="Login")
        screen2 = Screen(name="HomeScreen", activity="com.app.Home", description="Home")
        db.add_all([screen1, screen2])
        db.commit()

        response = client.get("/api/v1/screens?search=Login")
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["total"] == 1
        assert body["data"]["items"][0]["name"] == "LoginScreen"


class TestScreensCreate:
    def test_create_screen_success(self, client: TestClient):
        """测试成功创建屏幕"""
        response = client.post(
            "/api/v1/screens",
            json={
                "name": "RegisterPage",
                "activity": "com.example.app.RegisterActivity",
                "description": "注册页面"
            }
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["name"] == "RegisterPage"

    def test_create_screen_duplicate_name(self, client: TestClient, screen):
        """测试创建重复名称的屏幕"""
        response = client.post(
            "/api/v1/screens",
            json={
                "name": "LoginPage",
                "activity": "com.example.app.DuplicateActivity",
                "description": "Duplicate name"
            }
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0


class TestScreensGet:
    def test_get_screen_success(self, client: TestClient, screen):
        """测试获取单个屏幕"""
        response = client.get(f"/api/v1/screens/{screen.id}")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["name"] == "LoginPage"

    def test_get_screen_not_found(self, client: TestClient):
        """测试获取不存在的屏幕"""
        response = client.get("/api/v1/screens/99999")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0


class TestScreensUpdate:
    def test_update_screen_success(self, client: TestClient, screen):
        """测试更新屏幕"""
        response = client.put(
            f"/api/v1/screens/{screen.id}",
            json={
                "name": "LoginPageUpdated",
                "activity": "com.example.app.LoginActivity",
                "description": "Updated description"
            }
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["name"] == "LoginPageUpdated"

    def test_update_screen_not_found(self, client: TestClient):
        """测试更新不存在的屏幕"""
        response = client.put(
            "/api/v1/screens/99999",
            json={"name": "test", "activity": "test", "description": "test"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0


class TestScreensDelete:
    def test_delete_screen_success(self, client: TestClient, db):
        """测试删除屏幕"""
        from app.models.screen import Screen
        screen = Screen(
            name="to_delete",
            activity="com.example.app.DeleteActivity",
            description="Will be deleted"
        )
        db.add(screen)
        db.commit()
        db.refresh(screen)

        response = client.delete(f"/api/v1/screens/{screen.id}")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0

    def test_delete_screen_not_found(self, client: TestClient):
        """测试删除不存在的屏幕"""
        response = client.delete("/api/v1/screens/99999")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0


class TestScreensElements:
    def test_get_screen_elements_empty(self, client: TestClient, screen):
        """测试获取屏幕的空元素列表"""
        response = client.get(f"/api/v1/screens/{screen.id}/elements")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"] == []

    def test_get_screen_elements_with_data(self, client: TestClient, element):
        """测试获取屏幕的元素列表"""
        response = client.get(f"/api/v1/screens/{element.screen_id}/elements")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert len(body["data"]) == 1
        assert body["data"][0]["name"] == "loginBtn"
