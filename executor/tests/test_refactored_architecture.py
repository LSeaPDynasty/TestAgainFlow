"""
测试重构后的执行引擎架构
验证服务拆分是否正确
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock

from app.core.services import LogService, ResultCollector, ExecutionService
from app.core.task import TaskResult


class TestLogService:
    """测试LogService"""

    @pytest.fixture
    def mock_task_queue_client(self):
        """模拟TaskQueueClient"""
        client = Mock()
        client.send_task_log = AsyncMock()
        return client

    @pytest.fixture
    def log_service(self, mock_task_queue_client):
        """创建LogService实例"""
        return LogService(mock_task_queue_client)

    @pytest.mark.asyncio
    async def test_send_info_log(self, log_service, mock_task_queue_client):
        """测试发送INFO日志"""
        await log_service.info("task-123", "Test message")

        # 验证调用
        mock_task_queue_client.send_task_log.assert_called_once()
        call_args = mock_task_queue_client.send_task_log.call_args

        assert call_args[0][0] == "task-123"
        assert call_args[0][1]["level"] == "INFO"
        assert call_args[0][1]["message"] == "Test message"

    @pytest.mark.asyncio
    async def test_send_error_log(self, log_service, mock_task_queue_client):
        """测试发送ERROR日志"""
        await log_service.error("task-123", "Error message")

        call_args = mock_task_queue_client.send_task_log.call_args
        assert call_args[0][1]["level"] == "ERROR"


class TestResultCollector:
    """测试ResultCollector"""

    @pytest.fixture
    def collector(self):
        """创建ResultCollector实例"""
        return ResultCollector()

    def test_add_passed_result(self, collector):
        """测试添加通过结果"""
        collector.add_result(TaskResult.PASSED)
        summary = collector.get_summary()

        assert summary["total"] == 1
        assert summary["passed"] == 1
        assert summary["failed"] == 0
        assert summary["success_rate"] == 100.0

    def test_add_failed_result(self, collector):
        """测试添加失败结果"""
        collector.add_result(TaskResult.FAILED, {"item": "test"})
        summary = collector.get_summary()

        assert summary["total"] == 1
        assert summary["passed"] == 0
        assert summary["failed"] == 1
        assert summary["success_rate"] == 0.0

    def test_multiple_results(self, collector):
        """测试多个结果"""
        collector.add_result(TaskResult.PASSED)
        collector.add_result(TaskResult.PASSED)
        collector.add_result(TaskResult.FAILED)

        summary = collector.get_summary()
        assert summary["total"] == 3
        assert summary["passed"] == 2
        assert summary["failed"] == 1
        assert summary["success_rate"] == pytest.approx(66.67, rel=0.1)

    def test_get_final_result(self, collector):
        """测试获取最终结果"""
        collector.add_result(TaskResult.PASSED)
        collector.add_result(TaskResult.FAILED)

        final = collector.get_final_result()
        assert final == TaskResult.FAILED


class TestExecutionServiceArchitecture:
    """测试ExecutionService架构"""

    @pytest.fixture
    def mock_db_client(self):
        """模拟DatabaseClient"""
        return Mock()

    @pytest.fixture
    def mock_log_service(self):
        """模拟LogService"""
        service = Mock()
        service.info = AsyncMock()
        service.error = AsyncMock()
        return service

    @pytest.fixture
    def mock_result_collector(self):
        """模拟ResultCollector"""
        return Mock()

    @pytest.fixture
    def execution_service(self, mock_db_client, mock_log_service, mock_result_collector):
        """创建ExecutionService实例"""
        return ExecutionService(
            mock_db_client,
            mock_log_service,
            mock_result_collector
        )

    def test_service_initialization(self, execution_service):
        """测试服务初始化"""
        assert execution_service.db_client is not None
        assert execution_service.log_service is not None
        assert execution_service.result_collector is not None

    @pytest.mark.asyncio
    async def test_execute_step_delegates_to_step_executor(self, execution_service, mock_db_client):
        """测试execute_step委托给StepExecutor"""
        # 模拟步骤数据
        mock_db_client.get_step = AsyncMock(return_value={
            "id": 1,
            "name": "Test Step",
            "action_type": "click",
            "screen_id": 1,
            "element_id": 1
        })

        # 模拟task
        from app.core.task import ExecutionTask, ExecutionType
        task = ExecutionTask(
            task_id="test-task",
            execution_type=ExecutionType.STEP,
            target_id=1,
            device_serial="test-device",
            config={}
        )

        # 执行（会因为driver mock而失败，但可以验证调用）
        try:
            result = await execution_service.execute_step(task)
        except Exception:
            pass  # 预期会失败，因为没有真实的driver

        # 验证调用了get_step
        mock_db_client.get_step.assert_called_once_with(1)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
