"""Tests for profile APIs."""
from fastapi.testclient import TestClient


class TestProfilesList:
    def test_list_profiles_empty(self, client: TestClient):
        """测试获取空的配置列表"""
        response = client.get("/api/v1/profiles")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["total"] == 0
        assert body["data"]["items"] == []

    def test_list_profiles_with_data(self, client: TestClient, profile):
        """测试获取配置列表"""
        response = client.get("/api/v1/profiles")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["total"] == 1
        assert len(body["data"]["items"]) == 1
        assert body["data"]["items"][0]["name"] == "staging"

    def test_list_profiles_pagination(self, client: TestClient, db):
        """测试配置列表分页"""
        from app.models.profile import Profile
        for i in range(5):
            profile = Profile(
                name=f"profile_{i}",
                description=f"Test profile {i}",
                variables={"key": f"value_{i}"}
            )
            db.add(profile)
        db.commit()

        response = client.get("/api/v1/profiles?page=1&page_size=3")
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["total"] == 5
        assert len(body["data"]["items"]) == 3


class TestProfilesCreate:
    def test_create_profile_success(self, client: TestClient):
        """测试成功创建配置"""
        response = client.post(
            "/api/v1/profiles",
            json={
                "name": "production",
                "description": "Production environment",
                "variables": {"base_url": "https://api.example.com"}
            }
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["name"] == "production"
        assert body["data"]["variables"]["base_url"] == "https://api.example.com"

    def test_create_profile_duplicate_name(self, client: TestClient, profile):
        """测试创建重复名称的配置"""
        response = client.post(
            "/api/v1/profiles",
            json={
                "name": "staging",
                "description": "Duplicate name",
                "variables": {}
            }
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0


class TestProfilesGet:
    def test_get_profile_success(self, client: TestClient, profile):
        """测试获取单个配置"""
        response = client.get(f"/api/v1/profiles/{profile.id}")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["name"] == "staging"

    def test_get_profile_not_found(self, client: TestClient):
        """测试获取不存在的配置"""
        response = client.get("/api/v1/profiles/99999")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0


class TestProfilesUpdate:
    def test_update_profile_success(self, client: TestClient, profile):
        """测试更新配置"""
        response = client.put(
            f"/api/v1/profiles/{profile.id}",
            json={
                "name": "staging_updated",
                "description": "Updated description",
                "variables": {"base_url": "https://staging-updated.example.com"}
            }
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["name"] == "staging_updated"

    def test_update_profile_not_found(self, client: TestClient):
        """测试更新不存在的配置"""
        response = client.put(
            "/api/v1/profiles/99999",
            json={"name": "test", "description": "test", "variables": {}}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0


class TestProfilesDelete:
    def test_delete_profile_success(self, client: TestClient, db):
        """测试删除配置"""
        from app.models.profile import Profile
        profile = Profile(
            name="to_delete",
            description="Will be deleted",
            variables={}
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

        response = client.delete(f"/api/v1/profiles/{profile.id}")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0

    def test_delete_profile_not_found(self, client: TestClient):
        """测试删除不存在的配置"""
        response = client.delete("/api/v1/profiles/99999")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0
