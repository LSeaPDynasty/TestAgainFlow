"""
Testcases API 测试

测试覆盖：
- 用例 CRUD
- 依赖链验证
- 用例复制
- 三种流程角色 (setup/main/teardown)
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestTestcasesCreate:
    """用例创建接口测试"""

    def test_create_testcase_success(
        self,
        client: TestClient,
        db: Session,
        flow
    ):
        """TC-TC-001: 正常创建用例"""
        response = client.post(
            "/api/v1/testcases",
            json={
                "name": "LoginTest",
                "description": "验证登录功能",
                "priority": "P1",
                "timeout": 120,
                "main_flows": [
                    {"flow_id": flow.id, "order": 1, "enabled": True}
                ]
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
        assert data["data"]["name"] == "LoginTest"
        assert data["data"]["priority"] == "P1"

    def test_create_testcase_with_setup_teardown(
        self,
        client: TestClient,
        db: Session,
        flow
    ):
        """TC-TC-002: 创建含 setup/teardown 的用例"""
        from tests.factories import TestDataFactory
        setup_flow = TestDataFactory.create_flow(db, name="SetupFlow")
        teardown_flow = TestDataFactory.create_flow(db, name="TeardownFlow")

        response = client.post(
            "/api/v1/testcases",
            json={
                "name": "FullTest",
                "priority": "P0",
                "setup_flows": [
                    {"flow_id": setup_flow.id, "order": 1, "enabled": True}
                ],
                "main_flows": [
                    {"flow_id": flow.id, "order": 1, "enabled": True}
                ],
                "teardown_flows": [
                    {"flow_id": teardown_flow.id, "order": 1, "enabled": True}
                ]
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
        assert data["data"]["setup_flow_count"] == 1
        assert data["data"]["main_flow_count"] == 1
        assert data["data"]["teardown_flow_count"] == 1

    def test_create_testcase_flows_empty(
        self,
        client: TestClient,
        db: Session
    ):
        """TC-TC-003: main_flows 为空"""
        response = client.post(
            "/api/v1/testcases",
            json={
                "name": "EmptyTest",
                "priority": "P2",
                "main_flows": []
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 4001
        assert "flow" in data["message"].lower()

    def test_create_testcase_invalid_priority(
        self,
        client: TestClient,
        db: Session,
        flow
    ):
        """TC-TC-004: 不合法的 priority"""
        response = client.post(
            "/api/v1/testcases",
            json={
                "name": "Test",
                "priority": "P5",  # 无效优先级
                "main_flows": [
                    {"flow_id": flow.id, "order": 1}
                ]
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 4001
        assert "priority" in data["message"].lower()

    def test_create_testcase_invalid_flow_id(
        self,
        client: TestClient,
        db: Session
    ):
        """TC-TC-005: 引用不存在的 flow_id"""
        response = client.post(
            "/api/v1/testcases",
            json={
                "name": "Test",
                "priority": "P1",
                "main_flows": [
                    {"flow_id": 999, "order": 1}
                ]
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 4004
        assert "flow" in data["message"].lower()

    def test_create_testcase_duplicate_name(
        self,
        client: TestClient,
        db: Session,
        flow
    ):
        """TC-TC-006: 用例名称重复"""
        from tests.factories import TestDataFactory

        # 创建第一个用例
        TestDataFactory.create_testcase(
            db,
            name="DuplicateTest",
            main_flows=[{"flow_id": flow.id, "order": 1}]
        )

        # 尝试创建同名用例
        response = client.post(
            "/api/v1/testcases",
            json={
                "name": "DuplicateTest",
                "priority": "P1",
                "main_flows": [
                    {"flow_id": flow.id, "order": 1}
                ]
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 4009
        assert "exists" in data["message"].lower()

    def test_create_testcase_with_tags(
        self,
        client: TestClient,
        db: Session,
        flow
    ):
        """TC-TC-007: 创建带标签的用例"""
        from tests.factories import TestDataFactory
        tag1 = TestDataFactory.create_tag(db, name="smoke")
        tag2 = TestDataFactory.create_tag(db, name="regression")

        response = client.post(
            "/api/v1/testcases",
            json={
                "name": "TaggedTest",
                "priority": "P1",
                "main_flows": [
                    {"flow_id": flow.id, "order": 1}
                ],
                "tag_ids": [tag1.id, tag2.id]
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
        assert len(data["data"]["tags"]) == 2

    def test_create_testcase_with_params(
        self,
        client: TestClient,
        db: Session,
        flow
    ):
        """TC-TC-008: 创建含参数的用例"""
        response = client.post(
            "/api/v1/testcases",
            json={
                "name": "ParamTest",
                "priority": "P1",
                "params": {
                    "username": "test_user",
                    "password": "test_pass",
                    "iterations": 3
                },
                "main_flows": [
                    {
                        "flow_id": flow.id,
                        "order": 1,
                        "params": {
                            "username": "{{params.username}}"
                        }
                    }
                ]
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
        assert data["data"]["params"]["username"] == "test_user"


class TestTestcasesUpdate:
    """用例更新接口测试"""

    def test_update_testcase_success(
        self,
        client: TestClient,
        db: Session,
        testcase
    ):
        """TC-TC-020: 正常更新用例"""
        response = client.put(
            f"/api/v1/testcases/{testcase.id}",
            json={
                "description": "更新后的描述",
                "priority": "P0"
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
        assert data["data"]["description"] == "更新后的描述"
        assert data["data"]["priority"] == "P0"

    def test_update_testcase_not_found(
        self,
        client: TestClient
    ):
        """TC-TC-021: 更新不存在的用例"""
        response = client.put(
            "/api/v1/testcases/999",
            json={"description": "测试"}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 4004


class TestTestcasesDuplicate:
    """用例复制接口测试"""

    def test_duplicate_testcase_success(
        self,
        client: TestClient,
        db: Session,
        testcase
    ):
        """TC-TC-030: 正常复制用例"""
        response = client.post(
            f"/api/v1/testcases/{testcase.id}/duplicate",
            json={
                "new_name": "CopiedTest"
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
        assert data["data"]["name"] == "CopiedTest"
        # 验证流程也被复制
        expected_main_flow_count = len([tf for tf in testcase.testcase_flows if tf.flow_role == 'main'])
        assert data["data"]["main_flow_count"] == expected_main_flow_count

    def test_duplicate_testcase_not_found(
        self,
        client: TestClient
    ):
        """TC-TC-031: 复制不存在的用例"""
        response = client.post(
            "/api/v1/testcases/999/duplicate",
            json={"new_name": "Copy"}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 4004

    def test_duplicate_testcase_name_exists(
        self,
        client: TestClient,
        db: Session,
        testcase
    ):
        """TC-TC-032: 复制后的名称已存在"""
        response = client.post(
            f"/api/v1/testcases/{testcase.id}/duplicate",
            json={
                "new_name": testcase.name
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 4009
        assert "exists" in data["message"].lower()


class TestTestcasesDelete:
    """用例删除接口测试"""

    def test_delete_testcase_success(
        self,
        client: TestClient,
        db: Session,
        flow
    ):
        """TC-TC-040: 删除用例 - 成功"""
        from tests.factories import TestDataFactory
        testcase = TestDataFactory.create_testcase(
            db,
            name="TempTest",
            main_flows=[{"flow_id": flow.id, "order": 1}]
        )

        response = client.delete(f"/api/v1/testcases/{testcase.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0

    def test_delete_testcase_in_suite(
        self,
        client: TestClient,
        db: Session,
        testcase
    ):
        """TC-TC-041: 删除被套件引用的用例"""
        from tests.factories import TestDataFactory
        # 创建套件并引用用例
        suite = TestDataFactory.create_suite(
            db,
            name="TestSuite",
            testcase_ids=[testcase.id]
        )

        response = client.delete(f"/api/v1/testcases/{testcase.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 4022
        assert "referenced" in data["message"].lower()


class TestTestcasesList:
    """用例列表接口测试"""

    def test_list_testcases_by_priority(
        self,
        client: TestClient,
        db: Session,
        testcase
    ):
        """按优先级筛选用例"""
        from tests.factories import TestDataFactory
        TestDataFactory.create_testcase(
            db,
            name="P0Test",
            priority="P0",
            main_flows=[]
        )

        response = client.get("/api/v1/testcases?priority=P1")
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
        assert all(tc["priority"] == "P1" for tc in data["data"]["items"])

    def test_list_testcases_by_tag(
        self,
        client: TestClient,
        db: Session,
        flow
    ):
        """按标签筛选用例"""
        from tests.factories import TestDataFactory
        tag = TestDataFactory.create_tag(db, name="smoke")

        TestDataFactory.create_testcase(
            db,
            name="SmokeTest",
            main_flows=[{"flow_id": flow.id, "order": 1}],
            tag_ids=[tag.id]
        )

        response = client.get(f"/api/v1/testcases?tag_id={tag.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
        assert all(any(t["id"] == tag.id for t in tc["tags"])
                   for tc in data["data"]["items"])

    def test_list_testcases_search(
        self,
        client: TestClient,
        db: Session,
        testcase
    ):
        """关键词搜索用例"""
        response = client.get("/api/v1/testcases?search=Login")
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
        assert any("Login" in tc["name"] for tc in data["data"]["items"])

    def test_list_testcases_with_stats(
        self,
        client: TestClient,
        db: Session,
        testcase
    ):
        """获取用例列表（含统计信息）"""
        response = client.get("/api/v1/testcases?include_stats=true")
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
        item = data["data"]["items"][0]
        assert "step_count" in item
        assert "estimated_duration" in item
        assert "suite_count" in item


class TestTestcasesDependencyChain:
    """用例依赖链测试"""

    def test_get_dependency_chain(
        self,
        client: TestClient,
        db: Session,
        testcase
    ):
        """TC-TC-050: 获取用例依赖链"""
        response = client.get(f"/api/v1/testcases/{testcase.id}/dependency-chain")
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
        assert "setup_flows" in data["data"]
        assert "main_flows" in data["data"]
        assert "teardown_flows" in data["data"]
        assert "all_steps" in data["data"]
        assert "required_profiles" in data["data"]

    def test_dependency_chain_includes_flow_details(
        self,
        client: TestClient,
        db: Session,
        testcase
    ):
        """TC-TC-051: 依赖链包含流程详情"""
        response = client.get(f"/api/v1/testcases/{testcase.id}/dependency-chain")
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0

        # 验证流程详情包含步骤信息
        if len(data["data"]["main_flows"]) > 0:
            flow = data["data"]["main_flows"][0]
            assert "steps" in flow
            assert "requires" in flow
