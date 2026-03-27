"""Tests for AI APIs."""
from fastapi.testclient import TestClient


class TestAIElementsSuggest:
    def test_suggest_elements_success(self, client: TestClient, screen):
        """测试AI元素推荐"""
        request_data = {
            "dom_element": {
                "tagName": "button",
                "text": "Submit",
                "resourceId": "com.example:id/submit_btn",
                "bounds": {"left": 100, "top": 200, "right": 300, "bottom": 250}
            },
            "screen_id": screen.id,
            "threshold": 0.8
        }

        response = client.post("/api/v1/ai/elements/suggest", json=request_data)
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0


class TestAITestcasesGenerate:
    def test_generate_testcase_success(self, client: TestClient):
        """测试AI生成测试用例"""
        request_data = {
            "json_data": {
                "name": "Login Test",
                "description": "Test user login functionality",
                "steps": [
                    {"action": "click", "element": "username_field"},
                    {"action": "input", "value": "testuser"},
                    {"action": "click", "element": "password_field"},
                    {"action": "input", "value": "testpass"},
                    {"action": "click", "element": "login_button"}
                ]
            },
            "project_id": None
        }

        response = client.post("/api/v1/ai/testcases/generate", json=request_data)
        assert response.status_code == 200
        body = response.json()
        assert "code" in body


class TestAIStepsGenerate:
    def test_generate_step_success(self, client: TestClient):
        """测试AI生成测试步骤"""
        response = client.post(
            "/api/v1/ai/steps/generate?step_description=Click the login button"
        )
        assert response.status_code == 200
        body = response.json()
        assert "code" in body


class TestAIConfig:
    def test_list_ai_configs(self, client: TestClient):
        """测试获取AI配置列表"""
        response = client.get("/api/v1/ai/config")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert isinstance(body["data"], list)

    def test_list_ai_configs_active_only(self, client: TestClient):
        """测试只获取启用的AI配置"""
        response = client.get("/api/v1/ai/config?active_only=true")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0

    def test_get_active_config(self, client: TestClient):
        """测试获取当前激活的AI配置"""
        response = client.get("/api/v1/ai/config/active")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0

    def test_create_ai_config_success(self, client: TestClient):
        """测试创建AI配置"""
        request_data = {
            "provider": "openai",
            "name": "test-config",
            "config_data": {
                "api_key": "test-key",
                "model": "gpt-4"
            },
            "priority": 1,
            "is_active": False
        }

        response = client.post("/api/v1/ai/config", json=request_data)
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0

    def test_create_ai_config_duplicate_name(self, client: TestClient, db):
        """测试创建重复名称的AI配置"""
        from app.models.ai_config import AIConfig
        config = AIConfig(
            provider="openai",
            name="duplicate-test",
            config_data={"api_key": "key1"},
            priority=1,
            is_active=True
        )
        db.add(config)
        db.commit()

        request_data = {
            "provider": "openai",
            "name": "duplicate-test",
            "config_data": {"api_key": "key2"},
            "priority": 2,
            "is_active": True
        }

        response = client.post("/api/v1/ai/config", json=request_data)
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0

    def test_update_ai_config_success(self, client: TestClient, db):
        """测试更新AI配置"""
        from app.models.ai_config import AIConfig
        config = AIConfig(
            provider="openai",
            name="to-update",
            config_data={"api_key": "old-key"},
            priority=1,
            is_active=True
        )
        db.add(config)
        db.commit()
        db.refresh(config)

        request_data = {
            "name": "updated-name",
            "priority": 2
        }

        response = client.put(f"/api/v1/ai/config/{config.id}", json=request_data)
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0

    def test_delete_ai_config_success(self, client: TestClient, db):
        """测试删除AI配置"""
        from app.models.ai_config import AIConfig
        config = AIConfig(
            provider="openai",
            name="to-delete",
            config_data={"api_key": "delete-key"},
            priority=1,
            is_active=True
        )
        db.add(config)
        db.commit()
        db.refresh(config)

        response = client.delete(f"/api/v1/ai/config/{config.id}")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0


class TestAIStats:
    def test_get_daily_stats(self, client: TestClient):
        """测试获取每日AI使用统计"""
        response = client.get("/api/v1/ai/stats/daily")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0

    def test_get_recent_logs(self, client: TestClient):
        """测试获取最近的AI请求日志"""
        response = client.get("/api/v1/ai/logs/recent?limit=10")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert isinstance(body["data"], list)
