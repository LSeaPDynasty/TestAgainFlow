"""
Execution Service - 测试执行服务
提取核心执行逻辑，使executor.py专注于调度
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional

from ...services.db_client import DatabaseClient
from .log_service import LogService
from .result_collector import ResultCollector
from ...drivers import create_driver
from ..task import ExecutionTask, TaskResult, ExecutionType
from ..step_executor import StepExecutor

logger = logging.getLogger(__name__)


class ExecutionService:
    """
    测试执行服务 - 负责实际的测试执行逻辑

    职责：
    - 执行Step、Flow、Testcase、Suite
    - 管理Driver生命周期
    - 协调LogService和ResultCollector
    """

    def __init__(
        self,
        db_client: DatabaseClient,
        log_service: LogService,
        result_collector: ResultCollector
    ):
        self.db_client = db_client
        self.log_service = log_service
        self.result_collector = result_collector

    async def execute_step(self, task: ExecutionTask) -> TaskResult:
        """执行单个步骤"""
        try:
            # 获取步骤数据
            step_data = await self.db_client.get_step(task.target_id)
            if not step_data:
                await self.log_service.error(task.task_id, f"步骤不存在: {task.target_id}")
                return TaskResult.FAILED

            await self.log_service.info(task.task_id, f"执行步骤: {step_data.get('name', 'Unknown')}")

            # 创建driver和executor
            driver = self._create_driver(task)
            step_executor = StepExecutor(driver, task)

            # 执行步骤
            result = await step_executor.execute_with_data(step_data)

            # 清理driver
            await self._cleanup_driver(driver)

            return result

        except Exception as e:
            logger.error(f"Step execution error: {e}", exc_info=True)
            await self.log_service.error(task.task_id, f"步骤执行异常: {str(e)}")
            return TaskResult.FAILED

    async def execute_flow(self, task: ExecutionTask) -> TaskResult:
        """执行流程"""
        try:
            # 获取流程数据
            flow_data = await self.db_client.get_flow(task.target_id)
            if not flow_data:
                await self.log_service.error(task.task_id, f"流程不存在: {task.target_id}")
                return TaskResult.FAILED

            await self.log_service.info(task.task_id, f"执行流程: {flow_data.get('name', 'Unknown')}")

            # 获取流程步骤
            flow_steps = flow_data.get("steps", [])
            if not flow_steps:
                await self.log_service.warning(task.task_id, "流程没有步骤")
                return TaskResult.SKIPPED

            # 执行流程中的每个步骤
            for idx, step_data in enumerate(flow_steps, 1):
                await self.log_service.info(task.task_id, f"步骤 {idx}/{len(flow_steps)}: {step_data.get('name')}")

                step_task = ExecutionTask(
                    task_id=f"{task.task_id}_step_{idx}",
                    execution_type=ExecutionType.STEP,
                    target_id=step_data["id"],
                    device_serial=task.device_serial,
                    config=task.config
                )

                result = await self.execute_step(step_task)
                self.result_collector.add_result(result, {"step": step_data.get("name")})

                # 如果步骤失败且不允许继续，则中止
                if result == TaskResult.FAILED and not step_data.get("continue_on_error", False):
                    await self.log_service.error(task.task_id, f"步骤失败，中止流程")
                    return TaskResult.FAILED

            return TaskResult.PASSED

        except Exception as e:
            logger.error(f"Flow execution error: {e}", exc_info=True)
            await self.log_service.error(task.task_id, f"流程执行异常: {str(e)}")
            return TaskResult.FAILED

    async def execute_testcase_items(
        self,
        task: ExecutionTask,
        testcase_items: List[Dict[str, Any]]
    ) -> TaskResult:
        """执行testcase_items（支持flow/step混排）"""
        try:
            await self.log_service.info(
                task.task_id,
                f"Main阶段: {len(testcase_items)} 个items (flow/step混排)"
            )

            # ✅ 批量预加载所有步骤数据
            step_ids = [
                item.get("step_id")
                for item in testcase_items
                if item.get("item_type") == "step"
            ]
            steps_map = await self.db_client.get_steps_batch(step_ids) if step_ids else {}

            final_result = TaskResult.PASSED
            enabled_count = 0

            for idx, item in enumerate(testcase_items, 1):
                if not item.get("enabled", 1):
                    continue

                enabled_count += 1
                item_type = item.get("item_type")

                if item_type == "flow":
                    result = await self._execute_flow_item(task, item, enabled_count)
                elif item_type == "step":
                    result = await self._execute_step_item(task, item, enabled_count, steps_map)
                else:
                    await self.log_service.error(task.task_id, f"未知的item_type: {item_type}")
                    return TaskResult.FAILED

                self.result_collector.add_result(result, {"item": item})

                if result != TaskResult.PASSED:
                    if not item.get("continue_on_error", False):
                        final_result = TaskResult.FAILED
                        break

            return final_result

        except Exception as e:
            logger.error(f"Testcase items execution error: {e}", exc_info=True)
            await self.log_service.error(task.task_id, f"测试用例执行异常: {str(e)}")
            return TaskResult.FAILED

    async def _execute_flow_item(self, task: ExecutionTask, item: Dict, index: int) -> TaskResult:
        """执行flow类型的item"""
        flow_id = item.get("flow_id")
        flow_name = item.get("flow_name", f"Flow-{flow_id}")

        await self.log_service.info(task.task_id, f"Item {index}: Flow - {flow_name}")

        flow_task = ExecutionTask(
            task_id=f"{task.task_id}_item_{item.get('id')}",
            execution_type=ExecutionType.FLOW,
            target_id=flow_id,
            device_serial=task.device_serial,
            config=task.config
        )

        return await self.execute_flow(flow_task)

    async def _execute_step_item(
        self,
        task: ExecutionTask,
        item: Dict,
        index: int,
        steps_map: Dict[int, Dict]
    ) -> TaskResult:
        """执行step类型的item"""
        step_id = item.get("step_id")
        step_name = item.get("step_name", f"Step-{step_id}")
        step_action_type = item.get("step_action_type", "unknown")

        await self.log_service.info(task.task_id, f"Item {index}: Step - {step_name} ({step_action_type})")

        # 使用预加载的步骤数据
        step_data = steps_map.get(step_id)
        if not step_data:
            await self.log_service.error(task.task_id, f"步骤数据不存在: {step_id}")
            return TaskResult.FAILED

        # 创建driver和executor
        driver = self._create_driver(task)
        step_executor = StepExecutor(driver, task)

        # 执行步骤
        result = await step_executor.execute_with_data(step_data)

        # 清理driver
        await self._cleanup_driver(driver)

        return result

    def _create_driver(self, task: ExecutionTask):
        """创建设备driver"""
        device_config = task.config.get("device", {})
        return create_driver(task.device_serial, device_config)

    async def _cleanup_driver(self, driver):
        """清理driver资源"""
        try:
            if driver:
                await driver.cleanup()
        except Exception as e:
            logger.error(f"Driver cleanup error: {e}")
