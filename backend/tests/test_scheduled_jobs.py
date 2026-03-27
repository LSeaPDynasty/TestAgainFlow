"""Tests for scheduled jobs APIs."""
from fastapi.testclient import TestClient


class TestScheduledJobsList:
    def test_list_scheduled_jobs_empty(self, client: TestClient):
        """测试获取空的定时任务列表"""
        response = client.get("/api/v1/scheduled-jobs")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["total"] == 0
        assert body["data"]["items"] == []

    def test_list_scheduled_jobs_pagination(self, client: TestClient, db):
        """测试定时任务列表分页"""
        from app.models.scheduled_job import ScheduledJob
        from app.models.suite import Suite
        suite = Suite(name="TestSuite", description="Test", enabled=True)
        db.add(suite)
        db.flush()

        for i in range(5):
            job = ScheduledJob(
                name=f"Job_{i}",
                description=f"Test job {i}",
                job_type="suite",
                target_id=suite.id,
                cron_expression="0 0 * * *",
                enabled=True
            )
            db.add(job)
        db.commit()

        response = client.get("/api/v1/scheduled-jobs?page=1&page_size=3")
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["total"] == 5
        assert len(body["data"]["items"]) == 3

    def test_list_scheduled_jobs_enabled_only(self, client: TestClient, db):
        """测试只获取启用的定时任务"""
        from app.models.scheduled_job import ScheduledJob
        from app.models.testcase import Testcase
        testcase = Testcase(name="TestTC", description="Test", priority="P1", timeout=120)
        db.add(testcase)
        db.flush()

        job1 = ScheduledJob(
            name="EnabledJob",
            description="Enabled",
            job_type="testcase",
            target_id=testcase.id,
            cron_expression="0 0 * * *",
            enabled=True
        )
        job2 = ScheduledJob(
            name="DisabledJob",
            description="Disabled",
            job_type="testcase",
            target_id=testcase.id,
            cron_expression="0 1 * * *",
            enabled=False
        )
        db.add_all([job1, job2])
        db.commit()

        response = client.get("/api/v1/scheduled-jobs?enabled_only=true")
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["total"] == 1
        assert body["data"]["items"][0]["enabled"] is True


class TestScheduledJobsCreate:
    def test_create_scheduled_job_success(self, client: TestClient, testcase):
        """测试成功创建定时任务"""
        response = client.post(
            "/api/v1/scheduled-jobs",
            json={
                "name": "DailyTestJob",
                "description": "Daily test job",
                "job_type": "testcase",
                "target_id": testcase.id,
                "cron_expression": "0 0 * * *",
                "enabled": True
            }
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["name"] == "DailyTestJob"

    def test_create_scheduled_job_empty_name(self, client: TestClient):
        """测试创建空名称的定时任务"""
        response = client.post(
            "/api/v1/scheduled-jobs",
            json={
                "name": "",
                "description": "Test",
                "job_type": "testcase",
                "target_id": 1,
                "cron_expression": "0 0 * * *",
                "enabled": True
            }
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0
        assert "cannot be empty" in body["message"]

    def test_create_scheduled_job_invalid_cron(self, client: TestClient, testcase):
        """测试创建无效cron表达式的定时任务"""
        response = client.post(
            "/api/v1/scheduled-jobs",
            json={
                "name": "InvalidCronJob",
                "description": "Test",
                "job_type": "testcase",
                "target_id": testcase.id,
                "cron_expression": "invalid-cron",
                "enabled": True
            }
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0
        assert "Invalid cron expression" in body["message"]

    def test_create_scheduled_job_not_found_target(self, client: TestClient):
        """测试创建不存在目标的定时任务"""
        response = client.post(
            "/api/v1/scheduled-jobs",
            json={
                "name": "NotFoundJob",
                "description": "Test",
                "job_type": "testcase",
                "target_id": 99999,
                "cron_expression": "0 0 * * *",
                "enabled": True
            }
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0
        assert "not found" in body["message"]


class TestScheduledJobsGet:
    def test_get_scheduled_job_success(self, client: TestClient, db):
        """测试获取单个定时任务"""
        from app.models.scheduled_job import ScheduledJob
        from app.models.testcase import Testcase
        testcase = Testcase(name="TestTC", description="Test", priority="P1", timeout=120)
        db.add(testcase)
        db.flush()

        job = ScheduledJob(
            name="GetJob",
            description="Get test",
            job_type="testcase",
            target_id=testcase.id,
            cron_expression="0 0 * * *",
            enabled=True
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        response = client.get(f"/api/v1/scheduled-jobs/{job.id}")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["name"] == "GetJob"

    def test_get_scheduled_job_not_found(self, client: TestClient):
        """测试获取不存在的定时任务"""
        response = client.get("/api/v1/scheduled-jobs/99999")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0


class TestScheduledJobsUpdate:
    def test_update_scheduled_job_success(self, client: TestClient, db):
        """测试更新定时任务"""
        from app.models.scheduled_job import ScheduledJob
        from app.models.testcase import Testcase
        testcase = Testcase(name="TestTC", description="Test", priority="P1", timeout=120)
        db.add(testcase)
        db.flush()

        job = ScheduledJob(
            name="ToUpdate",
            description="Update test",
            job_type="testcase",
            target_id=testcase.id,
            cron_expression="0 0 * * *",
            enabled=True
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        response = client.put(
            f"/api/v1/scheduled-jobs/{job.id}",
            json={
                "name": "UpdatedJob",
                "description": "Updated description",
                "cron_expression": "0 1 * * *"
            }
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["name"] == "UpdatedJob"


class TestScheduledJobsDelete:
    def test_delete_scheduled_job_success(self, client: TestClient, db):
        """测试删除定时任务"""
        from app.models.scheduled_job import ScheduledJob
        from app.models.testcase import Testcase
        testcase = Testcase(name="TestTC", description="Test", priority="P1", timeout=120)
        db.add(testcase)
        db.flush()

        job = ScheduledJob(
            name="ToDelete",
            description="Delete test",
            job_type="testcase",
            target_id=testcase.id,
            cron_expression="0 0 * * *",
            enabled=True
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        response = client.delete(f"/api/v1/scheduled-jobs/{job.id}")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0


class TestScheduledJobsToggle:
    def test_toggle_scheduled_job_success(self, client: TestClient, db):
        """测试切换定时任务启用状态"""
        from app.models.scheduled_job import ScheduledJob
        from app.models.testcase import Testcase
        testcase = Testcase(name="TestTC", description="Test", priority="P1", timeout=120)
        db.add(testcase)
        db.flush()

        job = ScheduledJob(
            name="ToggleJob",
            description="Toggle test",
            job_type="testcase",
            target_id=testcase.id,
            cron_expression="0 0 * * *",
            enabled=True
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        response = client.post(f"/api/v1/scheduled-jobs/{job.id}/toggle")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["enabled"] is False


class TestScheduledJobsRun:
    def test_run_scheduled_job_success(self, client: TestClient, db):
        """测试手动运行定时任务"""
        from app.models.scheduled_job import ScheduledJob
        from app.models.testcase import Testcase
        testcase = Testcase(name="TestTC", description="Test", priority="P1", timeout=120)
        db.add(testcase)
        db.flush()

        job = ScheduledJob(
            name="RunJob",
            description="Run test",
            job_type="testcase",
            target_id=testcase.id,
            cron_expression="0 0 * * *",
            enabled=True
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        response = client.post(
            f"/api/v1/scheduled-jobs/{job.id}/run",
            json={"device_serial": "test-serial"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert "task_id" in body["data"]
