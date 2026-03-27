"""Android driver backed by ADBService."""
from __future__ import annotations

from typing import Any, Dict, Optional

from .base import DeviceDriver
from ..services.adb_service import ADBService


class AndroidDriver(DeviceDriver):
    """Android implementation of device driver interface."""

    def __init__(self, adb_service: ADBService):
        self.adb_service = adb_service

    async def tap_element(self, serial: str, locator: Dict[str, Any]) -> bool:
        return await self.adb_service.tap_element(serial, locator)

    async def long_press(self, serial: str, locator: Dict[str, Any], duration_ms: int = 2000) -> bool:
        return await self.adb_service.long_press(serial, locator, duration_ms)

    async def input_text(self, serial: str, locator: Dict[str, Any], text: str) -> bool:
        return await self.adb_service.input_text(serial, locator, text)

    async def swipe(self, serial: str, direction: str) -> bool:
        return await self.adb_service.swipe(serial, direction)

    async def press_back(self, serial: str) -> bool:
        return await self.adb_service.press_back(serial)

    async def wait_for_element(self, serial: str, locator: Dict[str, Any], timeout_ms: int = 5000) -> bool:
        return await self.adb_service.wait_for_element(serial, locator, timeout_ms)

    async def element_exists(self, serial: str, locator: Dict[str, Any]) -> bool:
        return await self.adb_service.element_exists(serial, locator)

    async def get_element_text(self, serial: str, locator: Dict[str, Any]) -> Optional[str]:
        return await self.adb_service.get_element_text(serial, locator)

    async def start_activity(self, serial: str, activity_name: str) -> bool:
        return await self.adb_service.start_activity(serial, activity_name)

    async def take_screenshot(self, serial: str, path: str | None = None) -> bool:
        return await self.adb_service.take_screenshot(serial, path)

    # ========== 新增基础操作 ==========

    async def clear_text(self, serial: str, locator: Dict[str, Any]) -> bool:
        return await self.adb_service.clear_text(serial, locator)

    async def press_home(self, serial: str) -> bool:
        return await self.adb_service.press_home(serial)

    async def press_recent(self, serial: str) -> bool:
        return await self.adb_service.press_recent(serial)

    # ========== 断言操作 ==========

    async def is_enabled(self, serial: str, locator: Dict[str, Any]) -> bool:
        return await self.adb_service.is_enabled(serial, locator)

    async def is_displayed(self, serial: str, locator: Dict[str, Any]) -> bool:
        return await self.adb_service.is_displayed(serial, locator)

    async def is_selected(self, serial: str, locator: Dict[str, Any]) -> bool:
        return await self.adb_service.is_selected(serial, locator)

    # ========== Appium操作 ==========

    async def get_element_attribute(self, serial: str, locator: Dict[str, Any], attr_name: str) -> Optional[str]:
        return await self.adb_service.get_element_attribute(serial, locator, attr_name)

    async def get_element_location(self, serial: str, locator: Dict[str, Any]) -> Optional[Dict[str, int]]:
        return await self.adb_service.get_element_location(serial, locator)

    async def get_element_size(self, serial: str, locator: Dict[str, Any]) -> Optional[Dict[str, int]]:
        return await self.adb_service.get_element_size(serial, locator)

    async def scroll_to_element(self, serial: str, locator: Dict[str, Any]) -> bool:
        return await self.adb_service.scroll_to_element(serial, locator)

    # ========== 系统操作 ==========

    async def get_current_activity(self, serial: str) -> Optional[str]:
        return await self.adb_service.get_current_activity(serial)

    async def open_notifications(self, serial: str) -> bool:
        return await self.adb_service.open_notifications(serial)

    async def toggle_location(self, serial: str, enabled: bool) -> bool:
        return await self.adb_service.toggle_location(serial, enabled)

    async def toggle_wifi(self, serial: str, enabled: bool) -> bool:
        return await self.adb_service.toggle_wifi(serial, enabled)

    # ========== ADB操作 ==========

    async def adb_install(self, serial: str, apk_path: str) -> bool:
        return await self.adb_service.adb_install(serial, apk_path)

    async def adb_uninstall(self, serial: str, package_name: str) -> bool:
        return await self.adb_service.adb_uninstall(serial, package_name)

    async def adb_start_app(self, serial: str, package_name: str) -> bool:
        return await self.adb_service.adb_start_app(serial, package_name)

    async def adb_stop_app(self, serial: str, package_name: str) -> bool:
        return await self.adb_service.adb_stop_app(serial, package_name)

    async def adb_restart_app(self, serial: str, package_name: str) -> bool:
        return await self.adb_service.adb_restart_app(serial, package_name)

    async def adb_clear_app(self, serial: str, package_name: str) -> bool:
        return await self.adb_service.adb_clear_app(serial, package_name)

    async def adb_tap(self, serial: str, x: int, y: int) -> bool:
        return await self.adb_service.adb_tap(serial, x, y)

    async def adb_swipe(self, serial: str, config: str) -> bool:
        return await self.adb_service.adb_swipe(serial, config)

    async def adb_key_event(self, serial: str, keycode: str) -> bool:
        return await self.adb_service.adb_key_event(serial, keycode)

    async def adb_input_text(self, serial: str, text: str) -> bool:
        return await self.adb_service.adb_input_text(serial, text)

    async def adb_shell(self, serial: str, cmd: str) -> bool:
        return await self.adb_service.adb_shell(serial, cmd)

    async def adb_push(self, serial: str, local_path: str, remote_path: str) -> bool:
        return await self.adb_service.adb_push(serial, local_path, remote_path)

    async def adb_pull(self, serial: str, remote_path: str, local_path: str) -> bool:
        return await self.adb_service.adb_pull(serial, remote_path, local_path)

    # ========== 高级操作 ==========

    async def switch_to_webview(self, serial: str, webview_name: str) -> bool:
        return await self.adb_service.switch_to_webview(serial, webview_name)

    async def switch_to_native_app(self, serial: str) -> bool:
        return await self.adb_service.switch_to_native_app(serial)
