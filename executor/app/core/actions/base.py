"""
Base Action - 所有操作的基类
定义操作接口和通用功能
"""
import logging
import re
from abc import ABC, abstractmethod
from typing import Dict, Any
from ..task import ExecutionTask, TaskResult
from ...drivers.base import DeviceDriver

logger = logging.getLogger(__name__)


class BaseAction(ABC):
    """
    操作基类

    所有具体操作必须继承此类并实现execute方法

    使用示例：
        class ClickAction(BaseAction):
            action_type = "click"
            description = "点击元素"

            async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
                element_id = step_data.get('element_id')
                await self.driver.click_element(element_id)
                return TaskResult.PASSED
    """

    # 子类必须定义这些类属性
    action_type: str = None  # 操作类型标识
    description: str = ""    # 操作描述
    config_schema: Dict[str, Any] = {}  # 配置schema（可选）

    def __init__(self, driver: DeviceDriver, task: ExecutionTask):
        """
        初始化操作

        Args:
            driver: 设备驱动
            task: 执行任务
        """
        self.driver = driver
        self.task = task
        self.variables: Dict[str, Any] = getattr(task, 'variables', {})

    @abstractmethod
    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        """
        执行操作 - 子类必须实现

        Args:
            step_data: 步骤配置数据

        Returns:
            TaskResult: 执行结果
        """
        pass

    def replace_variables(self, text: str) -> str:
        """
        替换文本中的变量引用

        支持格式：{{var_name}}, ${var_name}, ${var_name:default}
        """
        if not text or not isinstance(text, str):
            return text

        # 替换 {{var}} 格式
        def replace_braces(match):
            var_name = match.group(1)
            if ':' in var_name:
                var_name, default = var_name.split(':', 1)
                return str(self.variables.get(var_name.strip(), default.strip()))
            return str(self.variables.get(var_name.strip(), match.group(0)))

        text = re.sub(r'\{\{([^}]+)\}\}', replace_braces, text)

        # 替换 ${var} 格式
        def replace_dollar(match):
            var_name = match.group(1)
            if ':' in var_name:
                var_name, default = var_name.split(':', 1)
                return str(self.variables.get(var_name.strip(), default.strip()))
            return str(self.variables.get(var_name.strip(), match.group(0)))

        text = re.sub(r'\$\{([^}]+)\}', replace_dollar, text)

        return text

    def set_variable(self, name: str, value: Any):
        """设置变量"""
        if hasattr(self.task, 'variables'):
            self.task.variables[name] = value
            self.variables[name] = value

    def get_variable(self, name: str, default: Any = None) -> Any:
        """获取变量"""
        return self.variables.get(name, default)

    async def take_failure_screenshot(self, step_name: str):
        """失败时截图（如果需要）"""
        try:
            if hasattr(self.task, 'failure_screenshots'):
                screenshot_data = await self.driver.get_screenshot()
                self.task.failure_screenshots.append({
                    'step': step_name,
                    'data': screenshot_data
                })
        except Exception as e:
            logger.warning(f"Failed to take screenshot: {e}")

    def log_info(self, message: str):
        """记录信息日志"""
        if hasattr(self.task, 'log'):
            self.task.log(message)

    def log_error(self, message: str):
        """记录错误日志"""
        if hasattr(self.task, 'log'):
            self.task.log(f"ERROR: {message}")
