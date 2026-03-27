"""Tests for project APIs."""
from fastapi.testclient import TestClient


class TestProjectsList:
    def test_list_projects_empty(self, client: TestClient):
        """测试获取空的项目列表"""
        response = client.get("/api/v1/projects")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["total"] == 0
        assert body["data"]["items"] == []

    def test_list_projects_with_data(self, client: TestClient, db):
        """测试获取项目列表"""
        from app.models.project import Project
        project = Project(
            name="TestProject",
            description="Test project description",
            status="active",
            priority="P1"
        )
        db.add(project)
        db.commit()

        response = client.get("/api/v1/projects")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["total"] == 1
        assert len(body["data"]["items"]) == 1
        assert body["data"]["items"][0]["name"] == "TestProject"

    def test_list_projects_pagination(self, client: TestClient, db):
        """测试项目列表分页"""
        from app.models.project import Project
        for i in range(5):
            project = Project(
                name=f"Project_{i}",
                description=f"Test project {i}",
                status="active",
                priority="P2"
            )
            db.add(project)
        db.commit()

        response = client.get("/api/v1/projects?page=1&page_size=3")
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["total"] == 5
        assert len(body["data"]["items"]) == 3

    def test_list_projects_filter_by_status(self, client: TestClient, db):
        """测试按状态筛选项目"""
        from app.models.project import Project
        project1 = Project(name="ActiveProject", description="Active", status="active", priority="P1")
        project2 = Project(name="ArchivedProject", description="Archived", status="archived", priority="P2")
        db.add_all([project1, project2])
        db.commit()

        response = client.get("/api/v1/projects?status=active")
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["total"] == 1
        assert body["data"]["items"][0]["status"] == "active"


class TestProjectsCreate:
    def test_create_project_success(self, client: TestClient):
        """测试成功创建项目"""
        response = client.post(
            "/api/v1/projects",
            json={
                "name": "NewProject",
                "description": "New project description",
                "status": "active",
                "priority": "P1"
            }
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["name"] == "NewProject"

    def test_create_project_duplicate_name(self, client: TestClient, db):
        """测试创建重复名称的项目"""
        from app.models.project import Project
        project = Project(name="Duplicate", description="Test", status="active", priority="P1")
        db.add(project)
        db.commit()

        response = client.post(
            "/api/v1/projects",
            json={"name": "Duplicate", "description": "Duplicate", "status": "active", "priority": "P1"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0


class TestProjectsGet:
    def test_get_project_success(self, client: TestClient, db):
        """测试获取单个项目"""
        from app.models.project import Project
        project = Project(name="GetProject", description="Get test", status="active", priority="P1")
        db.add(project)
        db.commit()
        db.refresh(project)

        response = client.get(f"/api/v1/projects/{project.id}")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["name"] == "GetProject"

    def test_get_project_not_found(self, client: TestClient):
        """测试获取不存在的项目"""
        response = client.get("/api/v1/projects/99999")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0


class TestProjectsUpdate:
    def test_update_project_success(self, client: TestClient, db):
        """测试更新项目"""
        from app.models.project import Project
        project = Project(name="ToUpdate", description="Update test", status="active", priority="P1")
        db.add(project)
        db.commit()
        db.refresh(project)

        response = client.put(
            f"/api/v1/projects/{project.id}",
            json={
                "name": "UpdatedProject",
                "description": "Updated description",
                "status": "completed",
                "priority": "P2"
            }
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["name"] == "UpdatedProject"

    def test_update_project_not_found(self, client: TestClient):
        """测试更新不存在的项目"""
        response = client.put(
            "/api/v1/projects/99999",
            json={"name": "test", "description": "test", "status": "active", "priority": "P1"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0


class TestProjectsDelete:
    def test_delete_project_success(self, client: TestClient, db):
        """测试删除项目"""
        from app.models.project import Project
        project = Project(name="ToDelete", description="Delete test", status="active", priority="P1")
        db.add(project)
        db.commit()
        db.refresh(project)

        response = client.delete(f"/api/v1/projects/{project.id}")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0

    def test_delete_project_not_found(self, client: TestClient):
        """测试删除不存在的项目"""
        response = client.delete("/api/v1/projects/99999")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0


class TestProjectsStatistics:
    def test_get_project_statistics_success(self, client: TestClient, db):
        """测试获取项目统计信息"""
        from app.models.project import Project
        project = Project(name="StatsProject", description="Stats test", status="active", priority="P1")
        db.add(project)
        db.commit()
        db.refresh(project)

        response = client.get(f"/api/v1/projects/{project.id}/stats")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert "data" in body

    def test_get_project_statistics_not_found(self, client: TestClient):
        """测试获取不存在项目的统计信息"""
        response = client.get("/api/v1/projects/99999/stats")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0
