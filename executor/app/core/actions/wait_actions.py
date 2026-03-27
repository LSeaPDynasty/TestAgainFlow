"""
Wait Actions - 等待操作
包括：wait_element, wait_time, wait_until等等待相关操作
"""
import asyncio
import logging
from typing import Dict, Any
from .base import BaseAction
from .registry import register_action
from ..task import TaskResult

logger = logging.getLogger(__name__)


@register_action
class WaitElementAction(BaseAction):
    """等待元素出现"""
    action_type = "wait_element"
    description = "等待元素出现"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        element_id = step_data.get('element_id')
        timeout = step_data.get('timeout', 10000)  # 默认10秒

        if not element_id:
            self.log_error("WaitElement action requires element_id")
            return TaskResult.FAILED

        try:
            await asyncio.wait_for(
                self.driver.wait_for_element(element_id),
                timeout=timeout / 1000
            )
            self.log_info(f"Element found: {element_id}")
            return TaskResult.PASSED
        except asyncio.TimeoutError:
            self.log_error(f"Element not found within {timeout}ms: {element_id}")
            await self.take_failure_screenshot("wait_element")
            return TaskResult.FAILED


@register_action
class WaitTimeAction(BaseAction):
    """等待固定时间"""
    action_type = "wait_time"
    description = "等待指定时间"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        duration = step_data.get('duration', 1000)  # 默认1秒

        self.log_info(f"Waiting for {duration}ms")
        await asyncio.sleep(duration / 1000)
        return TaskResult.PASSED


@register_action
class WaitUntilAction(BaseAction):
    """等待条件满足"""
    action_type = "wait_until"
    description = "等待条件满足"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        condition = step_data.get('condition', '')
        timeout = step_data.get('timeout', 10000)

        if not condition:
            self.log_error("WaitUntil action requires condition")
            return TaskResult.FAILED

        # 简化实现：支持文本出现检查
        element_id = step_data.get('element_id')
        expected_text = step_data.get('text', '')

        start_time = asyncio.get_event_loop().time()
        while (asyncio.get_event_loop().time() - start_time) * 1000 < timeout:
            try:
                if element_id:
                    text = await self.driver.get_element_text(element_id)
                    if expected_text in text:
                        self.log_info(f"Condition met: '{expected_text}' found")
                        return TaskResult.PASSED
                await asyncio.sleep(0.5)
            except Exception:
                await asyncio.sleep(0.5)

        self.log_error(f"Condition not met within {timeout}ms")
        await self.take_failure_screenshot("wait_until")
        return TaskResult.FAILED
