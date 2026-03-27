"""
Flows API 测试

测试覆盖：
- 流程 CRUD
- DSL 验证
- 流程复制
- 三种流程类型 (standard/dsl/python)
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestFlowsCreate:
    """流程创建接口测试"""

    def test_create_standard_flow_success(
        self,
        client: TestClient,
        db: Session,
        step
    ):
        """TC-FL-001: 正常创建 standard 类型流程"""
        response = client.post(
            "/api/v1/flows",
            json={
                "name": "LoginFlow",
                "description": "登录流程",
                "flow_type": "standard",
                "steps": [
                    {"step_id": step.id, "order": 1}
                ]
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
        assert data["data"]["flow_type"] == "standard"
        assert data["data"]["step_count"] == 1

    def test_create_dsl_flow_success(
        self,
        client: TestClient,
        db: Session,
        step
    ):
        """TC-FL-002: 正常创建 dsl 类型流程"""
        dsl_content = """
- step_id: 1
  repeat: 3
- step_id: 1
  break_if: ${success} == true
"""
        response = client.post(
            "/api/v1/flows",
            json={
                "name": "DslFlow",
                "flow_type": "dsl",
                "dsl_content": dsl_content
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
        assert data["data"]["flow_type"] == "dsl"
        assert data["data"]["expanded_step_count"] == 4

    def test_create_flow_steps_empty(
        self,
        client: TestClient,
        db: Session
    ):
        """TC-FL-003: standard 类型但 steps 为空"""
        response = client.post(
            "/api/v1/flows",
            json={
                "name": "EmptyFlow",
                "flow_type": "standard",
                "steps": []
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 4001
        assert "step" in data["message"].lower()

    def test_create_flow_invalid_step_id(
        self,
        client: TestClient,
        db: Session
    ):
        """TC-FL-004: steps 中包含不存在的 step_id"""
        response = client.post(
            "/api/v1/flows",
            json={
                "name": "TestFlow",
                "flow_type": "standard",
                "steps": [
                    {"step_id": 999, "order": 1}
                ]
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 4004
        assert "step" in data["message"].lower()

    def test_create_flow_duplicate_name(
        self,
        client: TestClient,
        db: Session,
        step
    ):
        """TC-FL-005: 流程名称重复"""
        from tests.factories import TestDataFactory

        # 创建第一个流程
        TestDataFactory.create_flow(
            db,
            name="DuplicateFlow",
            steps=[{"step_id": step.id, "order": 1}]
        )

        # 尝试创建同名流程
        response = client.post(
            "/api/v1/flows",
            json={
                "name": "DuplicateFlow",
                "flow_type": "standard",
                "steps": [
                    {"step_id": step.id, "order": 1}
                ]
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 4009
        assert "exists" in data["message"].lower()

    def test_create_flow_invalid_type(
        self,
        client: TestClient,
        db: Session
    ):
        """TC-FL-006: 不合法的 flow_type"""
        response = client.post(
            "/api/v1/flows",
            json={
                "name": "TestFlow",
                "flow_type": "invalid_type",
                "steps": []
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 4001
        assert "flow_type" in data["message"].lower()

    def test_create_dsl_flow_invalid_yaml(
        self,
        client: TestClient,
        db: Session
    ):
        """TC-FL-007: dsl_content 不是合法的 YAML"""
        response = client.post(
            "/api/v1/flows",
            json={
                "name": "InvalidDslFlow",
                "flow_type": "dsl",
                "dsl_content": "invalid: yaml: content: ["
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 4001
        assert "yaml" in data["message"].lower() or "syntax" in data["message"].lower()

    def test_create_flow_with_requires(
        self,
        client: TestClient,
        db: Session,
        step
    ):
        """TC-FL-008: 创建带 requires 的流程"""
        response = client.post(
            "/api/v1/flows",
            json={
                "name": "FlowWithRequires",
                "flow_type": "standard",
                "requires": ["username", "password"],
                "default_params": {
                    "username": "test_user",
                    "timeout": 5000
                },
                "steps": [
                    {"step_id": step.id, "order": 1}
                ]
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
        assert data["data"]["requires"] == ["username", "password"]
        assert data["data"]["default_params"]["username"] == "test_user"

    def test_create_python_flow(
        self,
        client: TestClient,
        db: Session
    ):
        """TC-FL-009: 创建 python 类型流程"""
        response = client.post(
            "/api/v1/flows",
            json={
                "name": "PythonFlow",
                "flow_type": "python",
                "dsl_content": "def execute(context):\n    return {'success': True}"
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
        assert data["data"]["flow_type"] == "python"


class TestFlowsValidateDsl:
    """DSL 验证接口测试"""

    def test_dsl_validation_valid(
        self,
        client: TestClient,
        db: Session,
        step
    ):
        """TC-FL-010: DSL 验证通过"""
        dsl_content = f"""
- step_id: {step.id}
- step_id: {step.id}
  repeat: 3
"""
        response = client.post(
            "/api/v1/flows/validate-dsl",
            json={
                "dsl_content": dsl_content
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
        assert data["data"]["valid"] is True
        assert data["data"]["expanded_count"] == 4

    def test_dsl_validation_invalid_step_id(
        self,
        client: TestClient,
        db: Session
    ):
        """TC-FL-011: DSL 中引用不存在的 step_id"""
        dsl_content = """
