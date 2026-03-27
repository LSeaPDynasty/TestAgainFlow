"""
Base Actions - 基础操作
包括：click, long_press, input, swipe, back等基础UI操作
"""
import logging
from typing import Dict, Any
from .base import BaseAction
from .registry import register_action
from ..task import TaskResult

logger = logging.getLogger(__name__)


@register_action
class ClickAction(BaseAction):
    """点击操作"""
    action_type = "click"
    description = "点击UI元素"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        element_id = step_data.get('element_id')
        if not element_id:
            self.log_error("Click action requires element_id")
            return TaskResult.FAILED

        await self.driver.click_element(element_id)
        self.log_info(f"Clicked element: {element_id}")
        return TaskResult.PASSED


@register_action
class LongPressAction(BaseAction):
    """长按操作"""
    action_type = "long_press"
    description = "长按UI元素"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        element_id = step_data.get('element_id')
        duration = step_data.get('duration', 1000)  # 默认1秒

        if not element_id:
            self.log_error("LongPress action requires element_id")
            return TaskResult.FAILED

        await self.driver.long_press(element_id, duration)
        self.log_info(f"Long pressed element: {element_id} for {duration}ms")
        return TaskResult.PASSED


@register_action
class InputAction(BaseAction):
    """输入操作"""
    action_type = "input"
    description = "向输入框输入文本"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        element_id = step_data.get('element_id')
        text = step_data.get('text', '')
        clear_first = step_data.get('clear_first', False)

        if not element_id:
            self.log_error("Input action requires element_id")
            return TaskResult.FAILED

        # 替换变量
        text = self.replace_variables(text)

        if clear_first:
            await self.driver.clear_element(element_id)

        await self.driver.input_text(element_id, text)
        self.log_info(f"Input text into element: {element_id}")
        return TaskResult.PASSED


@register_action
class SwipeAction(BaseAction):
    """滑动操作"""
    action_type = "swipe"
    description = "屏幕滑动"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        direction = step_data.get('direction', 'up')
        distance = step_data.get('distance', 500)
        duration = step_data.get('duration', 500)

        await self.driver.swipe(direction, distance, duration)
        self.log_info(f"Swiped {direction} for {distance}px")
        return TaskResult.PASSED


@register_action
class BackAction(BaseAction):
    """返回操作"""
    action_type = "back"
    description = "按下返回键"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        await self.driver.press_back()
        self.log_info("Pressed back key")
        return TaskResult.PASSED


@register_action
class HomeAction(BaseAction):
    """主页操作"""
    action_type = "home"
    description = "按下主页键"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        await self.driver.press_home()
        self.log_info("Pressed home key")
        return TaskResult.PASSED


@register_action
class RecentAction(BaseAction):
    """最近任务操作"""
    action_type = "recent"
    description = "按下最近任务键"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        await self.driver.press_recent()
        self.log_info("Pressed recent key")
        return TaskResult.PASSED


@register_action
class ClearTextAction(BaseAction):
    """清除文本操作"""
    action_type = "clear_text"
    description = "清除输入框文本"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        element_id = step_data.get('element_id')
        if not element_id:
            self.log_error("ClearText action requires element_id")
            return TaskResult.FAILED

        await self.driver.clear_element(element_id)
        self.log_info(f"Cleared text in element: {element_id}")
        return TaskResult.PASSED
