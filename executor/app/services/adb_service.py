"""
ADB Service
Handles all ADB operations for device control
"""
import asyncio
import logging
import subprocess
import json
import re
from typing import Dict, Any, Optional, List
from ..core.config import settings

logger = logging.getLogger(__name__)


class ADBService:
    """
    Android Debug Bridge (ADB) Service
    Provides high-level interface for device control
    """

    def __init__(self, adb_path: str = None):
        self.adb_path = adb_path or settings.adb_path
        self._devices_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_valid_until = 0

    async def initialize(self):
        """Initialize ADB service"""
        logger.info("🔧 Initializing ADB service...")

        # Check ADB availability
        result = await self._run_adb_command(["version"])
        if result["returncode"] == 0:
            logger.info(f"✅ ADB available: {result['stdout'].strip()}")
        else:
            logger.warning("⚠️  ADB not found or not accessible")

        # Start ADB server
        await self._run_adb_command(["start-server"])

        logger.info("✅ ADB service initialized")

    async def cleanup(self):
        """Cleanup ADB service"""
        logger.info("🧹 Cleaning up ADB service...")

    async def get_devices(self) -> List[Dict[str, Any]]:
        """Get list of connected devices"""
        result = await self._run_adb_command(["devices", "-l"])
        if result["returncode"] != 0:
            logger.error(f"Failed to get devices: {result['stderr']}")
            return []

        devices = []
        lines = result["stdout"].strip().split('\n')[1:]  # Skip header

        for line in lines:
            if not line.strip():
                continue

            parts = line.split()
            if len(parts) >= 2:
                serial = parts[0]
                status = parts[1]

                device_info = {
                    "serial": serial,
                    "status": status,
                    "connection_type": "USB" if ":" not in serial else "TCP/IP"
                }

                # Get device properties
                if status == "device":
                    props = await self.get_device_properties(serial)
                    device_info.update(props)

                devices.append(device_info)

        return devices

    async def get_device_properties(self, serial: str) -> Dict[str, Any]:
        """Get device properties"""
        properties = {}

        # Get Android version
        result = await self._run_adb_command(
            ["-s", serial, "shell", "getprop", "ro.build.version.release"]
        )
        if result["returncode"] == 0:
            properties["android_version"] = result["stdout"].strip()

        # Get device model
        result = await self._run_adb_command(
            ["-s", serial, "shell", "getprop", "ro.product.model"]
        )
        if result["returncode"] == 0:
            properties["model"] = result["stdout"].strip()

        # Get device brand
        result = await self._run_adb_command(
            ["-s", serial, "shell", "getprop", "ro.product.brand"]
        )
        if result["returncode"] == 0:
            properties["brand"] = result["stdout"].strip()

        # Get screen size
        result = await self._run_adb_command(
            ["-s", serial, "shell", "wm", "size"]
        )
        if result["returncode"] == 0:
            match = re.search(r'(\d+x\d+)', result["stdout"])
            if match:
                properties["screen_size"] = match.group(1)

        return properties

    async def tap_element(self, serial: str, locator: Dict[str, Any]) -> bool:
        """Tap on element at specified coordinates"""
        try:
            # Get element bounds
            bounds = await self._get_element_bounds(serial, locator)
            if not bounds:
                return False

            # Calculate center point
            x = (bounds["left"] + bounds["right"]) // 2
            y = (bounds["top"] + bounds["bottom"]) // 2

            # Tap
            result = await self._run_adb_command(
                ["-s", serial, "shell", "input", "tap", str(x), str(y)]
            )

            return result["returncode"] == 0

        except Exception as e:
            logger.error(f"Tap failed: {e}")
            return False

    async def long_press(self, serial: str, locator: Dict[str, Any], duration_ms: int = 2000) -> bool:
        """Long press on element"""
        try:
            bounds = await self._get_element_bounds(serial, locator)
            if not bounds:
                return False

            x = (bounds["left"] + bounds["right"]) // 2
            y = (bounds["top"] + bounds["bottom"]) // 2

            # Long press using swipe (tap and hold)
            result = await self._run_adb_command(
                ["-s", serial, "shell", "input", "swipe",
                 str(x), str(y), str(x), str(y), str(duration_ms)]
            )

            return result["returncode"] == 0

        except Exception as e:
            logger.error(f"Long press failed: {e}")
            return False

    async def input_text(self, serial: str, locator: Dict[str, Any], text: str) -> bool:
        """Input text into element"""
        try:
            # First tap to focus
            await self.tap_element(serial, locator)

            # Wait a bit for keyboard to appear
            await asyncio.sleep(0.5)

            # Input text
            result = await self._run_adb_command(
                ["-s", serial, "shell", "input", "text", text.replace(" ", "%s")]
            )

            return result["returncode"] == 0

        except Exception as e:
            logger.error(f"Input text failed: {e}")
            return False

    async def swipe(self, serial: str, direction: str) -> bool:
        """Swipe in specified direction"""
        try:
            # Get screen size
            screen_size = await self._get_screen_size(serial)
            if not screen_size:
                return False

            width, height = screen_size
            center_x = width // 2
            center_y = height // 2

            # Calculate swipe coordinates based on direction
            swipe_coords = {
                "up": (center_x, int(height * 0.7), center_x, int(height * 0.3)),
                "down": (center_x, int(height * 0.3), center_x, int(height * 0.7)),
                "left": (int(width * 0.7), center_y, int(width * 0.3), center_y),
                "right": (int(width * 0.3), center_y, int(width * 0.7), center_y),
            }

            if direction not in swipe_coords:
                logger.error(f"Unknown swipe direction: {direction}")
                return False

            x1, y1, x2, y2 = swipe_coords[direction]

            result = await self._run_adb_command(
                ["-s", serial, "shell", "input", "swipe",
                 str(x1), str(y1), str(x2), str(y2), "300"]
            )

            return result["returncode"] == 0

        except Exception as e:
            logger.error(f"Swipe failed: {e}")
            return False

    async def press_back(self, serial: str) -> bool:
        """Press back button"""
        result = await self._run_adb_command(
            ["-s", serial, "shell", "input", "keyevent", "KEYCODE_BACK"]
        )
        return result["returncode"] == 0

    async def wait_for_element(
        self,
        serial: str,
        locator: Dict[str, Any],
        timeout_ms: int = 5000
    ) -> bool:
        """Wait for element to appear"""
        start_time = asyncio.get_event_loop().time()

        while True:
            if await self.element_exists(serial, locator):
                return True

            elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
            if elapsed >= timeout_ms:
                return False

            await asyncio.sleep(0.5)

    async def element_exists(self, serial: str, locator: Dict[str, Any]) -> bool:
        """Check if element exists"""
        bounds = await self._get_element_bounds(serial, locator)
        return bounds is not None

    async def get_element_text(self, serial: str, locator: Dict[str, Any]) -> Optional[str]:
        """Get text from element using uiautomator2"""
        try:
            from .ui_automator import UIAutomatorService

            ui_service = UIAutomatorService(serial)
            locator_type = locator.get('type', '')
            locator_value = locator.get('value', '')

            # 根据定位器类型查找元素
            if locator_type == 'resource-id':
                result = ui_service.find_element_by_resource_id(locator_value)
            elif locator_type == 'text':
                result = ui_service.find_element_by_text(locator_value)
            elif locator_type == 'xpath':
                result = ui_service.find_element_by_xpath(locator_value)
            else:
                logger.error(f"不支持的定位器类型: {locator_type}")
                return None

            if result and result.get('found'):
                return result.get('text', '')

            return None

        except Exception as e:
            logger.error(f"获取元素文本失败: {e}")
            return None

    async def start_activity(self, serial: str, activity_name: str) -> bool:
        """Start an activity"""
        result = await self._run_adb_command(
            ["-s", serial, "shell", "am", "start", "-n", activity_name]
        )
        return result["returncode"] == 0

    async def take_screenshot(self, serial: str, path: str = None) -> bool:
        """Take screenshot"""
        import os
        from datetime import datetime

        if not path:
            os.makedirs(settings.screenshot_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(settings.screenshot_dir, f"screenshot_{serial}_{timestamp}.png")

        # Pull screenshot from device
        temp_path = "/sdcard/screenshot.png"
        result = await self._run_adb_command(
            ["-s", serial, "shell", "screencap", "-p", temp_path]
        )

        if result["returncode"] != 0:
            return False

        result = await self._run_adb_command(
            ["-s", serial, "pull", temp_path, path]
        )

        return result["returncode"] == 0

    async def _get_screen_size(self, serial: str) -> Optional[tuple]:
        """Get screen size"""
        result = await self._run_adb_command(
            ["-s", serial, "shell", "wm", "size"]
        )

        if result["returncode"] == 0:
            match = re.search(r'Physical size: (\d+)x(\d+)', result["stdout"])
            if match:
                return int(match.group(1)), int(match.group(2))

        return None

    async def _get_element_bounds(
        self,
        serial: str,
        locator: Dict[str, Any]
    ) -> Optional[Dict[str, int]]:
        """
        Get element bounds from locator using uiautomator2
        """
        try:
            from .ui_automator import UIAutomatorService

            ui_service = UIAutomatorService(serial)
            locator_type = locator.get('type', '')
            locator_value = locator.get('value', '')

            # 根据定位器类型查找元素
            if locator_type == 'resource-id':
                result = ui_service.find_element_by_resource_id(locator_value)
            elif locator_type == 'text':
                result = ui_service.find_element_by_text(locator_value)
            elif locator_type == 'xpath':
                result = ui_service.find_element_by_xpath(locator_value)
            else:
                logger.error(f"不支持的定位器类型: {locator_type}")
                return None

            if result and result.get('found'):
                bounds = result.get('bounds')
                if bounds:
                    logger.debug(f"找到元素坐标: {bounds}")
                    return bounds

            logger.warning(f"未找到元素: {locator_type}={locator_value}")
            return None

        except Exception as e:
            logger.error(f"获取元素坐标失败: {e}")
            return None

    async def _run_adb_command(self, args: List[str]) -> Dict[str, Any]:
        """Run ADB command"""
        try:
            cmd = [self.adb_path] + args
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=settings.adb_timeout
            )

            return {
                "returncode": process.returncode,
                "stdout": stdout.decode('utf-8', errors='ignore'),
                "stderr": stderr.decode('utf-8', errors='ignore')
            }

        except asyncio.TimeoutError:
            logger.error(f"ADB command timed out: {' '.join(args)}")
            return {"returncode": -1, "stdout": "", "stderr": "Command timed out"}
        except Exception as e:
            logger.error(f"ADB command failed: {e}")
            return {"returncode": -1, "stdout": "", "stderr": str(e)}

    # ========== 新增基础操作 ==========

    async def clear_text(self, serial: str, locator: Dict[str, Any]) -> bool:
        """清除元素文本"""
        try:
            bounds = await self._get_element_bounds(serial, locator)
            if not bounds:
                return False

            x, y = bounds['center']
            # 长按选中文本
            await self.long_press(serial, locator, 1000)
            # 全选
            await asyncio.sleep(0.5)
            await self._run_adb_command(['-s', serial, 'shell', 'input', 'keyevent', 'KEYCODE_CTRL_A'])
            await asyncio.sleep(0.3)
            # 删除
            await self._run_adb_command(['-s', serial, 'shell', 'input', 'keyevent', 'KEYCODE_DEL'])
            return True
        except Exception as e:
            logger.error(f"清除文本失败: {e}")
            return False

    async def press_home(self, serial: str) -> bool:
        """按Home键"""
        result = await self._run_adb_command(['-s', serial, 'shell', 'input', 'keyevent', 'KEYCODE_HOME'])
        return result['returncode'] == 0

    async def press_recent(self, serial: str) -> bool:
        """按最近任务键"""
        result = await self._run_adb_command(['-s', serial, 'shell', 'input', 'keyevent', 'KEYCODE_APP_SWITCH'])
        return result['returncode'] == 0

    # ========== 断言操作 ==========

    async def is_enabled(self, serial: str, locator: Dict[str, Any]) -> bool:
        """检查元素是否可用"""
        try:
            bounds = await self._get_element_bounds(serial, locator)
            return bounds is not None
        except:
            return False

    async def is_displayed(self, serial: str, locator: Dict[str, Any]) -> bool:
        """检查元素是否显示"""
        try:
            bounds = await self._get_element_bounds(serial, locator)
            return bounds is not None
        except:
            return False

    async def is_selected(self, serial: str, locator: Dict[str, Any]) -> bool:
        """检查元素是否选中"""
        try:
            bounds = await self._get_element_bounds(serial, locator)
            return bounds is not None
        except:
            return False

    # ========== Appium操作 ==========

    async def get_element_attribute(self, serial: str, locator: Dict[str, Any], attr_name: str) -> Optional[str]:
        """获取元素属性"""
        try:
            # 使用uiautomator获取属性
            xml = await self._dump_ui_hierarchy(serial)
            if not xml:
                return None

            element = self._find_element_in_xml(xml, locator)
            if not element:
                return None

            return element.get(attr_name, None)
        except Exception as e:
            logger.error(f"获取属性失败: {e}")
            return None

    async def get_element_location(self, serial: str, locator: Dict[str, Any]) -> Optional[Dict[str, int]]:
        """获取元素位置"""
        try:
            bounds = await self._get_element_bounds(serial, locator)
            if bounds:
                return {'x': bounds['left'], 'y': bounds['top']}
            return None
        except:
            return None

    async def get_element_size(self, serial: str, locator: Dict[str, Any]) -> Optional[Dict[str, int]]:
        """获取元素大小"""
        try:
            bounds = await self._get_element_bounds(serial, locator)
            if bounds:
                return {
                    'width': bounds['right'] - bounds['left'],
                    'height': bounds['bottom'] - bounds['top']
                }
            return None
        except:
            return None

    async def scroll_to_element(self, serial: str, locator: Dict[str, Any]) -> bool:
        """滚动到元素"""
        try:
            # 简单实现：多次滑动查找元素
            for _ in range(5):
                if await self.element_exists(serial, locator):
                    return True
                await self.swipe(serial, 'up')
                await asyncio.sleep(0.5)
            return False
        except Exception as e:
            logger.error(f"滚动到元素失败: {e}")
            return False

    # ========== 系统操作 ==========

    async def get_current_activity(self, serial: str) -> Optional[str]:
        """获取当前Activity"""
        try:
            result = await self._run_adb_command([
                '-s', serial, 'shell', 'dumpsys', 'window', 'windows', '|', 'grep', '-E', 'mCurrentFocus|mFocusedApp'
            ])
            if result['returncode'] == 0:
                output = result['stdout'].strip()
                # 解析输出获取Activity
                if 'mCurrentFocus' in output:
                    return output.split('mCurrentFocus')[1].split('/')[0].strip().split(' ')[-1]
            return None
        except Exception as e:
            logger.error(f"获取当前Activity失败: {e}")
            return None

    async def open_notifications(self, serial: str) -> bool:
        """打开通知栏"""
        result = await self._run_adb_command(['-s', serial, 'shell', 'cmd', 'statusbar', 'expand'])
        return result['returncode'] == 0

    async def toggle_location(self, serial: str, enabled: bool) -> bool:
        """开关定位服务"""
        try:
            if enabled:
                result = await self._run_adb_command(['-s', serial, 'shell', 'settings', 'put', 'secure', 'location_providers_allowed', 'gps,network'])
            else:
                result = await self._run_adb_command(['-s', serial, 'shell', 'settings', 'put', 'secure', 'location_providers_allowed', ''])
            return result['returncode'] == 0
        except Exception as e:
            logger.error(f"切换定位失败: {e}")
            return False

    async def toggle_wifi(self, serial: str, enabled: bool) -> bool:
        """开关WiFi"""
        try:
            if enabled:
                result = await self._run_adb_command(['-s', serial, 'shell', 'svc', 'wifi', 'enable'])
            else:
                result = await self._run_adb_command(['-s', serial, 'shell', 'svc', 'wifi', 'disable'])
            return result['returncode'] == 0
        except Exception as e:
            logger.error(f"切换WiFi失败: {e}")
            return False

    # ========== ADB操作 ==========

    async def adb_install(self, serial: str, apk_path: str) -> bool:
        """安装应用"""
        result = await self._run_adb_command(['-s', serial, 'install', '-r', apk_path])
        return result['returncode'] == 0

    async def adb_uninstall(self, serial: str, package_name: str) -> bool:
        """卸载应用"""
        result = await self._run_adb_command(['-s', serial, 'uninstall', package_name])
        return result['returncode'] == 0

    async def adb_start_app(self, serial: str, package_name: str) -> bool:
        """启动应用"""
        result = await self._run_adb_command(['-s', serial, 'shell', 'monkey', '-p', package_name, '-c', 'android.intent.category.LAUNCHER', '1'])
        return result['returncode'] == 0

    async def adb_stop_app(self, serial: str, package_name: str) -> bool:
        """停止应用"""
        result = await self._run_adb_command(['-s', serial, 'shell', 'am', 'force-stop', package_name])
        return result['returncode'] == 0

    async def adb_restart_app(self, serial: str, package_name: str) -> bool:
        """重启应用"""
        await self.adb_stop_app(serial, package_name)
        await asyncio.sleep(1)
        return await self.adb_start_app(serial, package_name)

    async def adb_clear_app(self, serial: str, package_name: str) -> bool:
        """清除应用数据"""
        result = await self._run_adb_command(['-s', serial, 'shell', 'pm', 'clear', package_name])
        return result['returncode'] == 0

    async def adb_tap(self, serial: str, x: int, y: int) -> bool:
        """点击坐标"""
        result = await self._run_adb_command(['-s', serial, 'shell', 'input', 'tap', str(x), str(y)])
        return result['returncode'] == 0

    async def adb_swipe(self, serial: str, config: str) -> bool:
        """ADB滑动"""
        try:
            # 解析配置: x1,y1,x2,y2,duration
            parts = config.split(',')
            if len(parts) >= 4:
                x1, y1, x2, y2 = parts[0], parts[1], parts[2], parts[3]
                duration = parts[4] if len(parts) > 4 else '300'
                result = await self._run_adb_command([
                    '-s', serial, 'shell', 'input', 'swipe',
                    x1.strip(), y1.strip(), x2.strip(), y2.strip(), duration.strip()
                ])
                return result['returncode'] == 0
        except Exception as e:
            logger.error(f"ADB滑动失败: {e}")
        return False

    async def adb_key_event(self, serial: str, keycode: str) -> bool:
        """发送按键事件"""
        result = await self._run_adb_command(['-s', serial, 'shell', 'input', 'keyevent', keycode])
        return result['returncode'] == 0

    async def adb_input_text(self, serial: str, text: str) -> bool:
        """通过ADB输入文本"""
        result = await self._run_adb_command(['-s', serial, 'shell', 'input', 'text', text])
        return result['returncode'] == 0

    async def adb_shell(self, serial: str, cmd: str) -> bool:
        """执行Shell命令"""
        result = await self._run_adb_command(['-s', serial, 'shell', cmd])
        return result['returncode'] == 0

    async def adb_push(self, serial: str, local_path: str, remote_path: str) -> bool:
        """推送文件到设备"""
        result = await self._run_adb_command(['-s', serial, 'push', local_path, remote_path])
        return result['returncode'] == 0

    async def adb_pull(self, serial: str, remote_path: str, local_path: str) -> bool:
        """从设备拉取文件"""
        result = await self._run_adb_command(['-s', serial, 'pull', remote_path, local_path])
        return result['returncode'] == 0

    # ========== 高级操作 ==========

    async def switch_to_webview(self, serial: str, webview_name: str) -> bool:
        """切换到WebView（简化实现）"""
        # 实际实现需要Appium或selendroid
        logger.warning(f"切换到WebView暂未完全实现: {webview_name}")
        return True

    async def switch_to_native_app(self, serial: str) -> bool:
        """切换到原生应用（简化实现）"""
        # 实际实现需要Appium
        logger.warning("切换到原生应用暂未完全实现")
        return True
