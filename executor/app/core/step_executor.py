"""
Step Executor (Refactored) - 使用工厂模式的步骤执行器
通过ActionRegistry自动发现和执行操作，无需手动维护if-elif链
"""
import logging
from typing import Dict, Any
from .task import ExecutionTask, TaskResult
from ..drivers.base import DeviceDriver
from .actions.registry import registry

logger = logging.getLogger(__name__)


class StepExecutor:
    """
    步骤执行器 - 使用工厂模式

    主要改进：
    1. 自动注册操作：添加新操作无需修改此类
    2. 统一接口：所有操作通过ActionRegistry调用
    3. 易扩展：新增操作只需创建新的Action类

    使用示例：
        executor = StepExecutor(driver, task)
        result = await executor.execute()
    """

    def __init__(self, driver: DeviceDriver, task: ExecutionTask):
        self.driver = driver
        self.task = task
        self.failure_screenshots = []  # 收集失败截图
        self.variables: Dict[str, Any] = {}  # 变量存储

        # 确保所有操作都已注册
        self._ensure_actions_registered()

    def _ensure_actions_registered(self):
        """
        确保所有操作模块都已导入并注册
        这会触发所有操作模块中的@register_action装饰器
        """
        try:
            # 导入所有操作模块，触发自动注册
            from .actions import base_actions
            from .actions import wait_actions
            from .actions import assert_actions
            from .actions import variable_actions
            from .actions import adb_actions
            from .actions import system_actions
            from .actions import appium_actions

            logger.debug(f"Registered actions: {registry.list_actions()}")
        except ImportError as e:
            logger.warning(f"Some action modules failed to import: {e}")

    async def execute(self) -> TaskResult:
        """执行步骤"""
        step_data = self.task.config.get('step_data', {})
        return await self.execute_with_data(step_data)

    async def execute_with_data(self, step_data: Dict[str, Any]) -> TaskResult:
        """
        执行步骤

        Args:
            step_data: 步骤配置数据

        Returns:
            TaskResult: 执行结果
        """
        action_type = step_data.get('action_type')
        step_name = step_data.get('name', 'Unnamed Step')

        self.task.log(f"   {step_name} ({action_type})")

        # 检查取消状态
        if self.task.is_cancelled():
            self.task.log(f"   Skipped: Task cancelled")
            return TaskResult.SKIPPED

        if not action_type:
            self.task.log(f"   ERROR: No action_type specified")
            return TaskResult.FAILED

        try:
            # 通过工厂创建操作实例
            action = registry.create(action_type, self.driver, self.task)

            if action is None:
                self.task.log(f"   ERROR: Unknown action type: {action_type}")
                self.task.log(f"   Available actions: {registry.list_actions()}")
                return TaskResult.FAILED

            # 执行操作
            result = await action.execute(step_data)

            return result

        except Exception as e:
            error_msg = f"Step execution error: {str(e)}"
            self.task.log(f"   ERROR: {error_msg}")
            logger.error(error_msg, exc_info=True)

            # 失败时截图
            await self._take_failure_screenshot(step_name)

            return TaskResult.FAILED

    async def _take_failure_screenshot(self, step_name: str):
        """失败时截图"""
        try:
            screenshot_data = await self.driver.get_screenshot()
            self.failure_screenshots.append({
                'step': step_name,
                'data': screenshot_data
            })
        except Exception as e:
            logger.warning(f"Failed to take screenshot: {e}")

    def get_failure_screenshots(self):
        """获取失败截图列表"""
        return self.failure_screenshots

    def list_available_actions(self):
        """列出所有可用的操作类型"""
        return registry.list_actions()

    def get_action_info(self, action_type: str):
        """获取操作的详细信息"""
        return registry.get_action_info(action_type)
