"""
Steps API 测试

测试覆盖：
- 步骤 CRUD
- 操作类型验证
- 断言配置验证
- 元素和界面关联验证
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestStepsCreate:
    """步骤创建接口测试"""

    def test_create_click_step_success(
        self,
        client: TestClient,
        db: Session,
        screen,
        element
    ):
        """TC-ST-001: 正常创建 click 类型步骤"""
        response = client.post(
            "/api/v1/steps",
            json={
                "name": "点击登录按钮",
                "screen_id": screen.id,
                "action_type": "click",
                "element_id": element.id,
                "wait_after_ms": 500
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
        assert data["data"]["action_type"] == "click"
        assert data["data"]["element_name"] == "loginBtn"

    def test_create_input_step_with_variable(
        self,
        client: TestClient,
        db: Session,
        screen,
        element
    ):
        """TC-ST-002: 创建 input 类型步骤（含变量）"""
        response = client.post(
            "/api/v1/steps",
            json={
                "name": "输入用户名",
                "screen_id": screen.id,
                "action_type": "input",
                "element_id": element.id,
                "action_value": "{{username}}"
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
        assert data["data"]["action_value"] == "{{username}}"

    def test_create_assert_text_step(
        self,
        client: TestClient,
        db: Session,
        screen
    ):
        """TC-ST-003: 创建 assert_text 类型步骤"""
        response = client.post(
            "/api/v1/steps",
            json={
                "name": "验证登录成功",
                "screen_id": screen.id,
                "action_type": "assert_text",
                "element_id": None,
                "assert_config": {
                    "type": "text",
                    "expected": "欢迎回来",
                    "on_fail": "stop"
                }
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
        assert data["data"]["assert_config"]["type"] == "text"

    def test_create_click_without_element_id(
        self,
        client: TestClient,
        db: Session,
        screen
    ):
        """TC-ST-004: 设备操作类型但未传 element_id"""
        response = client.post(
            "/api/v1/steps",
            json={
                "name": "点击某个按钮",
                "screen_id": screen.id,
                "action_type": "click",
                "element_id": None
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 4001
        assert "element" in data["message"].lower()

    def test_create_step_element_screen_mismatch(
        self,
        client: TestClient,
        db: Session,
        screen,
        element
    ):
        """TC-ST-005: element_id 与 screen_id 不匹配"""
        from tests.factories import TestDataFactory
        other_screen = TestDataFactory.create_screen(db, name="OtherScreen")

        response = client.post(
            "/api/v1/steps",
            json={
                "name": "点击登录按钮",
                "screen_id": other_screen.id,
                "action_type": "click",
                "element_id": element.id  # 元素属于 screen，不是 other_screen
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 4001
        assert "not belong" in data["message"].lower()

    def test_create_step_invalid_action_type(
        self,
        client: TestClient,
        db: Session,
        screen
    ):
        """TC-ST-006: 不合法的 action_type"""
        response = client.post(
            "/api/v1/steps",
            json={
                "name": "测试步骤",
                "screen_id": screen.id,
                "action_type": "fly",  # 无效类型
                "element_id": None
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 4001
        assert "action" in data["message"].lower()

    def test_create_step_invalid_on_fail(
        self,
        client: TestClient,
        db: Session,
        screen
    ):
        """TC-ST-007: assert_config.on_fail 非法值"""
        response = client.post(
            "/api/v1/steps",
            json={
                "name": "断言步骤",
                "screen_id": screen.id,
                "action_type": "assert_text",
                "assert_config": {
                    "type": "text",
                    "expected": "成功",
                    "on_fail": "explode"  # 无效值
                }
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 4001
        assert "on_fail" in data["message"].lower()


class TestStepsDelete:
    """步骤删除接口测试"""

    def test_delete_step_not_referenced(
        self,
        client: TestClient,
        db: Session,
        screen
    ):
        """TC-ST-021: 删除步骤 - 无引用，正常删除"""
        from tests.factories import TestDataFactory
        step = TestDataFactory.create_step(
            db,
            screen_id=screen.id,
            name="tempStep"
        )

        response = client.delete(f"/api/v1/steps/{step.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0

    def test_delete_step_referenced_by_flow(
        self,
        client: TestClient,
        db: Session,
        step
    ):
        """TC-ST-020: 删除步骤 - 被流程引用"""
        # Create a flow that uses this step
        from tests.factories import TestDataFactory
        TestDataFactory.create_flow(
            db,
            name="TestFlow",
            steps=[{"step_id": step.id, "order": 1}]
        )

        response = client.delete(f"/api/v1/steps/{step.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 4022
        assert "referenced" in data["message"].lower()


class TestStepsList:
    """步骤列表接口测试"""

    def test_list_steps_by_screen(
        self,
        client: TestClient,
        db: Session,
        screen,
        step
    ):
        """按界面筛选步骤"""
        response = client.get(f"/api/v1/steps?screen_id={screen.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
        assert data["data"]["total"] >= 1

    def test_list_steps_by_action_type(
        self,
        client: TestClient,
        db: Session,
        screen,
        step
    ):
        """按操作类型筛选步骤"""
        response = client.get(f"/api/v1/steps?action_type=click")
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
        # 至少包含我们创建的 click 步骤
        assert any(s["action_type"] == "click" for s in data["data"]["items"])
