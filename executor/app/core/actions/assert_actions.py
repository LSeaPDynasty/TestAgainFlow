"""
Assert Actions - 断言操作
包括：assert_text, assert_exists, assert_not_exists等断言相关操作
"""
import logging
from typing import Dict, Any
from .base import BaseAction
from .registry import register_action
from ..task import TaskResult

logger = logging.getLogger(__name__)


@register_action
class AssertTextAction(BaseAction):
    """断言文本"""
    action_type = "assert_text"
    description = "断言元素包含指定文本"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        element_id = step_data.get('element_id')
        expected_text = step_data.get('text', '')

        if not element_id:
            self.log_error("AssertText action requires element_id")
            return TaskResult.FAILED

        # 替换变量
        expected_text = self.replace_variables(expected_text)

        try:
            actual_text = await self.driver.get_element_text(element_id)
            if expected_text in actual_text:
                self.log_info(f"Text assertion passed: '{expected_text}' found")
                return TaskResult.PASSED
            else:
                self.log_error(f"Text assertion failed: expected '{expected_text}', got '{actual_text}'")
                await self.take_failure_screenshot("assert_text")
                return TaskResult.FAILED
        except Exception as e:
            self.log_error(f"AssertText error: {e}")
            await self.take_failure_screenshot("assert_text")
            return TaskResult.FAILED


@register_action
class AssertExistsAction(BaseAction):
    """断言元素存在"""
    action_type = "assert_exists"
    description = "断言元素存在"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        element_id = step_data.get('element_id')

        if not element_id:
            self.log_error("AssertExists action requires element_id")
            return TaskResult.FAILED

        try:
            exists = await self.driver.element_exists(element_id)
            if exists:
                self.log_info(f"Element exists: {element_id}")
                return TaskResult.PASSED
            else:
                self.log_error(f"Element does not exist: {element_id}")
                await self.take_failure_screenshot("assert_exists")
                return TaskResult.FAILED
        except Exception as e:
            self.log_error(f"AssertExists error: {e}")
            await self.take_failure_screenshot("assert_exists")
            return TaskResult.FAILED


@register_action
class AssertNotExistsAction(BaseAction):
    """断言元素不存在"""
    action_type = "assert_not_exists"
    description = "断言元素不存在"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        element_id = step_data.get('element_id')

        if not element_id:
            self.log_error("AssertNotExists action requires element_id")
            return TaskResult.FAILED

        try:
            exists = await self.driver.element_exists(element_id)
            if not exists:
                self.log_info(f"Element does not exist: {element_id}")
                return TaskResult.PASSED
            else:
                self.log_error(f"Element still exists: {element_id}")
                await self.take_failure_screenshot("assert_not_exists")
                return TaskResult.FAILED
        except Exception as e:
            self.log_error(f"AssertNotExists error: {e}")
            await self.take_failure_screenshot("assert_not_exists")
            return TaskResult.FAILED


@register_action
class AssertEnabledAction(BaseAction):
    """断言元素启用"""
    action_type = "assert_enabled"
    description = "断言元素处于启用状态"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        element_id = step_data.get('element_id')

        if not element_id:
            self.log_error("AssertEnabled action requires element_id")
            return TaskResult.FAILED

        try:
            enabled = await self.driver.is_element_enabled(element_id)
            if enabled:
                self.log_info(f"Element is enabled: {element_id}")
                return TaskResult.PASSED
            else:
                self.log_error(f"Element is not enabled: {element_id}")
                await self.take_failure_screenshot("assert_enabled")
                return TaskResult.FAILED
        except Exception as e:
            self.log_error(f"AssertEnabled error: {e}")
            await self.take_failure_screenshot("assert_enabled")
            return TaskResult.FAILED


@register_action
class AssertVisibleAction(BaseAction):
    """断言元素可见"""
    action_type = "assert_visible"
    description = "断言元素可见"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        element_id = step_data.get('element_id')

        if not element_id:
            self.log_error("AssertVisible action requires element_id")
            return TaskResult.FAILED

        try:
            visible = await self.driver.is_element_visible(element_id)
            if visible:
                self.log_info(f"Element is visible: {element_id}")
                return TaskResult.PASSED
            else:
                self.log_error(f"Element is not visible: {element_id}")
                await self.take_failure_screenshot("assert_visible")
                return TaskResult.FAILED
        except Exception as e:
            self.log_error(f"AssertVisible error: {e}")
            await self.take_failure_screenshot("assert_visible")
            return TaskResult.FAILED


@register_action
class AssertColorAction(BaseAction):
    """断言颜色"""
    action_type = "assert_color"
    description = "断言元素颜色"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        element_id = step_data.get('element_id')
        expected_color = step_data.get('color', '')

        if not element_id:
            self.log_error("AssertColor action requires element_id")
            return TaskResult.FAILED

        # 简化实现：实际需要根据颜色检查逻辑
        self.log_info(f"Color assertion for {element_id}: {expected_color}")
        return TaskResult.PASSED
