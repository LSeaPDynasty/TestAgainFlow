"""
Action Registry - 操作注册器
使用工厂模式管理所有操作，实现自动注册和调用
"""
import logging
from typing import Dict, Type, Optional, List
from .base import BaseAction

logger = logging.getLogger(__name__)


class ActionRegistry:
    """
    操作注册器 - 单例模式

    功能：
    1. 自动注册操作类
    2. 根据action_type查找操作
    3. 创建操作实例
    4. 列出所有可用操作

    使用示例：
        registry = ActionRegistry()

        # 注册操作
        registry.register(ClickAction)

        # 获取操作
        action_class = registry.get("click")
        action = action_class(driver, task)
        result = await action.execute(step_data)
    """

    _instance: Optional['ActionRegistry'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._actions: Dict[str, Type[BaseAction]] = {}
        return cls._instance

    def register(self, action_class: Type[BaseAction]):
        """
        注册操作类

        Args:
            action_class: 继承自BaseAction的操作类
        """
        if not action_class.action_type:
            raise ValueError(f"Action class {action_class.__name__} must define action_type")

        if action_class.action_type in self._actions:
            logger.warning(f"Action '{action_class.action_type}' already registered, replacing with {action_class.__name__}")

        self._actions[action_class.action_type] = action_class
        logger.debug(f"Registered action: {action_class.action_type} -> {action_class.__name__}")

        return action_class  # 支持装饰器语法

    def get(self, action_type: str) -> Optional[Type[BaseAction]]:
        """
        获取操作类

        Args:
            action_type: 操作类型标识

        Returns:
            操作类，如果不存在返回None
        """
        return self._actions.get(action_type)

    def create(self, action_type: str, driver, task) -> Optional[BaseAction]:
        """
        创建操作实例

        Args:
            action_type: 操作类型标识
            driver: 设备驱动
            task: 执行任务

        Returns:
            操作实例，如果不存在返回None
        """
        action_class = self.get(action_type)
        if action_class:
            return action_class(driver, task)
        return None

    def list_actions(self) -> List[str]:
        """列出所有已注册的操作类型"""
        return list(self._actions.keys())

    def get_action_info(self, action_type: str) -> Optional[Dict]:
        """
        获取操作信息

        Args:
            action_type: 操作类型标识

        Returns:
            操作信息字典，包含description和config_schema
        """
        action_class = self.get(action_type)
        if action_class:
            return {
                'action_type': action_class.action_type,
                'description': action_class.description,
                'config_schema': getattr(action_class, 'config_schema', {})
            }
        return None

    def list_all_info(self) -> Dict[str, Dict]:
        """列出所有操作的详细信息"""
        return {
            action_type: self.get_action_info(action_type)
            for action_type in self.list_actions()
        }

    def clear(self):
        """清空所有注册（主要用于测试）"""
        self._actions.clear()


# 全局注册器实例
registry = ActionRegistry()


def register_action(action_class: Type[BaseAction]) -> Type[BaseAction]:
    """
    装饰器：注册操作类

    使用示例：
        @register_action
        class ClickAction(BaseAction):
            action_type = "click"
            ...
    """
    return registry.register(action_class)
