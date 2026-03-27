"""Tests for backup APIs."""
from fastapi.testclient import TestClient


class TestBackupsList:
    def test_list_backups_empty(self, client: TestClient):
        """测试获取空的备份列表"""
        response = client.get("/api/v1/backups")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"] == []

    def test_list_backups_with_filter(self, client: TestClient):
        """测试按资源类型筛选备份"""
        response = client.get("/api/v1/backups?resource=testcase")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert isinstance(body["data"], list)


class TestBackupsCreate:
    def test_create_backup_success(self, client: TestClient):
        """测试成功创建备份"""
        response = client.post(
            "/api/v1/backups",
            json={
                "resource": "testcase",
                "resource_id": "1",
                "name": "Test Backup",
                "description": "Test backup description"
            }
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["resource"] == "testcase"


class TestBackupsRestore:
    def test_restore_backup_without_confirmation(self, client: TestClient):
        """测试未确认的备份恢复"""
        response = client.post(
            "/api/v1/backups/test-backup-id/restore",
            json={"confirm": False}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0
        assert "Confirmation required" in body["message"]

    def test_restore_backup_with_confirmation(self, client: TestClient):
        """测试已确认的备份恢复"""
        response = client.post(
            "/api/v1/backups/test-backup-id/restore",
            json={"confirm": True}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0


class TestBackupsDelete:
    def test_delete_backup_success(self, client: TestClient):
        """测试删除备份"""
        response = client.delete("/api/v1/backups/test-backup-id")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
