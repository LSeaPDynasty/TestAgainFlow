"""Tests for tag APIs."""
from fastapi.testclient import TestClient


class TestTagsList:
    def test_list_tags_empty(self, client: TestClient):
        """测试获取空的标签列表"""
        response = client.get("/api/v1/tags")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["total"] == 0
        assert body["data"]["items"] == []

    def test_list_tags_with_data(self, client: TestClient, tag):
        """测试获取标签列表"""
        response = client.get("/api/v1/tags")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["total"] == 1
        assert len(body["data"]["items"]) == 1
        assert body["data"]["items"][0]["name"] == "smoke"

    def test_list_tags_pagination(self, client: TestClient, db):
        """测试标签列表分页"""
        from app.models.tag import Tag
        for i in range(5):
            tag = Tag(
                name=f"tag_{i}",
                color=f"#ff{i:02x}00"
            )
            db.add(tag)
        db.commit()

        response = client.get("/api/v1/tags?page=1&page_size=3")
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["total"] == 5
        assert len(body["data"]["items"]) == 3


class TestTagsCreate:
    def test_create_tag_success(self, client: TestClient):
        """测试成功创建标签"""
        response = client.post(
            "/api/v1/tags",
            json={
                "name": "regression",
                "color": "#00ff00",
                "description": "Regression tests"
            }
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["name"] == "regression"
        assert body["data"]["color"] == "#00ff00"

    def test_create_tag_duplicate_name(self, client: TestClient, tag):
        """测试创建重复名称的标签"""
        response = client.post(
            "/api/v1/tags",
            json={
                "name": "smoke",
                "color": "#000000",
                "description": "Duplicate name"
            }
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0


class TestTagsDelete:
    def test_delete_tag_success(self, client: TestClient, db):
        """测试删除标签"""
        from app.models.tag import Tag
        tag = Tag(
            name="to_delete",
            color="#ff0000"
        )
        db.add(tag)
        db.commit()
        db.refresh(tag)

        response = client.delete(f"/api/v1/tags/{tag.id}")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0

    def test_delete_tag_not_found(self, client: TestClient):
        """测试删除不存在的标签"""
        response = client.delete("/api/v1/tags/99999")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0
