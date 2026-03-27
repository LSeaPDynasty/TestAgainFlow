"""
Appium Actions - Appium操作
包括：get_text, get_attribute, get_location等Appium相关操作
"""
import logging
from typing import Dict, Any
from .base import BaseAction
from .registry import register_action
from ..task import TaskResult

logger = logging.getLogger(__name__)


@register_action
class GetTextAction(BaseAction):
    """获取元素文本"""
    action_type = "get_text"
    description = "获取UI元素文本内容"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        element_id = step_data.get('element_id')
        var_name = step_data.get('variable_name', '')

        if not element_id:
            self.log_error("GetText action requires element_id")
            return TaskResult.FAILED

        try:
            text = await self.driver.get_element_text(element_id)
            self.log_info(f"Element text: {text}")

            # 可选：保存到变量
            if var_name:
                self.set_variable(var_name, text)

            return TaskResult.PASSED
        except Exception as e:
            self.log_error(f"GetText error: {e}")
            return TaskResult.FAILED


@register_action
class GetAttributeAction(BaseAction):
    """获取元素属性"""
    action_type = "get_attribute"
    description = "获取UI元素属性值"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        element_id = step_data.get('element_id')
        attribute = step_data.get('attribute', 'text')
        var_name = step_data.get('variable_name', '')

        if not element_id:
            self.log_error("GetAttribute action requires element_id")
            return TaskResult.FAILED

        try:
            value = await self.driver.get_element_attribute(element_id, attribute)
            self.log_info(f"Element attribute '{attribute}': {value}")

            # 可选：保存到变量
            if var_name:
                self.set_variable(var_name, value)

            return TaskResult.PASSED
        except Exception as e:
            self.log_error(f"GetAttribute error: {e}")
            return TaskResult.FAILED


@register_action
class GetLocationAction(BaseAction):
    """获取元素位置"""
    action_type = "get_location"
    description = "获取UI元素位置坐标"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        element_id = step_data.get('element_id')
        var_name = step_data.get('variable_name', '')

        if not element_id:
            self.log_error("GetLocation action requires element_id")
            return TaskResult.FAILED

        try:
            location = await self.driver.get_element_location(element_id)
            self.log_info(f"Element location: {location}")

            # 可选：保存到变量
            if var_name:
                self.set_variable(var_name, str(location))

            return TaskResult.PASSED
        except Exception as e:
            self.log_error(f"GetLocation error: {e}")
            return TaskResult.FAILED


@register_action
class GetSizeAction(BaseAction):
    """获取元素大小"""
    action_type = "get_size"
    description = "获取UI元素尺寸"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        element_id = step_data.get('element_id')
        var_name = step_data.get('variable_name', '')

        if not element_id:
            self.log_error("GetSize action requires element_id")
            return TaskResult.FAILED

        try:
            size = await self.driver.get_element_size(element_id)
            self.log_info(f"Element size: {size}")

            # 可选：保存到变量
            if var_name:
                self.set_variable(var_name, str(size))

            return TaskResult.PASSED
        except Exception as e:
            self.log_error(f"GetSize error: {e}")
            return TaskResult.FAILED


@register_action
class IsDisplayedAction(BaseAction):
    """检查元素是否显示"""
    action_type = "is_displayed"
    description = "检查UI元素是否显示"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        element_id = step_data.get('element_id')
        var_name = step_data.get('variable_name', '')

        if not element_id:
            self.log_error("IsDisplayed action requires element_id")
            return TaskResult.FAILED

        try:
            displayed = await self.driver.is_element_displayed(element_id)
            self.log_info(f"Element displayed: {displayed}")

            # 可选：保存到变量
            if var_name:
                self.set_variable(var_name, str(displayed))

            return TaskResult.PASSED
        except Exception as e:
            self.log_error(f"IsDisplayed error: {e}")
            return TaskResult.FAILED


@register_action
class IsEnabledAction(BaseAction):
    """检查元素是否启用"""
    action_type = "is_enabled"
    description = "检查UI元素是否启用"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        element_id = step_data.get('element_id')
        var_name = step_data.get('variable_name', '')

        if not element_id:
            self.log_error("IsEnabled action requires element_id")
            return TaskResult.FAILED

        try:
            enabled = await self.driver.is_element_enabled(element_id)
            self.log_info(f"Element enabled: {enabled}")

            # 可选：保存到变量
            if var_name:
                self.set_variable(var_name, str(enabled))

            return TaskResult.PASSED
        except Exception as e:
            self.log_error(f"IsEnabled error: {e}")
            return TaskResult.FAILED


@register_action
class IsSelectedAction(BaseAction):
    """检查元素是否选中"""
    action_type = "is_selected"
    description = "检查UI元素是否选中"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        element_id = step_data.get('element_id')
        var_name = step_data.get('variable_name', '')

        if not element_id:
            self.log_error("IsSelected action requires element_id")
            return TaskResult.FAILED

        try:
            selected = await self.driver.is_element_selected(element_id)
            self.log_info(f"Element selected: {selected}")

            # 可选：保存到变量
            if var_name:
                self.set_variable(var_name, str(selected))

            return TaskResult.PASSED
        except Exception as e:
            self.log_error(f"IsSelected error: {e}")
            return TaskResult.FAILED


@register_action
class ScrollToAction(BaseAction):
    """滚动到元素"""
    action_type = "scroll_to"
    description = "滚动到指定UI元素"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        element_id = step_data.get('element_id')

        if not element_id:
            self.log_error("ScrollTo action requires element_id")
            return TaskResult.FAILED

        try:
            await self.driver.scroll_to_element(element_id)
            self.log_info(f"Scrolled to element: {element_id}")
            return TaskResult.PASSED
        except Exception as e:
            self.log_error(f"ScrollTo error: {e}")
            await self.take_failure_screenshot("scroll_to")
            return TaskResult.FAILED
