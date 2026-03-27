"""
ADB Actions - ADB操作
包括：adb_install, adb_uninstall, adb_start_app等ADB相关操作
"""
import logging
from typing import Dict, Any
from .base import BaseAction
from .registry import register_action
from ..task import TaskResult

logger = logging.getLogger(__name__)


@register_action
class AdbInstallAction(BaseAction):
    """ADB安装应用"""
    action_type = "adb_install"
    description = "通过ADB安装应用"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        apk_path = step_data.get('apk_path', '')

        if not apk_path:
            self.log_error("AdbInstall action requires apk_path")
            return TaskResult.FAILED

        try:
            await self.driver.adb_install(apk_path)
            self.log_info(f"Installed APK: {apk_path}")
            return TaskResult.PASSED
        except Exception as e:
            self.log_error(f"AdbInstall error: {e}")
            return TaskResult.FAILED


@register_action
class AdbUninstallAction(BaseAction):
    """ADB卸载应用"""
    action_type = "adb_uninstall"
    description = "通过ADB卸载应用"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        package_name = step_data.get('package_name', '')

        if not package_name:
            self.log_error("AdbUninstall action requires package_name")
            return TaskResult.FAILED

        try:
            await self.driver.adb_uninstall(package_name)
            self.log_info(f"Uninstalled package: {package_name}")
            return TaskResult.PASSED
        except Exception as e:
            self.log_error(f"AdbUninstall error: {e}")
            return TaskResult.FAILED


@register_action
class AdbStartAppAction(BaseAction):
    """ADB启动应用"""
    action_type = "adb_start_app"
    description = "通过ADB启动应用"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        package_name = step_data.get('package_name', '')
        activity = step_data.get('activity', '')

        if not package_name:
            self.log_error("AdbStartApp action requires package_name")
            return TaskResult.FAILED

        try:
            await self.driver.adb_start_app(package_name, activity)
            self.log_info(f"Started app: {package_name}")
            return TaskResult.PASSED
        except Exception as e:
            self.log_error(f"AdbStartApp error: {e}")
            return TaskResult.FAILED


@register_action
class AdbStopAppAction(BaseAction):
    """ADB停止应用"""
    action_type = "adb_stop_app"
    description = "通过ADB停止应用"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        package_name = step_data.get('package_name', '')

        if not package_name:
            self.log_error("AdbStopApp action requires package_name")
            return TaskResult.FAILED

        try:
            await self.driver.adb_stop_app(package_name)
            self.log_info(f"Stopped app: {package_name}")
            return TaskResult.PASSED
        except Exception as e:
            self.log_error(f"AdbStopApp error: {e}")
            return TaskResult.FAILED


@register_action
class AdbRestartAppAction(BaseAction):
    """ADB重启应用"""
    action_type = "adb_restart_app"
    description = "通过ADB重启应用"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        package_name = step_data.get('package_name', '')

        if not package_name:
            self.log_error("AdbRestartApp action requires package_name")
            return TaskResult.FAILED

        try:
            await self.driver.adb_stop_app(package_name)
            await self.driver.adb_start_app(package_name)
            self.log_info(f"Restarted app: {package_name}")
            return TaskResult.PASSED
        except Exception as e:
            self.log_error(f"AdbRestartApp error: {e}")
            return TaskResult.FAILED


@register_action
class AdbClearAppAction(BaseAction):
    """ADB清除应用数据"""
    action_type = "adb_clear_app"
    description = "通过ADB清除应用数据"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        package_name = step_data.get('package_name', '')

        if not package_name:
            self.log_error("AdbClearApp action requires package_name")
            return TaskResult.FAILED

        try:
            await self.driver.adb_clear_app(package_name)
            self.log_info(f"Cleared app data: {package_name}")
            return TaskResult.PASSED
        except Exception as e:
            self.log_error(f"AdbClearApp error: {e}")
            return TaskResult.FAILED


@register_action
class AdbTapAction(BaseAction):
    """ADB点击屏幕坐标"""
    action_type = "adb_tap"
    description = "通过ADB点击屏幕坐标"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        x = step_data.get('x', 0)
        y = step_data.get('y', 0)

        try:
            await self.driver.adb_tap(x, y)
            self.log_info(f"ADB tapped at ({x}, {y})")
            return TaskResult.PASSED
        except Exception as e:
            self.log_error(f"AdbTap error: {e}")
            return TaskResult.FAILED


