"""Device driver abstraction for execution engine."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class DeviceDriver(ABC):
    """Abstract driver interface for different platforms."""

    @abstractmethod
    async def tap_element(self, serial: str, locator: Dict[str, Any]) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def long_press(self, serial: str, locator: Dict[str, Any], duration_ms: int = 2000) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def input_text(self, serial: str, locator: Dict[str, Any], text: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def swipe(self, serial: str, direction: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def press_back(self, serial: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def wait_for_element(self, serial: str, locator: Dict[str, Any], timeout_ms: int = 5000) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def element_exists(self, serial: str, locator: Dict[str, Any]) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def get_element_text(self, serial: str, locator: Dict[str, Any]) -> Optional[str]:
        raise NotImplementedError

    @abstractmethod
    async def start_activity(self, serial: str, activity_name: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def take_screenshot(self, serial: str, path: str | None = None) -> bool:
        raise NotImplementedError

    # ========== 新增基础操作 ==========

    @abstractmethod
    async def clear_text(self, serial: str, locator: Dict[str, Any]) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def press_home(self, serial: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def press_recent(self, serial: str) -> bool:
        raise NotImplementedError

    # ========== 断言操作 ==========

    @abstractmethod
    async def is_enabled(self, serial: str, locator: Dict[str, Any]) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def is_displayed(self, serial: str, locator: Dict[str, Any]) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def is_selected(self, serial: str, locator: Dict[str, Any]) -> bool:
        raise NotImplementedError

    # ========== Appium操作 ==========

    @abstractmethod
    async def get_element_attribute(self, serial: str, locator: Dict[str, Any], attr_name: str) -> Optional[str]:
        raise NotImplementedError

    @abstractmethod
    async def get_element_location(self, serial: str, locator: Dict[str, Any]) -> Optional[Dict[str, int]]:
        raise NotImplementedError

    @abstractmethod
    async def get_element_size(self, serial: str, locator: Dict[str, Any]) -> Optional[Dict[str, int]]:
        raise NotImplementedError

    @abstractmethod
    async def scroll_to_element(self, serial: str, locator: Dict[str, Any]) -> bool:
        raise NotImplementedError

    # ========== 系统操作 ==========

    @abstractmethod
    async def get_current_activity(self, serial: str) -> Optional[str]:
        raise NotImplementedError

    @abstractmethod
    async def open_notifications(self, serial: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def toggle_location(self, serial: str, enabled: bool) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def toggle_wifi(self, serial: str, enabled: bool) -> bool:
        raise NotImplementedError

    # ========== ADB操作 ==========

    @abstractmethod
    async def adb_install(self, serial: str, apk_path: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def adb_uninstall(self, serial: str, package_name: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def adb_start_app(self, serial: str, package_name: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def adb_stop_app(self, serial: str, package_name: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def adb_restart_app(self, serial: str, package_name: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def adb_clear_app(self, serial: str, package_name: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def adb_tap(self, serial: str, x: int, y: int) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def adb_swipe(self, serial: str, config: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def adb_key_event(self, serial: str, keycode: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def adb_input_text(self, serial: str, text: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def adb_shell(self, serial: str, cmd: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def adb_push(self, serial: str, local_path: str, remote_path: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def adb_pull(self, serial: str, remote_path: str, local_path: str) -> bool:
        raise NotImplementedError

    # ========== 高级操作 ==========

    @abstractmethod
    async def switch_to_webview(self, serial: str, webview_name: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def switch_to_native_app(self, serial: str) -> bool:
        raise NotImplementedError
