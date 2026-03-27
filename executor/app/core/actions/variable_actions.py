"""
Variable Actions - 变量操作
包括：extract_text, extract_attribute, set_variable, get_variable等变量相关操作
"""
import logging
from typing import Dict, Any
from .base import BaseAction
from .registry import register_action
from ..task import TaskResult

logger = logging.getLogger(__name__)


@register_action
class ExtractTextAction(BaseAction):
    """提取文本到变量"""
    action_type = "extract_text"
    description = "提取元素文本到变量"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        element_id = step_data.get('element_id')
        var_name = step_data.get('variable_name', '')

        if not element_id:
            self.log_error("ExtractText action requires element_id")
            return TaskResult.FAILED

        if not var_name:
            self.log_error("ExtractText action requires variable_name")
            return TaskResult.FAILED

        try:
            text = await self.driver.get_element_text(element_id)
            self.set_variable(var_name, text)
            self.log_info(f"Extracted text to variable '{var_name}': {text}")
            return TaskResult.PASSED
        except Exception as e:
            self.log_error(f"ExtractText error: {e}")
            return TaskResult.FAILED


@register_action
class ExtractAttributeAction(BaseAction):
    """提取属性到变量"""
    action_type = "extract_attribute"
    description = "提取元素属性到变量"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        element_id = step_data.get('element_id')
        var_name = step_data.get('variable_name', '')
        attribute = step_data.get('attribute', 'text')

        if not element_id:
            self.log_error("ExtractAttribute action requires element_id")
            return TaskResult.FAILED

        if not var_name:
            self.log_error("ExtractAttribute action requires variable_name")
            return TaskResult.FAILED

        try:
            value = await self.driver.get_element_attribute(element_id, attribute)
            self.set_variable(var_name, value)
            self.log_info(f"Extracted attribute '{attribute}' to variable '{var_name}': {value}")
            return TaskResult.PASSED
        except Exception as e:
            self.log_error(f"ExtractAttribute error: {e}")
            return TaskResult.FAILED


@register_action
class SetVariableAction(BaseAction):
    """设置变量"""
    action_type = "set_variable"
    description = "设置变量值"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        var_name = step_data.get('variable_name', '')
        value = step_data.get('value', '')

        if not var_name:
            self.log_error("SetVariable action requires variable_name")
            return TaskResult.FAILED

        # 替换变量
        value = self.replace_variables(value)

        self.set_variable(var_name, value)
        self.log_info(f"Set variable '{var_name}' = '{value}'")
        return TaskResult.PASSED


@register_action
class GetVariableAction(BaseAction):
    """获取变量"""
    action_type = "get_variable"
    description = "获取变量值（用于日志）"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        var_name = step_data.get('variable_name', '')

        if not var_name:
            self.log_error("GetVariable action requires variable_name")
            return TaskResult.FAILED

        value = self.get_variable(var_name)
        self.log_info(f"Variable '{var_name}' = '{value}'")
        return TaskResult.PASSED
