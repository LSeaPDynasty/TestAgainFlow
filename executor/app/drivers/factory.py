"""Driver factory for platform routing."""
from __future__ import annotations

from .android_driver import AndroidDriver
from .base import DeviceDriver
from .ios_driver import IOSDriver
from .web_driver import WebDriver
from ..services.adb_service import ADBService


def create_driver(platform: str | None, adb_service: ADBService) -> DeviceDriver:
    normalized = (platform or "android").strip().lower()
    if normalized == "android":
        return AndroidDriver(adb_service)
    if normalized == "ios":
        return IOSDriver()
    if normalized == "web":
        return WebDriver()
    raise ValueError(f"Unsupported platform: {normalized}")
