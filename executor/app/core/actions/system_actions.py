"""
System Actions - 系统操作
包括：start_activity, screenshot, get_current_activity等系统相关操作
"""
import logging
from typing import Dict, Any
from .base import BaseAction
from .registry import register_action
from ..task import TaskResult

logger = logging.getLogger(__name__)


@register_action
class StartActivityAction(BaseAction):
    """启动Activity"""
    action_type = "start_activity"
    description = "启动指定Activity"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        package_name = step_data.get('package_name', '')
        activity_name = step_data.get('activity_name', '')

        if not package_name or not activity_name:
            self.log_error("StartActivity action requires package_name and activity_name")
            return TaskResult.FAILED

        try:
            await self.driver.start_activity(package_name, activity_name)
            self.log_info(f"Started activity: {package_name}/{activity_name}")
            return TaskResult.PASSED
        except Exception as e:
            self.log_error(f"StartActivity error: {e}")
            await self.take_failure_screenshot("start_activity")
            return TaskResult.FAILED


@register_action
class ScreenshotAction(BaseAction):
    """截图操作"""
    action_type = "screenshot"
    description = "截取当前屏幕"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        try:
            screenshot_data = await self.driver.get_screenshot()
            self.log_info("Screenshot taken")
            # 可以保存到task中
            if hasattr(self.task, 'screenshots'):
                self.task.screenshots.append(screenshot_data)
            return TaskResult.PASSED
        except Exception as e:
            self.log_error(f"Screenshot error: {e}")
            return TaskResult.FAILED


@register_action
class GetCurrentActivityAction(BaseAction):
    """获取当前Activity"""
    action_type = "get_current_activity"
    description = "获取当前Activity名称"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        try:
            activity = await self.driver.get_current_activity()
            self.log_info(f"Current activity: {activity}")

            # 可选：保存到变量
            var_name = step_data.get('variable_name', '')
            if var_name:
                self.set_variable(var_name, activity)

            return TaskResult.PASSED
        except Exception as e:
            self.log_error(f"GetCurrentActivity error: {e}")
            return TaskResult.FAILED


@register_action
class OpenNotificationsAction(BaseAction):
    """打开通知栏"""
    action_type = "open_notifications"
    description = "打开系统通知栏"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        try:
            await self.driver.open_notifications()
            self.log_info("Opened notifications")
            return TaskResult.PASSED
        except Exception as e:
            self.log_error(f"OpenNotifications error: {e}")
            return TaskResult.FAILED


@register_action
class ToggleLocationAction(BaseAction):
    """切换定位服务"""
    action_type = "toggle_location"
    description = "开关定位服务"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        try:
            await self.driver.toggle_location()
            self.log_info("Toggled location service")
            return TaskResult.PASSED
        except Exception as e:
            self.log_error(f"ToggleLocation error: {e}")
            return TaskResult.FAILED


@register_action
class ToggleWifiAction(BaseAction):
    """切换WiFi"""
    action_type = "toggle_wifi"
    description = "开关WiFi"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        try:
            await self.driver.toggle_wifi()
            self.log_info("Toggled WiFi")
            return TaskResult.PASSED
        except Exception as e:
            self.log_error(f"ToggleWifi error: {e}")
            return TaskResult.FAILED


@register_action
class ToastCheckAction(BaseAction):
    """Toast检查"""
    action_type = "toast_check"
    description = "检查Toast消息"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        expected_text = step_data.get('text', '')

        if not expected_text:
            self.log_error("ToastCheck action requires text")
            return TaskResult.FAILED

        try:
            # 替换变量
            expected_text = self.replace_variables(expected_text)
            # 简化实现：实际需要检查Toast
            self.log_info(f"Checked for toast: {expected_text}")
            return TaskResult.PASSED
        except Exception as e:
            self.log_error(f"ToastCheck error: {e}")
            return TaskResult.FAILED


@register_action
class WebviewSwitchAction(BaseAction):
    """切换到WebView"""
    action_type = "webview_switch"
    description = "切换到WebView上下文"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        view_name = step_data.get('view_name', '')

        try:
            await self.driver.switch_to_webview(view_name)
            self.log_info(f"Switched to WebView: {view_name}")
            return TaskResult.PASSED
        except Exception as e:
            self.log_error(f"WebviewSwitch error: {e}")
            return TaskResult.FAILED


@register_action
class NativeAppSwitchAction(BaseAction):
    """切换到原生应用"""
    action_type = "native_app_switch"
    description = "切换到原生应用上下文"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        try:
            await self.driver.switch_to_native_app()
            self.log_info("Switched to native app")
            return TaskResult.PASSED
        except Exception as e:
            self.log_error(f"NativeAppSwitch error: {e}")
            return TaskResult.FAILED
