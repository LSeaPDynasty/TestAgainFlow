"""Tests for test plan APIs."""
from fastapi.testclient import TestClient


class TestPlansList:
    def test_list_test_plans_empty(self, client: TestClient):
        """测试获取空的测试计划列表"""
        response = client.get("/api/v1/test-plans")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["total"] == 0
        assert body["data"]["items"] == []

    def test_list_test_plans_with_data(self, client: TestClient, db):
        """测试获取测试计划列表"""
        from app.models.test_plan import TestPlan
        plan = TestPlan(
            name="SmokeTestPlan",
            description="Smoke testing plan",
            execution_strategy="sequential",
            max_parallel_tasks=1,
            enabled=True
        )
        db.add(plan)
        db.commit()

        response = client.get("/api/v1/test-plans")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["total"] == 1
        assert len(body["data"]["items"]) == 1
        assert body["data"]["items"][0]["name"] == "SmokeTestPlan"

    def test_list_test_plans_pagination(self, client: TestClient, db):
        """测试测试计划列表分页"""
        from app.models.test_plan import TestPlan
        for i in range(5):
            plan = TestPlan(
                name=f"TestPlan_{i}",
                description=f"Test plan {i}",
                execution_strategy="sequential",
                max_parallel_tasks=1,
                enabled=True
            )
            db.add(plan)
        db.commit()

        response = client.get("/api/v1/test-plans?page=1&page_size=3")
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["total"] == 5
        assert len(body["data"]["items"]) == 3


class TestPlansCreate:
    def test_create_test_plan_success(self, client: TestClient):
        """测试成功创建测试计划"""
        response = client.post(
            "/api/v1/test-plans",
            json={
                "name": "RegressionTestPlan",
                "description": "Regression testing plan",
                "execution_strategy": "parallel",
                "max_parallel_tasks": 3,
                "suites": []
            }
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["name"] == "RegressionTestPlan"

    def test_create_test_plan_with_suites(self, client: TestClient, suite):
        """测试创建包含套件的测试计划"""
        response = client.post(
            "/api/v1/test-plans",
            json={
                "name": "SuiteTestPlan",
                "description": "Test plan with suites",
                "execution_strategy": "sequential",
                "max_parallel_tasks": 1,
                "suites": [{"suite_id": suite.id, "order_index": 1}]
            }
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0


class TestPlansGet:
    def test_get_test_plan_success(self, client: TestClient, db):
        """测试获取单个测试计划"""
        from app.models.test_plan import TestPlan
        plan = TestPlan(
            name="DetailTestPlan",
            description="Test plan detail",
            execution_strategy="sequential",
            max_parallel_tasks=1,
            enabled=True
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)

        response = client.get(f"/api/v1/test-plans/{plan.id}")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["name"] == "DetailTestPlan"

    def test_get_test_plan_not_found(self, client: TestClient):
        """测试获取不存在的测试计划"""
        response = client.get("/api/v1/test-plans/99999")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0


class TestPlansUpdate:
    def test_update_test_plan_success(self, client: TestClient, db):
        """测试更新测试计划"""
        from app.models.test_plan import TestPlan
        plan = TestPlan(
            name="ToUpdate",
            description="Will be updated",
            execution_strategy="sequential",
            max_parallel_tasks=1,
            enabled=True
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)

        response = client.put(
            f"/api/v1/test-plans/{plan.id}",
            json={
                "name": "UpdatedPlan",
                "description": "Updated description",
                "execution_strategy": "parallel",
                "max_parallel_tasks": 2,
                "suites": []
            }
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["name"] == "UpdatedPlan"

    def test_update_test_plan_not_found(self, client: TestClient):
        """测试更新不存在的测试计划"""
        response = client.put(
            "/api/v1/test-plans/99999",
            json={
                "name": "test",
                "description": "test",
                "execution_strategy": "sequential",
                "max_parallel_tasks": 1,
                "suites": []
            }
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0


class TestPlansDelete:
    def test_delete_test_plan_success(self, client: TestClient, db):
        """测试删除测试计划"""
        from app.models.test_plan import TestPlan
        plan = TestPlan(
            name="ToDelete",
            description="Will be deleted",
            execution_strategy="sequential",
            max_parallel_tasks=1,
            enabled=True
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)

        response = client.delete(f"/api/v1/test-plans/{plan.id}")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0

    def test_delete_test_plan_not_found(self, client: TestClient):
        """测试删除不存在的测试计划"""
        response = client.delete("/api/v1/test-plans/99999")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0


class TestPlansToggle:
    def test_toggle_test_plan_success(self, client: TestClient, db):
        """测试切换测试计划启用状态"""
        from app.models.test_plan import TestPlan
        plan = TestPlan(
            name="TogglePlan",
            description="Toggle test",
            execution_strategy="sequential",
            max_parallel_tasks=1,
            enabled=True
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)

        response = client.patch(
            f"/api/v1/test-plans/{plan.id}/toggle",
            json={"enabled": False}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["enabled"] is False


class TestPlansSuites:
    def test_add_suites_to_plan(self, client: TestClient, db):
        """测试向测试计划添加套件"""
        from app.models.test_plan import TestPlan
        from app.models.suite import Suite
        plan = TestPlan(
            name="AddSuitesPlan",
            description="Add suites test",
            execution_strategy="sequential",
            max_parallel_tasks=1,
            enabled=True
        )
        suite = Suite(name="TestSuite", description="Test", enabled=True)
        db.add_all([plan, suite])
        db.commit()
        db.refresh(plan)
        db.refresh(suite)

        response = client.post(
            f"/api/v1/test-plans/{plan.id}/suites",
            json={"suite_ids": [suite.id]}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0

    def test_remove_suites_from_plan(self, client: TestClient, db):
        """测试从测试计划移除套件"""
        from app.models.test_plan import TestPlan
        from app.models.suite import Suite
        from app.models.test_plan import TestPlanSuite
        plan = TestPlan(
            name="RemoveSuitesPlan",
            description="Remove suites test",
            execution_strategy="sequential",
            max_parallel_tasks=1,
            enabled=True
        )
        suite = Suite(name="TestSuite", description="Test", enabled=True)
        db.add_all([plan, suite])
        db.flush()
        plan_suite = TestPlanSuite(
            test_plan_id=plan.id,
            suite_id=suite.id,
            order_index=1
        )
        db.add(plan_suite)
        db.commit()
        db.refresh(plan)

        response = client.delete(
            f"/api/v1/test-plans/{plan.id}/suites",
            json={"suite_ids": [suite.id]}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
