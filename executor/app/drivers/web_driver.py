"""Web driver placeholder."""
from __future__ import annotations

from typing import Any, Dict, Optional

from .base import DeviceDriver


class WebDriver(DeviceDriver):
    """Placeholder Web driver implementation."""

    def _unsupported(self) -> None:
        raise NotImplementedError("Web driver is not implemented yet")

    async def tap_element(self, serial: str, locator: Dict[str, Any]) -> bool:
        self._unsupported()

    async def long_press(self, serial: str, locator: Dict[str, Any], duration_ms: int = 2000) -> bool:
        self._unsupported()

    async def input_text(self, serial: str, locator: Dict[str, Any], text: str) -> bool:
        self._unsupported()

    async def swipe(self, serial: str, direction: str) -> bool:
        self._unsupported()

    async def press_back(self, serial: str) -> bool:
        self._unsupported()

    async def wait_for_element(self, serial: str, locator: Dict[str, Any], timeout_ms: int = 5000) -> bool:
        self._unsupported()

    async def element_exists(self, serial: str, locator: Dict[str, Any]) -> bool:
        self._unsupported()

    async def get_element_text(self, serial: str, locator: Dict[str, Any]) -> Optional[str]:
        self._unsupported()

    async def start_activity(self, serial: str, activity_name: str) -> bool:
        self._unsupported()

    async def take_screenshot(self, serial: str, path: str | None = None) -> bool:
        self._unsupported()