@register_action
class AdbSwipeAction(BaseAction):
    """ADB滑动屏幕"""
    action_type = "adb_swipe"
    description = "通过ADB滑动屏幕"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        x1 = step_data.get('x1', 0)
        y1 = step_data.get('y1', 0)
        x2 = step_data.get('x2', 0)
        y2 = step_data.get('y2', 0)
        duration = step_data.get('duration', 500)

        try:
            await self.driver.adb_swipe(x1, y1, x2, y2, duration)
            self.log_info(f"ADB swiped from ({x1}, {y1}) to ({x2}, {y2})")
            return TaskResult.PASSED
        except Exception as e:
            self.log_error(f"AdbSwipe error: {e}")
            return TaskResult.FAILED


@register_action
class AdbKeyEventAction(BaseAction):
    """ADB按键事件"""
    action_type = "adb_key_event"
    description = "通过ADB发送按键事件"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        keycode = step_data.get('keycode', '')

        if not keycode:
            self.log_error("AdbKeyEvent action requires keycode")
            return TaskResult.FAILED

        try:
            await self.driver.adb_key_event(keycode)
            self.log_info(f"ADB sent key event: {keycode}")
            return TaskResult.PASSED
        except Exception as e:
            self.log_error(f"AdbKeyEvent error: {e}")
            return TaskResult.FAILED


@register_action
class AdbInputTextAction(BaseAction):
    """ADB输入文本"""
    action_type = "adb_input_text"
    description = "通过ADB输入文本"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        text = step_data.get('text', '')

        if not text:
            self.log_error("AdbInputText action requires text")
            return TaskResult.FAILED

        try:
            # 替换变量
            text = self.replace_variables(text)
            await self.driver.adb_input_text(text)
            self.log_info(f"ADB input text: {text}")
            return TaskResult.PASSED
        except Exception as e:
            self.log_error(f"AdbInputText error: {e}")
            return TaskResult.FAILED


@register_action
class AdbShellAction(BaseAction):
    """ADB Shell命令"""
    action_type = "adb_shell"
    description = "执行ADB Shell命令"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        command = step_data.get('command', '')

        if not command:
            self.log_error("AdbShell action requires command")
            return TaskResult.FAILED

        try:
            # 替换变量
            command = self.replace_variables(command)
            result = await self.driver.adb_shell(command)
            self.log_info(f"ADB shell command: {command}")
            self.log_info(f"Result: {result}")
            return TaskResult.PASSED
        except Exception as e:
            self.log_error(f"AdbShell error: {e}")
            return TaskResult.FAILED


@register_action
class AdbPushFileAction(BaseAction):
    """ADB推送文件"""
    action_type = "adb_push_file"
    description = "通过ADB推送文件到设备"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        local_path = step_data.get('local_path', '')
        remote_path = step_data.get('remote_path', '')

        if not local_path or not remote_path:
            self.log_error("AdbPushFile action requires local_path and remote_path")
            return TaskResult.FAILED

        try:
            await self.driver.adb_push_file(local_path, remote_path)
            self.log_info(f"ADB pushed file: {local_path} -> {remote_path}")
            return TaskResult.PASSED
        except Exception as e:
            self.log_error(f"AdbPushFile error: {e}")
            return TaskResult.FAILED


@register_action
class AdbPullFileAction(BaseAction):
    """ADB拉取文件"""
    action_type = "adb_pull_file"
    description = "通过ADB从设备拉取文件"

    async def execute(self, step_data: Dict[str, Any]) -> TaskResult:
        remote_path = step_data.get('remote_path', '')
        local_path = step_data.get('local_path', '')

        if not remote_path or not local_path:
            self.log_error("AdbPullFile action requires remote_path and local_path")
            return TaskResult.FAILED

        try:
            await self.driver.adb_pull_file(remote_path, local_path)
            self.log_info(f"ADB pulled file: {remote_path} -> {local_path}")
            return TaskResult.PASSED
        except Exception as e:
            self.log_error(f"AdbPullFile error: {e}")
            return TaskResult.FAILED
