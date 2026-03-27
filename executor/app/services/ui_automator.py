"""UI Automator service."""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class UIAutomatorService:
    """UI Automator service based on uiautomator2."""

    def __init__(self, device_serial: str):
        self.device_serial = device_serial
        self._device = None

    def _get_device(self):
        if self._device is None:
            try:
                import uiautomator2 as u2

                self._device = u2.connect(self.device_serial)
                logger.debug("UIAutomator2 connected: %s", self.device_serial)
            except Exception as e:
                logger.error("UIAutomator2 connection failed: %s", e)
                raise
        return self._device

    def find_element_by_resource_id(self, resource_id: str) -> Dict[str, Any]:
        try:
            d = self._get_device()
            element = d(resourceId=resource_id)
            if not element.exists:
                logger.warning("Element not found by resource-id: %s", resource_id)
                return {"found": False}

            info = element.info
            return {
                "found": True,
                "resource_id": resource_id,
                "text": info.get("text", ""),
                "class": info.get("className", ""),
                "bounds": info.get("bounds", {}),
                "clickable": info.get("clickable", False),
                "enabled": info.get("enabled", False),
            }
        except Exception as e:
            logger.error("Find element by resource-id failed: %s", e)
            return {"found": False, "error": str(e)}

    def find_element_by_text(self, text: str) -> Dict[str, Any]:
        try:
            d = self._get_device()
            element = d(text=text)
            if not element.exists:
                return {"found": False}

            info = element.info
            return {
                "found": True,
                "text": text,
                "resource_id": info.get("resourceId", ""),
                "class": info.get("className", ""),
                "bounds": info.get("bounds", {}),
                "clickable": info.get("clickable", False),
                "enabled": info.get("enabled", False),
            }
        except Exception as e:
            logger.error("Find element by text failed: %s", e)
            return {"found": False, "error": str(e)}

    def find_element_by_xpath(self, xpath: str) -> Dict[str, Any]:
        """Find element by XPath with compatibility fallback."""
        try:
            d = self._get_device()
            selector = d.xpath(xpath)
            if not selector.exists:
                return {"found": False}

            node = selector.get(timeout=0)
            if node is None:
                return {"found": False}

            attrs = getattr(node, "attrib", {}) or {}
            return {
                "found": True,
                "text": attrs.get("text", getattr(node, "text", "")) or "",
                "resource_id": attrs.get("resource-id", ""),
                "class": attrs.get("class", ""),
                "bounds": self._normalize_bounds(getattr(node, "bounds", None)),
                "clickable": str(attrs.get("clickable", "false")).lower() == "true",
                "enabled": str(attrs.get("enabled", "false")).lower() == "true",
            }
        except Exception as e:
            if "xpath is not allowed" in str(e).lower():
                fallback = self._find_by_xpath_text_or_desc(xpath)
                if fallback.get("found"):
                    return fallback
            logger.error("Find element by xpath failed: %s", e)
            return {"found": False, "error": str(e)}

    def _normalize_bounds(self, bounds: Any) -> Dict[str, int]:
        if isinstance(bounds, dict):
            return {
                "left": int(bounds.get("left", 0)),
                "top": int(bounds.get("top", 0)),
                "right": int(bounds.get("right", 0)),
                "bottom": int(bounds.get("bottom", 0)),
            }

        if isinstance(bounds, (list, tuple)) and len(bounds) == 4:
            left, top, right, bottom = bounds
            return {
                "left": int(left),
                "top": int(top),
                "right": int(right),
                "bottom": int(bottom),
            }

        return {"left": 0, "top": 0, "right": 0, "bottom": 0}

    def _find_by_xpath_text_or_desc(self, xpath: str) -> Dict[str, Any]:
        """Fallback for xpath patterns using text/content-desc predicates."""
        try:
            d = self._get_device()
            text_values = re.findall(r"@text\s*=\s*['\"]([^'\"]+)['\"]", xpath)
            desc_values = re.findall(
                r"@content-desc\s*=\s*['\"]([^'\"]+)['\"]", xpath
            )

            for value in text_values:
                element = d(text=value)
                if element.exists:
                    info = element.info
                    return {
                        "found": True,
                        "text": info.get("text", ""),
                        "resource_id": info.get("resourceId", ""),
                        "class": info.get("className", ""),
                        "bounds": info.get("bounds", {}),
                        "clickable": info.get("clickable", False),
                        "enabled": info.get("enabled", False),
                    }

            for value in desc_values:
                element = d(description=value)
                if element.exists:
                    info = element.info
                    return {
                        "found": True,
                        "text": info.get("text", ""),
                        "resource_id": info.get("resourceId", ""),
                        "class": info.get("className", ""),
                        "bounds": info.get("bounds", {}),
                        "clickable": info.get("clickable", False),
                        "enabled": info.get("enabled", False),
                    }
        except Exception as fallback_err:
            logger.error("XPath fallback failed: %s", fallback_err)

        return {"found": False}

    def tap_element(self, bounds: Dict[str, int]) -> bool:
        try:
            d = self._get_device()
            x = (bounds["left"] + bounds["right"]) // 2
            y = (bounds["top"] + bounds["bottom"]) // 2
            d.click(x, y)
            return True
        except Exception as e:
            logger.error("Tap element failed: %s", e)
            return False

    def input_text(self, text: str) -> bool:
        try:
            d = self._get_device()
            d.send_keys(text)
            return True
        except Exception as e:
            logger.error("Input text failed: %s", e)
            return False

    def get_current_package(self) -> Optional[str]:
        try:
            d = self._get_device()
            app_info = d.app_current()
            return app_info.get("package") if app_info else None
        except Exception as e:
            logger.error("Get current package failed: %s", e)
            return None

    def start_app(self, package_name: str) -> bool:
        try:
            d = self._get_device()
            d.app_start(package_name)
            logger.debug("App started: %s", package_name)
            return True
        except Exception as e:
            logger.error("Start app failed: %s", e)
            return False

    def dump_hierarchy(self) -> str:
        try:
            d = self._get_device()
            return d.dump_hierarchy()
        except Exception as e:
            logger.error("Dump hierarchy failed: %s", e)
            raise
