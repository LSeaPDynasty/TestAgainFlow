"""Tests for executor capabilities APIs."""
from fastapi.testclient import TestClient


class TestExecutorCapabilitiesRegister:
    def test_register_executor_success(self, client: TestClient):
        """测试成功注册执行器"""
        request_data = {
            "executor_id": "test-executor-001",
            "executor_version": "1.0.0",
            "hostname": "test-host",
            "ip_address": "192.168.1.100",
            "capabilities": [
                {
                    "type_code": "click",
                    "display_name": "点击",
                    "category": "设备操作",
                    "description": "点击屏幕元素",
                    "color": "blue",
                    "requires_element": True,
                    "requires_value": False,
                    "implementation_version": "1.0"
                },
                {
                    "type_code": "screenshot",
                    "display_name": "截图",
                    "category": "系统",
                    "description": "截取设备屏幕",
                    "color": "gold",
                    "requires_element": False,
                    "requires_value": False,
                    "implementation_version": "1.0"
                }
            ]
        }

        response = client.post("/api/v1/executor-capabilities/register", json=request_data)
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["executor_id"] == "test-executor-001"


class TestExecutorCapabilitiesHeartbeat:
    def test_executor_heartbeat_success(self, client: TestClient):
        """测试执行器心跳成功"""
        request_data = {
            "executor_id": "test-executor-001",
            "executor_version": "1.0.0"
        }

        response = client.post("/api/v1/executor-capabilities/heartbeat", json=request_data)
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["status"] == "ok"

    def test_executor_heartbeat_missing_id(self, client: TestClient):
        """测试执行器心跳缺少executor_id"""
        request_data = {
            "executor_version": "1.0.0"
        }

        response = client.post("/api/v1/executor-capabilities/heartbeat", json=request_data)
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0


class TestExecutorCapabilitiesActionTypes:
    def test_get_action_types_success(self, client: TestClient):
        """测试获取操作类型列表"""
        response = client.get("/api/v1/executor-capabilities/action-types")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert "total" in body["data"]
        assert "items" in body["data"]
        assert "categories" in body["data"]

    def test_get_action_types_include_deprecated(self, client: TestClient):
        """测试获取操作类型列表（包含已废弃）"""
        response = client.get("/api/v1/executor-capabilities/action-types?include_deprecated=true")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0


class TestExecutorCapabilitiesCheck:
    def test_check_capability_success(self, client: TestClient):
        """测试检查执行器能力"""
        request_data = {
            "executor_id": "test-executor-001",
            "action_types": ["click", "input", "screenshot"]
        }

        response = client.post("/api/v1/executor-capabilities/check-capability", json=request_data)
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert "is_supported" in body["data"]


class TestExecutorCapabilitiesValidateTestcase:
    def test_validate_testcase_success(self, client: TestClient, testcase):
        """测试验证用例是否可执行"""
        request_data = {
            "testcase_id": testcase.id,
            "executor_id": "test-executor-001",
            "skip_unsupported": False
        }

        response = client.post("/api/v1/executor-capabilities/validate-testcase", json=request_data)
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0

    def test_validate_testcase_not_found(self, client: TestClient):
        """测试验证不存在的用例"""
        request_data = {
            "testcase_id": 99999,
            "executor_id": "test-executor-001",
            "skip_unsupported": False
        }

        response = client.post("/api/v1/executor-capabilities/validate-testcase", json=request_data)
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0
