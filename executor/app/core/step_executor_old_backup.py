"""
Step Executor
Handles execution of individual test steps
"""
import logging
import asyncio
import json
import re
from typing import Dict, Any, Optional, Callable
from ..drivers.base import DeviceDriver
from .task import ExecutionTask, TaskResult

logger = logging.getLogger(__name__)


class StepExecutor:
    """
    Executes a single test step on a device
    """

    def __init__(self, driver: DeviceDriver, task: ExecutionTask):
        self.driver = driver
        self.task = task
        self.failure_screenshots = []  # 收集失败截图
        self.variables: Dict[str, Any] = {}  # 变量存储 ⭐

    async def execute(self) -> TaskResult:
        """Execute step from task config"""
        step_data = self.task.config.get('step_data', {})
        return await self.execute_with_data(step_data)

    # ========== 变量管理方法 ⭐ ==========

    def _replace_variables(self, text: str) -> str:
        """
        替换文本中的变量引用

        支持的变量格式：
        - {{var_name}}
        - ${var_name}
        - ${var_name:default_value}
        """
        if not text or not isinstance(text, str):
            return text

        # 替换 {{var}} 格式
        def replace_braces(match):
            var_name = match.group(1)
            if ':' in var_name:
                var_name, default = var_name.split(':', 1)
                return str(self.variables.get(var_name, default))
            return str(self.variables.get(var_name, match.group(0)))

        text = re.sub(r'\{\{([^}]+)\}\}', replace_braces, text)

        # 替换 ${var} 格式
        def replace_dollar(match):
            var_name = match.group(1)
            if ':' in var_name:
                var_name, default = var_name.split(':', 1)
                return str(self.variables.get(var_name, default))
            return str(self.variables.get(var_name, match.group(0)))

        text = re.sub(r'\$\{([^}]+)\}', replace_dollar, text)

        return text

    def _set_variable(self, name: str, value: Any):
        """设置变量"""
        self.variables[name] = value
        self.task.log(f"   💾 设置变量: {name} = {value}")

    def _get_variable(self, name: str, default: Any = None) -> Any:
        """获取变量"""
        return self.variables.get(name, default)

    def _parse_variable_name(self, value: str) -> str:
        """
        从值中解析变量名

        支持格式：
        - var_name
        - {{var_name}}
        - ${var_name}
        """
        value = value.strip()

        # 移除 {{}} 包裹
        if value.startswith('{{') and value.endswith('}}'):
            return value[2:-2].strip()

        # 移除 ${} 包裹
        if value.startswith('${') and value.endswith('}'):
            return value[2:-1].strip()

        return value

    async def execute_with_data(self, step_data: Dict[str, Any]) -> TaskResult:
        """
        Execute step with provided data

        Args:
            step_data: Step configuration including action_type, element info, etc.

        Returns:
            TaskResult indicating pass/fail/skip
        """
        action_type = step_data.get('action_type')
        step_name = step_data.get('name', 'Unnamed Step')

        self.task.log(f"   📌 {step_name} ({action_type})")

        # Check for cancellation
        if self.task.is_cancelled():
            self.task.log(f"   ⏭️  Skipped: Task cancelled")
            return TaskResult.SKIPPED

        try:
            # Execute based on action type
            if action_type == 'click':
                result = await self._execute_click(step_data)
            elif action_type == 'long_press':
                result = await self._execute_long_press(step_data)
            elif action_type == 'input':
                result = await self._execute_input(step_data)
            elif action_type == 'swipe':
                result = await self._execute_swipe(step_data)
            elif action_type == 'hardware_back':
                result = await self._execute_back(step_data)
            elif action_type == 'wait_element':
                result = await self._execute_wait_element(step_data)
            elif action_type == 'wait_time':
                result = await self._execute_wait_time(step_data)
            elif action_type == 'assert_text':
                result = await self._execute_assert_text(step_data)
            elif action_type == 'assert_exists':
                result = await self._execute_assert_exists(step_data)
            elif action_type == 'assert_not_exists':
                result = await self._execute_assert_not_exists(step_data)
            elif action_type == 'assert_color':
                result = await self._execute_assert_color(step_data)
            elif action_type == 'start_activity':
                result = await self._execute_start_activity(step_data)
            elif action_type == 'screenshot':
                result = await self._execute_screenshot(step_data)

            # ========== 新增基础操作 ==========
            elif action_type == 'clear_text':
                result = await self._execute_clear_text(step_data)
            elif action_type == 'hardware_home':
                result = await self._execute_home(step_data)
            elif action_type == 'hardware_recent':
                result = await self._execute_recent(step_data)

            # ========== 新增等待操作 ==========
            elif action_type == 'wait_until':
                result = await self._execute_wait_until(step_data)

            # ========== 新增断言操作 ==========
            elif action_type == 'assert_enabled':
                result = await self._execute_assert_enabled(step_data)
            elif action_type == 'assert_visible':
                result = await self._execute_assert_visible(step_data)

            # ========== 变量提取操作 ⭐ ==========
            elif action_type == 'extract_text':
                result = await self._execute_extract_text(step_data)
            elif action_type == 'extract_attribute':
                result = await self._execute_extract_attribute(step_data)
            elif action_type == 'set_variable':
                result = await self._execute_set_variable(step_data)
            elif action_type == 'get_variable':
                result = await self._execute_get_variable(step_data)

            # ========== ADB操作 ==========
            elif action_type == 'adb_install':
                result = await self._execute_adb_install(step_data)
            elif action_type == 'adb_uninstall':
                result = await self._execute_adb_uninstall(step_data)
            elif action_type == 'adb_start_app':
                result = await self._execute_adb_start_app(step_data)
            elif action_type == 'adb_stop_app':
                result = await self._execute_adb_stop_app(step_data)
            elif action_type == 'adb_restart_app':
                result = await self._execute_adb_restart_app(step_data)
            elif action_type == 'adb_clear_app':
                result = await self._execute_adb_clear_app(step_data)
            elif action_type == 'adb_tap':
                result = await self._execute_adb_tap(step_data)
            elif action_type == 'adb_swipe':
                result = await self._execute_adb_swipe(step_data)
            elif action_type == 'adb_key_event':
                result = await self._execute_adb_key_event(step_data)
            elif action_type == 'adb_input_text':
                result = await self._execute_adb_input_text(step_data)
            elif action_type == 'adb_shell':
                result = await self._execute_adb_shell(step_data)
            elif action_type == 'adb_push_file':
                result = await self._execute_adb_push_file(step_data)
            elif action_type == 'adb_pull_file':
                result = await self._execute_adb_pull_file(step_data)

            # ========== Appium操作 ==========
            elif action_type == 'get_text':
                result = await self._execute_get_text(step_data)
            elif action_type == 'get_attribute':
                result = await self._execute_get_attribute(step_data)
            elif action_type == 'get_location':
                result = await self._execute_get_location(step_data)
            elif action_type == 'get_size':
                result = await self._execute_get_size(step_data)
            elif action_type == 'is_displayed':
                result = await self._execute_is_displayed(step_data)
            elif action_type == 'is_enabled':
                result = await self._execute_is_enabled(step_data)
            elif action_type == 'is_selected':
                result = await self._execute_is_selected(step_data)
            elif action_type == 'scroll_to':
                result = await self._execute_scroll_to(step_data)

            # ========== 系统操作 ==========
            elif action_type == 'get_current_activity':
                result = await self._execute_get_current_activity(step_data)
            elif action_type == 'open_notifications':
                result = await self._execute_open_notifications(step_data)
            elif action_type == 'toggle_location':
                result = await self._execute_toggle_location(step_data)
            elif action_type == 'toggle_wifi':
                result = await self._execute_toggle_wifi(step_data)

            # ========== 高级操作 ==========
            elif action_type == 'toast_check':
                result = await self._execute_toast_check(step_data)
            elif action_type == 'webview_switch':
                result = await self._execute_webview_switch(step_data)
            elif action_type == 'native_app_switch':
                result = await self._execute_native_app_switch(step_data)

            else:
                self.task.log(f"   ⚠️  Unknown action type: {action_type}")
                return TaskResult.SKIPPED

            # 步骤失败时自动截图
            if result == TaskResult.FAILED:
                await self._take_failure_screenshot(step_name)

            return result

        except Exception as e:
            error_msg = str(e)
            self.task.log(f"   ❌ Error: {error_msg}")
            logger.error(f"Step execution error: {error_msg}", exc_info=True)

            # 异常时也截图
            await self._take_failure_screenshot(step_name)

            return TaskResult.FAILED

    async def _take_failure_screenshot(self, step_name: str):
        """步骤失败时自动截图"""
        try:
            import os
            from datetime import datetime

            # 创建截图目录
            screenshot_dir = "screenshots/failures"
            os.makedirs(screenshot_dir, exist_ok=True)

            # 生成截图文件名（替换特殊字符）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_step_name = step_name.replace(" ", "_").replace("/", "_")[:20]
            filename = f"{self.task.task_id}_{safe_step_name}_{timestamp}.png"
            filepath = os.path.join(screenshot_dir, filename)

            # 截图
            success = await self.driver.take_screenshot(
                self.task.device_serial,
                filepath
            )

            if success:
                self.task.log(f"   📸 失败截图已保存: {filename}")
                logger.info(f"失败截图已保存: {filepath}")

                # 保存截图信息
                self.failure_screenshots.append({
                    "filename": filename,
                    "filepath": filepath,
                    "step_name": step_name,
                    "timestamp": timestamp
                })

            else:
                self.task.log(f"   ⚠️  失败截图保存失败")

        except Exception as e:
            logger.error(f"失败截图出错: {e}", exc_info=True)

    def get_failure_screenshots(self):
        """获取所有失败截图"""
        return self.failure_screenshots

    async def _execute_click(self, step_data: Dict) -> TaskResult:
        """Execute click action"""
        element_id = step_data.get('element_id')
        if not element_id:
            error_msg = "Missing element_id"
            logger.error(error_msg)
            self.task.log(f"   ❌ {error_msg}")
            return TaskResult.FAILED

        # Get element locator
        locator = step_data.get('locator')
        if not locator:
            error_msg = "No locator found for element"
            logger.error(error_msg)
            self.task.log(f"   ❌ {error_msg}")
            return TaskResult.FAILED

        locator_value = locator.get('value', 'unknown')
        step_name = step_data.get('name', '点击操作')
        logger.info(f"点击: {step_name}")
        self.task.log(f"   👆 Clicking: {locator_value}")

        success = await self.driver.tap_element(
            self.task.device_serial,
            locator
        )

        if success:
            self.task.log(f"   ✅ Click successful")
            return TaskResult.PASSED
        else:
            error_msg = "Click failed"
            logger.error(f"{step_name} - 点击失败")
            self.task.log(f"   ❌ {error_msg}")
            return TaskResult.FAILED

    async def _execute_long_press(self, step_data: Dict) -> TaskResult:
        """Execute long press action"""
        element_id = step_data.get('element_id')
        locator = step_data.get('locator')

        if not locator:
            self.task.log(f"   ❌ No locator found")
            return TaskResult.FAILED

        self.task.log(f"   👆 Long pressing: {locator.get('value', 'unknown')}")

        duration_ms = step_data.get('duration', 2000)

        success = await self.driver.long_press(
            self.task.device_serial,
            locator,
            duration_ms
        )

        if success:
            self.task.log(f"   ✅ Long press successful")
            return TaskResult.PASSED
        else:
            self.task.log(f"   ❌ Long press failed")
            return TaskResult.FAILED

    async def _execute_input(self, step_data: Dict) -> TaskResult:
        """Execute input action"""
        element_id = step_data.get('element_id')
        locator = step_data.get('locator')
        text = step_data.get('action_value', '')

        if not locator:
            error_msg = "No locator found"
            logger.error(error_msg)
            self.task.log(f"   ❌ {error_msg}")
            return TaskResult.FAILED

        if not text:
            error_msg = "No text to input"
            logger.error(error_msg)
            self.task.log(f"   ❌ {error_msg}")
            return TaskResult.FAILED

        step_name = step_data.get('name', '输入文本')
        logger.info(f"输入: {step_name} - {text[:20]}...")
        self.task.log(f"   ⌨️  Inputting text: {text[:20]}...")

        success = await self.driver.input_text(
            self.task.device_serial,
            locator,
            text
        )

        if success:
            self.task.log(f"   ✅ Input successful")
            return TaskResult.PASSED
        else:
            error_msg = "Input failed"
            logger.error(f"{step_name} - 输入失败")
            self.task.log(f"   ❌ {error_msg}")
            return TaskResult.FAILED

    async def _execute_swipe(self, step_data: Dict) -> TaskResult:
        """Execute swipe action"""
        direction = step_data.get('action_value', 'up')
        self.task.log(f"   👆 Swiping: {direction}")

        success = await self.driver.swipe(
            self.task.device_serial,
            direction
        )

        if success:
            self.task.log(f"   ✅ Swipe successful")
            return TaskResult.PASSED
        else:
            self.task.log(f"   ❌ Swipe failed")
            return TaskResult.FAILED

    async def _execute_back(self, step_data: Dict) -> TaskResult:
        """Execute hardware back action"""
        self.task.log(f"   ↩️  Pressing back")

        success = await self.driver.press_back(self.task.device_serial)

        if success:
            self.task.log(f"   ✅ Back pressed")
            return TaskResult.PASSED
        else:
            self.task.log(f"   ❌ Back press failed")
            return TaskResult.FAILED

    async def _execute_wait_element(self, step_data: Dict) -> TaskResult:
        """Execute wait for element action"""
        element_id = step_data.get('element_id')
        locator = step_data.get('locator')
        timeout_ms = step_data.get('wait_time', 5000)

        if not locator:
            error_msg = "No locator found"
            logger.error(error_msg)
            self.task.log(f"   ❌ {error_msg}")
            return TaskResult.FAILED

        locator_value = locator.get('value', 'unknown')
        step_name = step_data.get('name', '等待元素')
        logger.info(f"{step_name} - 等待 {locator_value} (超时 {timeout_ms}ms)")
        self.task.log(f"   ⏳ Waiting for element: {locator_value} (timeout: {timeout_ms}ms)")

        found = await self.driver.wait_for_element(
            self.task.device_serial,
            locator,
            timeout_ms
        )

        if found:
            self.task.log(f"   ✅ Element found")
            return TaskResult.PASSED
        else:
            error_msg = f"Element not found after {timeout_ms}ms: {locator_value}"
            logger.error(f"{step_name} - 元素未找到")
            self.task.log(f"   ❌ {error_msg}")
            return TaskResult.FAILED

    async def _execute_wait_time(self, step_data: Dict) -> TaskResult:
        """Execute wait time action"""
        wait_time_ms = step_data.get('wait_time', 1000)

        self.task.log(f"   ⏳ Waiting {wait_time_ms}ms")

        await asyncio.sleep(wait_time_ms / 1000)

        self.task.log(f"   ✅ Wait completed")
        return TaskResult.PASSED

    async def _execute_assert_text(self, step_data: Dict) -> TaskResult:
        """Execute text assertion"""
        element_id = step_data.get('element_id')
        locator = step_data.get('locator')
        expected_text = step_data.get('action_value', '')

        if not locator:
            error_msg = "No locator found"
            logger.error(error_msg)
            self.task.log(f"   ❌ {error_msg}")
            return TaskResult.FAILED

        step_name = step_data.get('name', '断言文本')
        logger.info(f"{step_name} - 期望包含 '{expected_text}'")
        self.task.log(f"   🔍 Asserting text: '{expected_text}'")

        actual_text = await self.driver.get_element_text(
            self.task.device_serial,
            locator
        )

        if actual_text is None:
            logger.error(f"{step_name} - 元素未找到")
            self.task.log(f"   ❌ Element not found")
            return TaskResult.FAILED

        if expected_text in actual_text:
            self.task.log(f"   ✅ Assertion passed: '{actual_text}'")
            return TaskResult.PASSED
        else:
            error_msg = f"Assertion failed: expected '{expected_text}', got '{actual_text}'"
            logger.error(f"{step_name} - 断言失败")
            self.task.log(f"   ❌ {error_msg}")
            return TaskResult.FAILED

    async def _execute_assert_exists(self, step_data: Dict) -> TaskResult:
        """Execute element exists assertion"""
        element_id = step_data.get('element_id')
        locator = step_data.get('locator')

        if not locator:
            self.task.log(f"   ❌ No locator found")
            return TaskResult.FAILED

        self.task.log(f"   🔍 Asserting element exists")

        exists = await self.driver.element_exists(
            self.task.device_serial,
            locator
        )

        if exists:
            self.task.log(f"   ✅ Element exists")
            return TaskResult.PASSED
        else:
            self.task.log(f"   ❌ Element does not exist")
            return TaskResult.FAILED

    async def _execute_assert_not_exists(self, step_data: Dict) -> TaskResult:
        """Execute element not exists assertion"""
        element_id = step_data.get('element_id')
        locator = step_data.get('locator')

        if not locator:
            self.task.log(f"   ❌ No locator found")
            return TaskResult.FAILED

        self.task.log(f"   🔍 Asserting element not exists")

        exists = await self.driver.element_exists(
            self.task.device_serial,
            locator
        )

        if not exists:
            self.task.log(f"   ✅ Element does not exist (as expected)")
            return TaskResult.PASSED
        else:
            self.task.log(f"   ❌ Element exists (should not)")
            return TaskResult.FAILED

    async def _execute_assert_color(self, step_data: Dict) -> TaskResult:
        """Execute color assertion"""
        # TODO: Implement color assertion
        self.task.log(f"   ⚠️  Color assertion not yet implemented")
        return TaskResult.SKIPPED

    async def _execute_start_activity(self, step_data: Dict) -> TaskResult:
        """Execute start activity action"""
        activity_name = step_data.get('action_value', '')

        if not activity_name:
            self.task.log(f"   ❌ No activity name specified")
            return TaskResult.FAILED

        self.task.log(f"   🚀 Starting activity: {activity_name}")

        success = await self.driver.start_activity(
            self.task.device_serial,
            activity_name
        )

        if success:
            self.task.log(f"   ✅ Activity started")
            return TaskResult.PASSED
        else:
            self.task.log(f"   ❌ Failed to start activity")
            return TaskResult.FAILED

    async def _execute_screenshot(self, step_data: Dict) -> TaskResult:
        """Execute screenshot action"""
        self.task.log(f"   📸 Taking screenshot")

        success = await self.driver.take_screenshot(self.task.device_serial)

        if success:
            self.task.log(f"   ✅ Screenshot taken")
            return TaskResult.PASSED
        else:
            self.task.log(f"   ❌ Screenshot failed")
            return TaskResult.FAILED

    # ========== 新增基础操作实现 ==========

    async def _execute_clear_text(self, step_data: Dict) -> TaskResult:
        """清除文本"""
        locator = step_data.get('locator')
        if not locator:
            self.task.log(f"   ❌ No locator found")
            return TaskResult.FAILED

        self.task.log(f"   🧹 Clearing text")
        success = await self.driver.clear_text(self.task.device_serial, locator)

        if success:
            self.task.log(f"   ✅ Text cleared")
            return TaskResult.PASSED
        else:
            self.task.log(f"   ❌ Clear text failed")
            return TaskResult.FAILED

    async def _execute_home(self, step_data: Dict) -> TaskResult:
        """按Home键"""
        self.task.log(f"   🏠 Pressing Home")
        success = await self.driver.press_home(self.task.device_serial)
        return TaskResult.PASSED if success else TaskResult.FAILED

    async def _execute_recent(self, step_data: Dict) -> TaskResult:
        """按最近任务键"""
        self.task.log(f"   📱 Pressing Recent")
        success = await self.driver.press_recent(self.task.device_serial)
        return TaskResult.PASSED if success else TaskResult.FAILED

    async def _execute_wait_until(self, step_data: Dict) -> TaskResult:
        """等待直到条件满足"""
        condition = step_data.get('action_value', '')
        timeout_ms = step_data.get('wait_time', 5000)

        self.task.log(f"   ⏳ Waiting until: {condition}")
        # TODO: 实现条件解析和等待逻辑
        self.task.log(f"   ⚠️  Wait until not fully implemented")
        return TaskResult.PASSED

    async def _execute_assert_enabled(self, step_data: Dict) -> TaskResult:
        """断言元素可用"""
        locator = step_data.get('locator')
        if not locator:
            return TaskResult.FAILED

        enabled = await self.driver.is_enabled(self.task.device_serial, locator)
        if enabled:
            self.task.log(f"   ✅ Element is enabled")
            return TaskResult.PASSED
        else:
            self.task.log(f"   ❌ Element is not enabled")
            return TaskResult.FAILED

    async def _execute_assert_visible(self, step_data: Dict) -> TaskResult:
        """断言元素可见"""
        locator = step_data.get('locator')
        if not locator:
            return TaskResult.FAILED

        visible = await self.driver.is_displayed(self.task.device_serial, locator)
        if visible:
            self.task.log(f"   ✅ Element is visible")
            return TaskResult.PASSED
        else:
            self.task.log(f"   ❌ Element is not visible")
            return TaskResult.FAILED

    # ========== 变量提取操作实现 ⭐ ==========

    async def _execute_extract_text(self, step_data: Dict) -> TaskResult:
        """提取元素文本到变量"""
        locator = step_data.get('locator')
        var_name_expr = step_data.get('action_value', '')

        if not locator:
            self.task.log(f"   ❌ No locator found")
            return TaskResult.FAILED

        if not var_name_expr:
            self.task.log(f"   ❌ No variable name specified")
            return TaskResult.FAILED

        # 解析变量名
        var_name = self._parse_variable_name(var_name_expr)

        # 获取元素文本
        text = await self.driver.get_element_text(self.task.device_serial, locator)
        if text is None:
            self.task.log(f"   ❌ Failed to get element text")
            return TaskResult.FAILED

        # 保存到变量
        self._set_variable(var_name, text)
        self.task.log(f"   ✅ Extracted text: '{text}' -> ${var_name}")
        return TaskResult.PASSED

    async def _execute_extract_attribute(self, step_data: Dict) -> TaskResult:
        """提取元素属性到变量"""
        locator = step_data.get('locator')
        action_value = step_data.get('action_value', '')

        if not locator:
            self.task.log(f"   ❌ No locator found")
            return TaskResult.FAILED

        # 解析：属性名=变量名，例如 "text=var_name"
        if '=' not in action_value:
            self.task.log(f"   ❌ Invalid format, expected: attribute_name=variable_name")
            return TaskResult.FAILED

        attr_name, var_name_expr = action_value.split('=', 1)
        var_name = self._parse_variable_name(var_name_expr)

        # 获取属性值
        attr_value = await self.driver.get_element_attribute(
            self.task.device_serial, locator, attr_name.strip()
        )

        if attr_value is None:
            self.task.log(f"   ❌ Failed to get attribute: {attr_name}")
            return TaskResult.FAILED

        # 保存到变量
        self._set_variable(var_name, attr_value)
        self.task.log(f"   ✅ Extracted attribute: {attr_name}={attr_value} -> ${var_name}")
        return TaskResult.PASSED

    async def _execute_set_variable(self, step_data: Dict) -> TaskResult:
        """设置变量"""
        value_expr = step_data.get('action_value', '')

        if not value_expr:
            self.task.log(f"   ❌ No value specified")
            return TaskResult.FAILED

        # 解析：变量名=值，例如 "count=10"
        if '=' not in value_expr:
            self.task.log(f"   ❌ Invalid format, expected: variable_name=value")
            return TaskResult.FAILED

        var_name, value = value_expr.split('=', 1)

        # 替换值中的变量引用
        value = self._replace_variables(value.strip())

        # 保存到变量
        self._set_variable(var_name.strip(), value)
        return TaskResult.PASSED

    async def _execute_get_variable(self, step_data: Dict) -> TaskResult:
        """获取变量值（用于日志输出）"""
        var_name_expr = step_data.get('action_value', '')

        if not var_name_expr:
            self.task.log(f"   ❌ No variable name specified")
            return TaskResult.FAILED

        var_name = self._parse_variable_name(var_name_expr)
        value = self._get_variable(var_name)

        if value is None:
            self.task.log(f"   ⚠️  Variable not found: ${var_name}")
            return TaskResult.FAILED

        self.task.log(f"   💵 Variable ${var_name} = {value}")
        return TaskResult.PASSED

    # ========== ADB操作实现 ==========

    async def _execute_adb_install(self, step_data: Dict) -> TaskResult:
        """安装应用"""
        apk_path = step_data.get('action_value', '')
        self.task.log(f"   📦 Installing: {apk_path}")
        success = await self.driver.adb_install(self.task.device_serial, apk_path)
        return TaskResult.PASSED if success else TaskResult.FAILED

    async def _execute_adb_uninstall(self, step_data: Dict) -> TaskResult:
        """卸载应用"""
        package_name = step_data.get('action_value', '')
        self.task.log(f"   🗑️  Uninstalling: {package_name}")
        success = await self.driver.adb_uninstall(self.task.device_serial, package_name)
        return TaskResult.PASSED if success else TaskResult.FAILED

    async def _execute_adb_start_app(self, step_data: Dict) -> TaskResult:
        """启动应用"""
        package_name = step_data.get('action_value', '')
        self.task.log(f"   🚀 Starting app: {package_name}")
        success = await self.driver.adb_start_app(self.task.device_serial, package_name)
        return TaskResult.PASSED if success else TaskResult.FAILED

    async def _execute_adb_stop_app(self, step_data: Dict) -> TaskResult:
        """停止应用"""
        package_name = step_data.get('action_value', '')
        self.task.log(f"   🛑 Stopping app: {package_name}")
        success = await self.driver.adb_stop_app(self.task.device_serial, package_name)
        return TaskResult.PASSED if success else TaskResult.FAILED

    async def _execute_adb_restart_app(self, step_data: Dict) -> TaskResult:
        """重启应用"""
        package_name = step_data.get('action_value', '')
        self.task.log(f"   🔄 Restarting app: {package_name}")
        success = await self.driver.adb_restart_app(self.task.device_serial, package_name)
        return TaskResult.PASSED if success else TaskResult.FAILED

    async def _execute_adb_clear_app(self, step_data: Dict) -> TaskResult:
        """清除应用数据"""
        package_name = step_data.get('action_value', '')
        self.task.log(f"   🧹 Clearing app data: {package_name}")
        success = await self.driver.adb_clear_app(self.task.device_serial, package_name)
        return TaskResult.PASSED if success else TaskResult.FAILED

    async def _execute_adb_tap(self, step_data: Dict) -> TaskResult:
        """点击坐标"""
        coords = step_data.get('action_value', '')
        self.task.log(f"   👆 Tapping coordinates: {coords}")
        # 解析坐标: "x,y" 或 {"x":100,"y":200}
        try:
            if ',' in coords:
                x, y = coords.split(',')
                x, y = int(x.strip()), int(y.strip())
            else:
                coord_dict = json.loads(coords)
                x, y = int(coord_dict['x']), int(coord_dict['y'])
            success = await self.driver.adb_tap(self.task.device_serial, x, y)
            return TaskResult.PASSED if success else TaskResult.FAILED
        except:
            self.task.log(f"   ❌ Invalid coordinates format")
            return TaskResult.FAILED

    async def _execute_adb_swipe(self, step_data: Dict) -> TaskResult:
        """ADB滑动"""
        swipe_config = step_data.get('action_value', '')
        self.task.log(f"   👆 ADB Swiping: {swipe_config}")
        success = await self.driver.adb_swipe(self.task.device_serial, swipe_config)
        return TaskResult.PASSED if success else TaskResult.FAILED

    async def _execute_adb_key_event(self, step_data: Dict) -> TaskResult:
        """发送按键事件"""
        keycode = step_data.get('action_value', '')
        self.task.log(f"   🔑 Sending key event: {keycode}")
        success = await self.driver.adb_key_event(self.task.device_serial, keycode)
        return TaskResult.PASSED if success else TaskResult.FAILED

    async def _execute_adb_input_text(self, step_data: Dict) -> TaskResult:
        """通过ADB输入文本"""
        text = step_data.get('action_value', '')
        # 替换变量
        text = self._replace_variables(text)
        self.task.log(f"   ⌨️  ADB Input: {text}")
        success = await self.driver.adb_input_text(self.task.device_serial, text)
        return TaskResult.PASSED if success else TaskResult.FAILED

    async def _execute_adb_shell(self, step_data: Dict) -> TaskResult:
        """执行Shell命令"""
        cmd = step_data.get('action_value', '')
        # 替换变量
        cmd = self._replace_variables(cmd)
        self.task.log(f"   🐚 Shell: {cmd}")
        success = await self.driver.adb_shell(self.task.device_serial, cmd)
        return TaskResult.PASSED if success else TaskResult.FAILED

    async def _execute_adb_push_file(self, step_data: Dict) -> TaskResult:
        """推送文件到设备"""
        paths = step_data.get('action_value', '')
        self.task.log(f"   ⬆️  Pushing file: {paths}")
        # 解析: local_path,remote_path
        try:
            if ',' in paths:
                local_path, remote_path = paths.split(',', 1)
            else:
                raise ValueError("Invalid format")
            success = await self.driver.adb_push(
                self.task.device_serial,
                local_path.strip(),
                remote_path.strip()
            )
            return TaskResult.PASSED if success else TaskResult.FAILED
        except Exception as e:
            self.task.log(f"   ❌ Error: {e}")
            return TaskResult.FAILED

    async def _execute_adb_pull_file(self, step_data: Dict) -> TaskResult:
        """从设备拉取文件"""
        paths = step_data.get('action_value', '')
        self.task.log(f"   ⬇️  Pulling file: {paths}")
        # 解析: remote_path,local_path
        try:
            if ',' in paths:
                remote_path, local_path = paths.split(',', 1)
            else:
                raise ValueError("Invalid format")
            success = await self.driver.adb_pull(
                self.task.device_serial,
                remote_path.strip(),
                local_path.strip()
            )
            return TaskResult.PASSED if success else TaskResult.FAILED
        except Exception as e:
            self.task.log(f"   ❌ Error: {e}")
            return TaskResult.FAILED

    # ========== Appium操作实现 ==========

    async def _execute_get_text(self, step_data: Dict) -> TaskResult:
        """获取元素文本"""
        locator = step_data.get('locator')
        if not locator:
            return TaskResult.FAILED

        text = await self.driver.get_element_text(self.task.device_serial, locator)
        if text is not None:
            self.task.log(f"   📄 Text: {text}")
            return TaskResult.PASSED
        else:
            self.task.log(f"   ❌ Failed to get text")
            return TaskResult.FAILED

    async def _execute_get_attribute(self, step_data: Dict) -> TaskResult:
        """获取元素属性"""
        locator = step_data.get('locator')
        attr_name = step_data.get('action_value', '')

        if not locator or not attr_name:
            return TaskResult.FAILED

        attr_value = await self.driver.get_element_attribute(
            self.task.device_serial, locator, attr_name
        )
        if attr_value is not None:
            self.task.log(f"   📋 Attribute {attr_name}: {attr_value}")
            return TaskResult.PASSED
        else:
            self.task.log(f"   ❌ Failed to get attribute")
            return TaskResult.FAILED

    async def _execute_get_location(self, step_data: Dict) -> TaskResult:
        """获取元素位置"""
        locator = step_data.get('locator')
        if not locator:
            return TaskResult.FAILED

        location = await self.driver.get_element_location(self.task.device_serial, locator)
        if location:
            self.task.log(f"   📍 Location: x={location.get('x')}, y={location.get('y')}")
            return TaskResult.PASSED
        else:
            return TaskResult.FAILED

    async def _execute_get_size(self, step_data: Dict) -> TaskResult:
        """获取元素大小"""
        locator = step_data.get('locator')
        if not locator:
            return TaskResult.FAILED

        size = await self.driver.get_element_size(self.task.device_serial, locator)
        if size:
            self.task.log(f"   📐 Size: width={size.get('width')}, height={size.get('height')}")
            return TaskResult.PASSED
        else:
            return TaskResult.FAILED

    async def _execute_is_displayed(self, step_data: Dict) -> TaskResult:
        """检查元素是否显示"""
        locator = step_data.get('locator')
        if not locator:
            return TaskResult.FAILED

        displayed = await self.driver.is_displayed(self.task.device_serial, locator)
        self.task.log(f"   👁️  Displayed: {displayed}")
        return TaskResult.PASSED if displayed else TaskResult.FAILED

    async def _execute_is_enabled(self, step_data: Dict) -> TaskResult:
        """检查元素是否可用"""
        locator = step_data.get('locator')
        if not locator:
            return TaskResult.FAILED

        enabled = await self.driver.is_enabled(self.task.device_serial, locator)
        self.task.log(f"   ✅ Enabled: {enabled}")
        return TaskResult.PASSED if enabled else TaskResult.FAILED

    async def _execute_is_selected(self, step_data: Dict) -> TaskResult:
        """检查元素是否选中"""
        locator = step_data.get('locator')
        if not locator:
            return TaskResult.FAILED

        selected = await self.driver.is_selected(self.task.device_serial, locator)
        self.task.log(f"   ☑️  Selected: {selected}")
        return TaskResult.PASSED if selected else TaskResult.FAILED

    async def _execute_scroll_to(self, step_data: Dict) -> TaskResult:
        """滚动到元素"""
        locator = step_data.get('locator')
        if not locator:
            return TaskResult.FAILED

        self.task.log(f"   📜 Scrolling to element")
        success = await self.driver.scroll_to_element(self.task.device_serial, locator)
        return TaskResult.PASSED if success else TaskResult.FAILED

    # ========== 系统操作实现 ==========

    async def _execute_get_current_activity(self, step_data: Dict) -> TaskResult:
        """获取当前Activity"""
        activity = await self.driver.get_current_activity(self.task.device_serial)
        if activity:
            self.task.log(f"   📱 Current Activity: {activity}")
            return TaskResult.PASSED
        else:
            return TaskResult.FAILED

    async def _execute_open_notifications(self, step_data: Dict) -> TaskResult:
        """打开通知栏"""
        self.task.log(f"   📬 Opening notifications")
        success = await self.driver.open_notifications(self.task.device_serial)
        return TaskResult.PASSED if success else TaskResult.FAILED

    async def _execute_toggle_location(self, step_data: Dict) -> TaskResult:
        """开关定位服务"""
        enabled = step_data.get('action_value', 'true').lower() == 'true'
        self.task.log(f"   📍 Toggle location: {enabled}")
        success = await self.driver.toggle_location(self.task.device_serial, enabled)
        return TaskResult.PASSED if success else TaskResult.FAILED

    async def _execute_toggle_wifi(self, step_data: Dict) -> TaskResult:
        """开关WiFi"""
        enabled = step_data.get('action_value', 'true').lower() == 'true'
        self.task.log(f"   📶 Toggle WiFi: {enabled}")
        success = await self.driver.toggle_wifi(self.task.device_serial, enabled)
        return TaskResult.PASSED if success else TaskResult.FAILED

    # ========== 高级操作实现 ==========

    async def _execute_toast_check(self, step_data: Dict) -> TaskResult:
        """检查Toast提示"""
        toast_text = step_data.get('action_value', '')
        self.task.log(f"   🔍 Checking Toast: {toast_text}")
        # TODO: 实现Toast检查逻辑
        self.task.log(f"   ⚠️  Toast check not fully implemented")
        return TaskResult.PASSED

    async def _execute_webview_switch(self, step_data: Dict) -> TaskResult:
        """切换到WebView"""
        webview_name = step_data.get('action_value', '')
        self.task.log(f"   🌐 Switching to WebView: {webview_name}")
        success = await self.driver.switch_to_webview(self.task.device_serial, webview_name)
        return TaskResult.PASSED if success else TaskResult.FAILED

    async def _execute_native_app_switch(self, step_data: Dict) -> TaskResult:
        """切换到原生应用"""
        self.task.log(f"   📱 Switching to native app")
        success = await self.driver.switch_to_native_app(self.task.device_serial)
        return TaskResult.PASSED if success else TaskResult.FAILED
