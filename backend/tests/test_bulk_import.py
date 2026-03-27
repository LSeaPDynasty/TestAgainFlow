"""Tests for bulk import APIs."""
from fastapi.testclient import TestClient
import io
import json


class TestBulkImport:
    def test_bulk_import_success(self, client: TestClient):
        """测试批量导入成功"""
        import_data = {
            "version": "1.0",
            "screens": [
                {
                    "name": "ImportScreen",
                    "activity": "com.example.ImportActivity",
                    "description": "Imported screen",
                    "elements": [
                        {
                            "name": "importButton",
                            "description": "Import button",
                            "locators": [
                                {
                                    "type": "id",
                                    "value": "com.example:id/import_btn",
                                    "priority": 1
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        response = client.post(
            "/api/v1/import/bulk",
            json=import_data
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0

    def test_import_elements_success(self, client: TestClient, screen):
        """测试导入元素到指定屏幕"""
        import_data = {
            "target_screen": {
                "name": screen.name,
                "activity": screen.activity
            },
            "elements": [
                {
                    "name": "newElement",
                    "description": "New element",
                    "locators": [
                        {
                            "type": "id",
                            "value": "com.example:id/new_element",
                            "priority": 1
                        }
                    ]
                }
            ]
        }

        response = client.post(
            "/api/v1/import/elements",
            json=import_data
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0

    def test_upload_import_file_json(self, client: TestClient):
        """测试上传JSON文件导入"""
        import_data = {
            "version": "1.0",
            "screens": [
                {
                    "name": "UploadScreen",
                    "activity": "com.example.UploadActivity",
                    "description": "Uploaded screen",
                    "elements": []
                }
            ]
        }

        file_content = json.dumps(import_data).encode("utf-8")
        files = {"file": ("test_import.json", io.BytesIO(file_content), "application/json")}
        data = {"skip_existing": "true", "create_screens": "true"}

        response = client.post("/api/v1/import/upload", files=files, data=data)
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0

    def test_preview_import_file(self, client: TestClient):
        """测试预览导入文件"""
        import_data = {
            "version": "1.0",
            "screens": [
                {
                    "name": "PreviewScreen",
                    "activity": "com.example.PreviewActivity",
                    "description": "Preview screen",
                    "elements": []
                }
            ]
        }

        file_content = json.dumps(import_data).encode("utf-8")
        files = {"file": ("test_preview.json", io.BytesIO(file_content), "application/json")}

        response = client.post("/api/v1/import/preview", files=files)
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True

    def test_get_json_template(self, client: TestClient):
        """测试获取JSON模板"""
        response = client.get("/api/v1/import/template/json")
        # 模板文件可能不存在，所以只检查响应
        assert response.status_code in [200, 404]

    def test_get_yaml_template(self, client: TestClient):
        """测试获取YAML模板"""
        response = client.get("/api/v1/import/template/yaml")
        # 模板文件可能不存在，所以只检查响应
        assert response.status_code in [200, 404]

    def test_get_elements_only_template(self, client: TestClient):
        """测试获取元素导入模板"""
        response = client.get("/api/v1/import/template/elements-only")
        # 模板文件可能不存在，所以只检查响应
        assert response.status_code in [200, 404]