- step_id: 999
"""
        response = client.post(
            "/api/v1/flows/validate-dsl",
            json={
                "dsl_content": dsl_content
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
        assert data["data"]["valid"] is False
        assert len(data["data"]["errors"]) > 0

    def test_dsl_validation_invalid_flow_name(
        self,
        client: TestClient,
        db: Session
    ):
        """TC-FL-012: DSL 中引用不存在的 flow_name"""
        dsl_content = """
- flow_name: NonExistentFlow
"""
        response = client.post(
            "/api/v1/flows/validate-dsl",
            json={
                "dsl_content": dsl_content
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
        assert data["data"]["valid"] is False
        assert any("flow" in error.lower() for error in data["data"]["errors"])

    def test_dsl_validation_with_call_directive(
        self,
        client: TestClient,
        db: Session,
        flow
    ):
        """TC-FL-013: DSL 验证包含 call 指令"""
        dsl_content = f"""
- flow_name: {flow.name}
  call:
    params:
      username: "test_user"
"""
        response = client.post(
            "/api/v1/flows/validate-dsl",
            json={
                "dsl_content": dsl_content
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
        assert data["data"]["valid"] is True


class TestFlowsUpdate:
    """流程更新接口测试"""

    def test_update_flow_success(
        self,
        client: TestClient,
        db: Session,
        flow
    ):
        """TC-FL-020: 正常更新流程"""
        response = client.put(
            f"/api/v1/flows/{flow.id}",
            json={
                "description": "更新后的描述",
                "requires": ["new_param"]
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
        assert data["data"]["description"] == "更新后的描述"
        assert data["data"]["requires"] == ["new_param"]

    def test_update_flow_not_found(
        self,
        client: TestClient
    ):
        """TC-FL-021: 更新不存在的流程"""
        response = client.put(
            "/api/v1/flows/999",
            json={"description": "测试"}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 4004


class TestFlowsDuplicate:
    """流程复制接口测试"""

    def test_duplicate_flow_success(
        self,
        client: TestClient,
        db: Session,
        flow
    ):
        """TC-FL-030: 正常复制流程"""
        response = client.post(
            f"/api/v1/flows/{flow.id}/duplicate",
            json={
                "new_name": "CopiedFlow"
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
        assert data["data"]["name"] == "CopiedFlow"
        assert data["data"]["step_count"] == len(flow.flow_steps)

    def test_duplicate_flow_not_found(
        self,
        client: TestClient
    ):
        """TC-FL-031: 复制不存在的流程"""
        response = client.post(
            "/api/v1/flows/999/duplicate",
            json={"new_name": "Copy"}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 4004

    def test_duplicate_flow_name_exists(
        self,
        client: TestClient,
        db: Session,
        flow
    ):
        """TC-FL-032: 复制后的名称已存在"""
        response = client.post(
            f"/api/v1/flows/{flow.id}/duplicate",
            json={
                "new_name": flow.name  # 使用原名称
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 4009
        assert "exists" in data["message"].lower()


class TestFlowsDelete:
    """流程删除接口测试"""

    def test_delete_flow_not_referenced(
        self,
        client: TestClient,
        db: Session,
        step
    ):
        """TC-FL-040: 删除流程 - 无引用"""
        from tests.factories import TestDataFactory
        flow = TestDataFactory.create_flow(
            db,
            name="TempFlow",
            steps=[{"step_id": step.id, "order": 1}]
        )

        response = client.delete(f"/api/v1/flows/{flow.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0

    def test_delete_flow_referenced_by_testcase(
        self,
        client: TestClient,
        db: Session,
        flow
    ):
        """TC-FL-041: 删除流程 - 被用例引用"""
        # Create a testcase that uses this flow
        from tests.factories import TestDataFactory
        TestDataFactory.create_testcase(
            db,
            name="TestForFlow",
            main_flows=[{"flow_id": flow.id, "order": 1}]
        )

        response = client.delete(f"/api/v1/flows/{flow.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 4022
        assert "referenced" in data["message"].lower()


class TestFlowsList:
    """流程列表接口测试"""

    def test_list_flows_by_type(
        self,
        client: TestClient,
        db: Session,
        flow
    ):
        """按流程类型筛选"""
        from tests.factories import TestDataFactory
        TestDataFactory.create_flow(
            db,
            name="DslFlow",
            flow_type="dsl"
        )

        response = client.get("/api/v1/flows?flow_type=standard")
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
        assert all(f["flow_type"] == "standard" for f in data["data"]["items"])

    def test_list_flows_search(
        self,
        client: TestClient,
        db: Session,
        flow
    ):
        """关键词搜索流程"""
        response = client.get("/api/v1/flows?search=Login")
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
        assert any("Login" in f["name"] for f in data["data"]["items"])

    def test_list_flows_with_stats(
        self,
        client: TestClient,
        db: Session,
        flow
    ):
        """获取流程列表（含统计信息）"""
        response = client.get("/api/v1/flows?include_stats=true")
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
        assert "step_count" in data["data"]["items"][0]
        assert "referenced_by_testcase_count" in data["data"]["items"][0]
