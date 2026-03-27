"""
示例：如何添加新的自定义操作

有了工厂模式，添加新操作变得非常简单：
1. 创建新的Action类
2. 使用@register_action装饰器
3. 定义action_type和实现execute方法
4. 无需修改任何其他文件！
"""

from .base import BaseAction
from .registry import register_action
from ..task import TaskResult
from typing import Dict, Any

@register_action
class CustomAction(BaseAction):
    """
    自定义操作示例

    这个类演示了如何创建一个新的操作：
    1. 继承BaseAction
    2. 使用@register_action装饰器自动注册
    3. 定义action_type作为操作标识
    4. 实现execute方法
    """

    # 操作类型标识（必须唯一）
    action_type = "custom_action"

    # 操作描述
    description = "自定义操作示例"

    # 配置schema（可选，用于前端生成表单）
    config_schema = {
        "type": "object",
        "properties": {
            "param1": {"type": "string", "description": "参数1"},
            "param2": {"type": "number", "description": "参数2"}
        }
    }

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        """
        执行自定义操作

        Args:
            step_data: 包含操作参数的字典

        Returns:
            TaskResult: 执行结果
        """
        # 获取参数
        param1 = step_data.get('param1', '')
        param2 = step_data.get('param2', 0)

        # 使用self.driver访问设备驱动
        # 使用self.task记录日志
        # 使用self.variables访问变量系统

        self.log_info(f"执行自定义操作: param1={param1}, param2={param2}")

        # 实现你的操作逻辑
        # ...

        return TaskResult.PASSED


# 就这么简单！现在"custom_action"操作已经自动注册
# 可以在任何地方使用，无需修改StepExecutor或其他文件
