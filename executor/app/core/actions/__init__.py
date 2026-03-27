"""
Actions Package - 工厂模式的测试操作
使用注册器模式，添加新操作无需修改核心代码
"""
from .base import BaseAction
from .registry import ActionRegistry, registry

# 导入所有操作模块，触发自动注册
from . import base_actions
from . import wait_actions
from . import assert_actions
from . import variable_actions
from . import adb_actions
from . import system_actions
from . import appium_actions

# 导出主要的类
__all__ = ['BaseAction', 'ActionRegistry', 'registry']
