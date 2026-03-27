"""
Runs API 测试

测试覆盖：
- 执行启动
- 执行控制（停止、暂停）
- 日志流 (SSE)
- 执行状态查询
"""
import pytest
import json
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestRunsStart:
    """执行启动接口测试"""

    def test_start_testcase_run_success(
        self,
        client: TestClient,
        db: Session,
        testcase,
        device
    ):
        """TC-RN-001: 启动用例执行"""
        response = client.post(
            "/api/v1/runs",
            json={
                "type": "testcase",
                "target_ids": [testcase.id],
                "device_serial": device.serial,
                "profile_id": None
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
        assert "task_id" in data["data"]
        assert data["data"]["status"] in ["pending", "running"]

    def test_start_suite_run_success(
        self,
        client: TestClient,
        db: Session,
        flow
    ):
        """TC-RN-002: 启动套件执行"""
        from tests.factories import TestDataFactory
        suite = TestDataFactory.create_suite(
            db,
            name="TestSuite",
            testcase_ids=[]
        )
        device = TestDataFactory.create_device(db)

        response = client.post(
            "/api/v1/runs",
            json={
                "type": "suite",
                "target_ids": [suite.id],
                "device_serial": device.serial
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
        assert "task_id" in data["data"]

    def test_start_run_invalid_type(
        self,
        client: TestClient,
        db: Session,
        device
    ):
        """TC-RN-003: 不合法的执行类型"""
        response = client.post(
            "/api/v1/runs",
            json={
                "type": "invalid_type",
                "target_ids": [1],
                "device_serial": device.serial
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 4001
        assert "type" in data["message"].lower()

    def test_start_run_empty_targets(
        self,
        client: TestClient,
        db: Session,
        device
    ):
        """TC-RN-004: target_ids 为空"""
        response = client.post(
            "/api/v1/runs",
            json={
                "type": "testcase",
                "target_ids": [],
                "device_serial": device.serial
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 4001
        assert "target" in data["message"].lower()

    def test_start_run_nonexistent_testcase(
        self,
        client: TestClient,
        db: Session,
        device
    ):
        """TC-RN-005: 引用不存在的用例"""
        response = client.post(
            "/api/v1/runs",
            json={
                "type": "testcase",
                "target_ids": [999],
                "device_serial": device.serial
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 4004
        assert "testcase" in data["message"].lower()

    def test_start_run_device_not_found(
        self,
        client: TestClient,
        db: Session,
        testcase
    ):
        """TC-RN-006: 设备不存在"""
        response = client.post(
            "/api/v1/runs",
            json={
                "type": "testcase",
                "target_ids": [testcase.id],
                "device_serial": "nonexistent_device"
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 4004
        assert "device" in data["message"].lower()

    def test_start_run_with_profile(
        self,
        client: TestClient,
        db: Session,
        testcase,
        device,
        profile
    ):
        """TC-RN-007: 使用 Profile 启动执行"""
        response = client.post(
            "/api/v1/runs",
            json={
                "type": "testcase",
                "target_ids": [testcase.id],
                "device_serial": device.serial,
                "profile_id": profile.id
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
        assert "task_id" in data["data"]

    def test_start_run_profile_not_found(
        self,
        client: TestClient,
        db: Session,
        testcase,
        device
    ):
        """TC-RN-008: Profile 不存在"""
        response = client.post(
            "/api/v1/runs",
            json={
                "type": "testcase",
                "target_ids": [testcase.id],
                "device_serial": device.serial,
                "profile_id": 999
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 4004
        assert "profile" in data["message"].lower()

    def test_start_run_device_offline(
        self,
        client: TestClient,
        db: Session,
        testcase,
        device,
        monkeypatch
    ):
        """TC-RN-009: 设备离线"""
        # Mock 设备离线
        import app.utils.adb as adb_module
        monkeypatch.setattr(
            adb_module,
            "check_device_online",
            lambda serial: False
        )

        response = client.post(
            "/api/v1/runs",
            json={
                "type": "testcase",
                "target_ids": [testcase.id],
                "device_serial": device.serial
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 4001
        assert "offline" in data["message"].lower() or "not available" in data["message"].lower()

    def test_start_run_with_custom_params(
        self,
        client: TestClient,
        db: Session,
        testcase,
        device
    ):
        """TC-RN-010: 使用自定义参数启动"""
        response = client.post(
            "/api/v1/runs",
            json={
                "type": "testcase",
                "target_ids": [testcase.id],
                "device_serial": device.serial,
                "params": {
                    "username": "custom_user",
                    "timeout": 10000
                }
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
        assert "task_id" in data["data"]


class TestRunsControl:
    """执行控制接口测试"""

    def test_stop_run_success(
        self,
        client: TestClient,
        db: Session,
        testcase,
        device,
        monkeypatch
    ):
        """TC-RN-020: 停止执行"""
        # 首先启动执行
        start_response = client.post(
            "/api/v1/runs",
            json={
                "type": "testcase",
                "target_ids": [testcase.id],
                "device_serial": device.serial
            }
        )
        task_id = start_response.json()["data"]["task_id"]

        # 停止执行
        response = client.post(f"/api/v1/runs/{task_id}/stop")
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0

    def test_stop_run_not_found(
        self,
        client: TestClient
    ):
        """TC-RN-021: 停止不存在的执行"""
        response = client.post("/api/v1/runs/nonexistent_task/stop")
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 4004

    def test_pause_run_success(
        self,
        client: TestClient,
        db: Session,
        testcase,
        device,
        monkeypatch
    ):
        """TC-RN-022: 暂停执行"""
        # 启动执行
        start_response = client.post(
            "/api/v1/runs",
            json={
                "type": "testcase",
                "target_ids": [testcase.id],
                "device_serial": device.serial
            }
        )
        task_id = start_response.json()["data"]["task_id"]

        # 暂停执行
        response = client.post(f"/api/v1/runs/{task_id}/pause")
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0

    def test_resume_run_success(
        self,
        client: TestClient,
        db: Session,
        testcase,
        device,
        monkeypatch
    ):
        """TC-RN-023: 恢复执行"""
        # 启动执行
        start_response = client.post(
            "/api/v1/runs",
            json={
                "type": "testcase",
                "target_ids": [testcase.id],
                "device_serial": device.serial
            }
        )
        task_id = start_response.json()["data"]["task_id"]

        # 恢复执行
        response = client.post(f"/api/v1/runs/{task_id}/resume")
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0


class TestRunsStatus:
    """执行状态查询接口测试"""

    def test_get_run_status_success(
        self,
        client: TestClient,
        db: Session,
        testcase,
        device
    ):
        """TC-RN-030: 查询执行状态"""
        # 启动执行
        start_response = client.post(
            "/api/v1/runs",
            json={
                "type": "testcase",
                "target_ids": [testcase.id],
                "device_serial": device.serial
            }
        )
        task_id = start_response.json()["data"]["task_id"]

        # 查询状态
        response = client.get(f"/api/v1/runs/{task_id}/status")
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
        assert "status" in data["data"]
        assert "progress" in data["data"]

    def test_get_run_status_not_found(
        self,
        client: TestClient
    ):
        """TC-RN-031: 查询不存在的执行"""
        response = client.get("/api/v1/runs/nonexistent_task/status")
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 4004

    def test_list_running_runs(
        self,
        client: TestClient,
        db: Session
    ):
        """TC-RN-032: 列出正在运行的执行"""
        response = client.get("/api/v1/runs?status=running")
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
        assert "items" in data["data"]

    def test_list_runs_by_device(
        self,
        client: TestClient,
        db: Session,
        device
    ):
        """TC-RN-033: 按设备筛选执行记录"""
        response = client.get(f"/api/v1/runs?device_serial={device.serial}")
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
        assert "items" in data["data"]


class TestRunsLogs:
    """执行日志接口测试 (SSE)"""

    def test_get_run_logs(
        self,
        client: TestClient,
        db: Session,
        testcase,
        device
    ):
        """TC-RN-040: 获取执行日志流"""
        # 启动执行
        start_response = client.post(
            "/api/v1/runs",
            json={
                "type": "testcase",
                "target_ids": [testcase.id],
                "device_serial": device.serial
            }
        )
        task_id = start_response.json()["data"]["task_id"]

        # 获取日志流
        response = client.get(f"/api/v1/runs/{task_id}/logs")
        # SSE 返回 200 和特定的 content-type
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")

    def test_get_run_logs_not_found(
        self,
        client: TestClient
    ):
        """TC-RN-041: 获取不存在执行的日志"""
        response = client.get("/api/v1/runs/nonexistent_task/logs")
        assert response.status_code == 200

        # 应该返回错误或空流
        assert response.status_code == 200


class TestRunsResults:
    """执行结果接口测试"""

    def test_get_run_results(
        self,
        client: TestClient,
        db: Session,
        testcase,
        device
    ):
        """TC-RN-050: 获取执行结果"""
        # 启动执行
        start_response = client.post(
            "/api/v1/runs",
            json={
                "type": "testcase",
                "target_ids": [testcase.id],
                "device_serial": device.serial
            }
        )
        task_id = start_response.json()["data"]["task_id"]

        # 获取结果
        response = client.get(f"/api/v1/runs/{task_id}/results")
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
        assert "testcases" in data["data"]
        assert "summary" in data["data"]

    def test_get_run_results_not_found(
        self,
        client: TestClient
    ):
        """TC-RN-051: 获取不存在执行的结果"""
        response = client.get("/api/v1/runs/nonexistent_task/results")
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 4004


class TestRunsBatch:
    """批量执行接口测试"""

    def test_start_batch_run(
        self,
        client: TestClient,
        db: Session,
        testcase,
        device
    ):
        """TC-RN-060: 批量启动多个用例"""
        from tests.factories import TestDataFactory
        testcase2 = TestDataFactory.create_testcase(
            db,
            name="Test2",
            main_flows=[]
        )

        response = client.post(
            "/api/v1/runs/batch",
            json={
                "type": "testcase",
                "target_ids": [testcase.id, testcase2.id],
                "device_serial": device.serial,
                "mode": "parallel"
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
        assert "task_ids" in data["data"]
        assert len(data["data"]["task_ids"]) == 2

    def test_start_batch_run_sequential_mode(
        self,
        client: TestClient,
        db: Session,
        testcase,
        device
    ):
        """TC-RN-061: 批量执行 - 串行模式"""
        response = client.post(
            "/api/v1/runs/batch",
            json={
                "type": "testcase",
                "target_ids": [testcase.id],
                "device_serial": device.serial,
                "mode": "sequential"
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 0
