"""
WebSocket Client for Executor
连接到后端WebSocket服务器，实时推送执行状态
"""
import asyncio
import websockets
import json
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ExecutorWebSocketClient:
    """执行引擎WebSocket客户端"""

    def __init__(self, backend_url: str = "ws://localhost:8000"):
        self.backend_url = backend_url
        self.ws_url = f"{backend_url}/ws/executor"
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.is_connected = False
        self.reconnect_delay = 5  # 重连延迟（秒）
        self.max_reconnect_attempts = 10  # 最大重连次数
        self.reconnect_attempts = 0
        self._stop_event = asyncio.Event()

    async def connect(self) -> bool:
        """连接到WebSocket服务器"""
        try:
            logger.info(f"🔗 连接到后端WebSocket服务器: {self.ws_url}")

            self.websocket = await websockets.connect(
                self.ws_url,
                ping_interval=20,
                ping_timeout=20,
                close_timeout=10
            )

            self.is_connected = True
            self.reconnect_attempts = 0
            logger.info("✅ 已连接到后端WebSocket服务器")

            # 启动消息接收循环
            asyncio.create_task(self._receive_messages())

            # 发送初始设备列表
            await self._send_device_list()

            return True

        except Exception as e:
            logger.error(f"❌ 连接后端WebSocket失败: {e}")
            self.is_connected = False
            return False

    async def disconnect(self):
        """断开WebSocket连接"""
        self._stop_event.set()

        if self.websocket:
            try:
                await self.websocket.close()
                logger.info("🔌 WebSocket连接已关闭")
            except Exception as e:
                logger.error(f"关闭WebSocket连接时出错: {e}")

        self.is_connected = False

    async def _receive_messages(self):
        """接收消息的循环"""
        try:
            async for message in self.websocket:
                if self._stop_event.is_set():
                    break

                try:
                    data = json.loads(message)
                    await self._process_message(data)

                except json.JSONDecodeError as e:
                    logger.error(f"解析JSON消息失败: {e}")
                except Exception as e:
                    logger.error(f"处理消息时出错: {e}")

        except websockets.exceptions.ConnectionClosed:
            logger.warning("⚠️ WebSocket连接已关闭")
            self.is_connected = False

            # 尝试重连
            if not self._stop_event.is_set():
                await self._reconnect()

        except Exception as e:
            logger.error(f"接收消息时出错: {e}")
            self.is_connected = False

    async def _process_message(self, data: dict):
        """处理收到的消息"""
        message_type = data.get("type")

        if message_type == "connected":
            logger.info(f"🎉 {data.get('message')}")
        elif message_type == "pong":
            logger.debug("💓 收到心跳响应")
        elif message_type == "error":
            logger.error(f"❌ 服务器错误: {data.get('message')}")
        elif message_type == "test_device":
            # 处理设备测试请求
            await self._handle_test_device(data)
        elif message_type == "test_element":
            # 处理元素测试请求
            await self._handle_test_element(data)
        elif message_type == "get_dom":
            # 处理DOM获取请求
            await self._handle_get_dom(data)

    async def _reconnect(self):
        """尝试重新连接"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error(f"❌ 达到最大重连次数 ({self.max_reconnect_attempts})，停止重连")
            return

        self.reconnect_attempts += 1
        delay = self.reconnect_delay * self.reconnect_attempts

        logger.info(f"🔄 {delay}秒后尝试第{self.reconnect_attempts}次重连...")

        await asyncio.sleep(delay)

        if await self.connect():
            logger.info("✅ 重连成功")
        else:
            # 继续尝试重连
            if not self._stop_event.is_set():
                await self._reconnect()

    async def send_message(self, message_type: str, data: dict = None) -> bool:
        """发送消息到服务器"""
        if not self.is_connected or not self.websocket:
            logger.warning("⚠️ 未连接到后端WebSocket，无法发送消息")
            return False

        try:
            message = {
                "type": message_type,
                "timestamp": datetime.now().isoformat(),
                **(data or {})
            }

            await self.websocket.send(json.dumps(message))
            return True

        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            self.is_connected = False
            return False

    async def send_status_update(self, status: str, data: dict = None):
        """发送状态更新"""
        return await self.send_message("status_update", {
            "status": status,
            "data": data or {}
        })

    async def send_task_update(self, task_id: str, task_data: dict):
        """发送任务更新"""
        return await self.send_message("task_update", {
            "task_id": task_id,
            "data": task_data
        })

    async def send_log(self, level: str, message: str, module: str = "executor"):
        """发送日志"""
        return await self.send_message("log", {
            "level": level,
            "message": message,
            "module": module
        })

    async def send_device_update(self, devices: list):
        """发送设备更新"""
        return await self.send_message("device_update", {
            "devices": devices
        })

    async def _send_device_list(self):
        """获取并发送当前设备列表"""
        try:
            import subprocess
            result = subprocess.run(['adb', 'devices'],
                                 capture_output=True, text=True)

            devices = []
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]
                for line in lines:
                    if line.strip():
                        parts = line.split('\t')
                        if len(parts) >= 2:
                            devices.append({
                                'serial': parts[0],
                                'status': parts[1]
                            })

            # 发送设备列表更新
            await self.send_device_update(devices)
            logger.debug(f"📱 发送设备列表: {len(devices)} 个设备")

        except Exception as e:
            logger.error(f"获取设备列表失败: {e}")

    async def _handle_test_device(self, data: dict):
        """处理设备测试请求"""
        serial = data.get("serial")
        request_id = data.get("request_id")

        logger.info(f"🧪 收到设备测试请求: {serial}")

        try:
            import subprocess

            # 执行真实的设备测试
            test_results = {}

            # 1. 检查设备是否连接
            result = subprocess.run(
                ['adb', '-s', serial, 'shell', 'echo', 'test'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                test_results['connection'] = 'success'
                test_results['message'] = '设备连接正常'

                # 2. 获取设备信息
                try:
                    # 获取设备型号
                    model_result = subprocess.run(
                        ['adb', '-s', serial, 'shell', 'getprop', 'ro.product.model'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    test_results['model'] = model_result.stdout.strip() if model_result.returncode == 0 else 'Unknown'

                    # 获取Android版本
                    version_result = subprocess.run(
                        ['adb', '-s', serial, 'shell', 'getprop', 'ro.build.version.release'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    test_results['android_version'] = version_result.stdout.strip() if version_result.returncode == 0 else 'Unknown'

                    # 获取设备制造商
                    manufacturer_result = subprocess.run(
                        ['adb', '-s', serial, 'shell', 'getprop', 'ro.product.manufacturer'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    test_results['manufacturer'] = manufacturer_result.stdout.strip() if manufacturer_result.returncode == 0 else 'Unknown'

                except Exception as e:
                    test_results['info_error'] = str(e)

            else:
                test_results['connection'] = 'failed'
                test_results['message'] = '设备连接失败'
                test_results['error'] = result.stderr

            # 发送测试结果回后端
            await self.send_message("test_device_result", {
                "request_id": request_id,
                "serial": serial,
                "results": test_results
            })

            logger.info(f"✅ 设备测试完成: {serial} - {test_results.get('connection')}")

        except Exception as e:
            logger.error(f"❌ 设备测试失败: {e}")

            # 发送错误结果
            await self.send_message("test_device_result", {
                "request_id": request_id,
                "serial": serial,
                "results": {
                    'connection': 'error',
                    'message': f'测试出错: {str(e)}'
                }
            })

    async def _handle_test_element(self, data: dict):
        """处理元素测试请求"""
        device_serial = data.get("device_serial")
        locator_type = data.get("locator_type")
        locator_value = data.get("locator_value")
        request_id = data.get("request_id")

        logger.info(f"🔍 收到元素测试请求: {device_serial} - {locator_type}={locator_value}")

        try:
            from .ui_automator import UIAutomatorService

            # 创建UI Automator服务
            ui_service = UIAutomatorService(device_serial)

            # 如果是resource-id，尝试启动对应的应用
            target_package = None
            if locator_type == "resource-id" and ":" in locator_value:
                target_package = locator_value.split(":")[0]
                logger.info(f"📱 检测到目标包名: {target_package}")

                # 检查当前应用
                current_package = ui_service.get_current_package()
                logger.info(f"📱 当前应用: {current_package}")

                if current_package != target_package:
                    logger.info(f"🚀 正在启动应用: {target_package}")
                    if ui_service.start_app(target_package):
                        import time
                        time.sleep(2)  # 等待应用启动
                    else:
                        logger.warning(f"⚠ 应用启动失败，继续测试")

            # 查找元素
            result = None

            if locator_type == "resource-id":
                logger.info(f"🔍 通过resource-id查找: {locator_value}")
                result = ui_service.find_element_by_resource_id(locator_value)

            elif locator_type == "text":
                logger.info(f"🔍 通过text查找: {locator_value}")
                result = ui_service.find_element_by_text(locator_value)

            elif locator_type == "xpath":
                logger.info(f"🔍 通过xpath查找: {locator_value}")
                result = ui_service.find_element_by_xpath(locator_value)

            # 发送结果
            if result and result.get('found'):
                logger.info(f"✅ 找到元素: {locator_value}")
                if result.get('bounds'):
                    logger.info(f"   坐标: {result['bounds']}")

                await self.send_message("test_element_result", {
                    "request_id": request_id,
                    "result": {
                        "found": True,
                        "bounds": result.get('bounds')
                    }
                })
            else:
                logger.warning(f"❌ 未找到元素: {locator_value}")
                await self.send_message("test_element_result", {
                    "request_id": request_id,
                    "result": {
                        "found": False,
                        "error": result.get('error') if result else "未知错误"
                    }
                })

        except Exception as e:
            logger.error(f"❌ 元素测试失败: {e}")
            await self.send_message("test_element_result", {
                "request_id": request_id,
                "result": {
                    "found": False,
                    "error": str(e)
                }
            })

    async def _handle_get_dom(self, data: dict):
        """处理DOM获取请求"""
        serial = data.get("serial")
        request_id = data.get("request_id")

        logger.info(f"🌳 收到DOM获取请求: {serial}")

        try:
            from .ui_automator import UIAutomatorService

            ui_service = UIAutomatorService(serial)
            dom_xml = ui_service.dump_hierarchy()

            await self.send_message("dom_result", {
                "request_id": request_id,
                "serial": serial,
                "dom_xml": dom_xml,
                "timestamp": datetime.now().isoformat()
            })
            logger.info(f"✅ DOM获取成功: {serial}, XML长度: {len(dom_xml)}")

        except Exception as e:
            logger.error(f"❌ DOM获取失败: {e}")
            await self.send_message("dom_result", {
                "request_id": request_id,
                "serial": serial,
                "dom_xml": "",
                "error": str(e)
            })

    async def run_forever(self):
        """保持运行，直到停止事件被设置"""
        try:
            while not self._stop_event.is_set():
                await asyncio.sleep(1)

                # 定期发送心跳
                if self.is_connected:
                    await self.send_message("ping")

                    # 每30秒发送一次设备列表更新
                    # 获取当前时间戳的最后一位数字
                    current_time = asyncio.get_event_loop().time()
                    if int(current_time) % 30 < 2:  # 每30秒左右
                        await self._send_device_list()

        except asyncio.CancelledError:
            logger.info("🛑 WebSocket客户端被取消")
        finally:
            await self.disconnect()