"""
任务队列客户端
连接到后端WebSocket，从队列获取任务
"""
import asyncio
import websockets
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class TaskQueueClient:
    """任务队列客户端"""

    def __init__(self, backend_url: str = "ws://localhost:8000"):
        self.backend_url = backend_url
        self.ws_url = f"{backend_url}/ws/task-queue"
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.is_connected = False
        self._stop_event = asyncio.Event()
        self.current_task_id: Optional[str] = None
        self.current_task_data: Optional[Dict[str, Any]] = None
        self.reconnect_delay = 5  # 重连延迟（秒）
        self.max_reconnect_attempts = 100  # 最大重连次数（设为无限重连）
        self.reconnect_attempts = 0

    async def connect(self) -> bool:
        """连接到任务队列WebSocket"""
        try:
            logger.info(f"🔗 连接到任务队列: {self.ws_url}")

            self.websocket = await websockets.connect(
                self.ws_url,
                ping_interval=20,
                ping_timeout=20,
                close_timeout=10
            )

            self.is_connected = True
            self.reconnect_attempts = 0  # 重置重连计数
            logger.info("✅ 已连接到任务队列")

            # 启动消息接收循环
            asyncio.create_task(self._receive_messages())

            # 注册执行引擎
            await self.send_message("register", {
                "capabilities": {
                    "max_concurrent_tasks": 5,
                    "supported_types": ["testcase", "suite"]
                }
            })

            return True

        except Exception as e:
            logger.error(f"❌ 连接任务队列失败: {e}")
            self.is_connected = False
            return False

    async def disconnect(self):
        """断开连接"""
        self._stop_event.set()

        if self.websocket:
            try:
                await self.websocket.close()
                logger.info("🔌 任务队列连接已关闭")
            except Exception as e:
                logger.error(f"关闭连接时出错: {e}")

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
            logger.warning("⚠️ 任务队列连接已关闭")
            self.is_connected = False

            # 尝试重连
            if not self._stop_event.is_set():
                await self._reconnect()

        except Exception as e:
            logger.error(f"接收消息时出错: {e}")
            self.is_connected = False

            # 尝试重连
            if not self._stop_event.is_set():
                await self._reconnect()

    async def _process_message(self, data: dict):
        """处理收到的消息"""
        message_type = data.get("type")

        if message_type == "connected":
            logger.info(f"🎉 {data.get('message')}")
        elif message_type == "queue_status":
            logger.info(f"📊 队列状态: {data.get('queue_size')} 个任务")
        elif message_type == "new_task":
            # 收到新任务
            task_id = data.get("task_id")
            task_data = data.get("task_data")
            logger.info(f"📥 收到新任务: {task_id}")

            # 保存任务信息
            self.current_task_id = task_id
            self.current_task_data = task_data

        elif message_type == "pong":
            logger.debug("💓 收到心跳响应")
        elif message_type == "error":
            logger.error(f"❌ 服务器错误: {data.get('message')}")

    async def _reconnect(self):
        """尝试重新连接"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error(f"❌ 达到最大重连次数 ({self.max_reconnect_attempts})，停止重连")
            return

        self.reconnect_attempts += 1
        delay = self.reconnect_delay * min(self.reconnect_attempts, 10)  # 最多延迟50秒

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
            logger.warning("⚠️ 未连接到任务队列，无法发送消息")
            return False

        try:
            message = {
                "type": message_type,
                **(data or {})
            }

            await self.websocket.send(json.dumps(message))
            return True

        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            self.is_connected = False
            return False

    async def send_task_status(self, task_id: str, status: str, data: dict = None):
        """发送任务状态更新"""
        return await self.send_message("task_status", {
            "task_id": task_id,
            "status": status,
            "data": data or {}
        })

    async def send_task_log(self, task_id: str, log: dict):
        """发送任务日志"""
        return await self.send_message("task_log", {
            "task_id": task_id,
            "log": log
        })

    async def send_task_complete(self, task_id: str, result: str):
        """发送任务完成消息"""
        return await self.send_message("task_complete", {
            "task_id": task_id,
            "result": result
        })

    async def wait_for_task(self, timeout: float = 60.0) -> Optional[Dict[str, Any]]:
        """等待接收任务（阻塞）"""
        start_time = asyncio.get_event_loop().time()

        while not self._stop_event.is_set():
            if self.current_task_id and self.current_task_data:
                # 有新任务
                task_info = {
                    "task_id": self.current_task_id,
                    "task_data": self.current_task_data
                }

                # 清空当前任务
                self.current_task_id = None
                self.current_task_data = None

                return task_info

            # 检查超时
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed >= timeout:
                return None

            await asyncio.sleep(0.5)

        return None

    async def run_forever(self):
        """保持运行，直到停止事件被设置"""
        try:
            while not self._stop_event.is_set():
                await asyncio.sleep(1)

                # 检查连接状态，如果断开则尝试重连
                if not self.is_connected and not self._stop_event.is_set():
                    logger.warning("⚠️ 检测到连接断开，尝试重连...")
                    await self._reconnect()

                # 定期发送心跳
                if self.is_connected:
                    try:
                        await self.send_message("ping", {"timestamp": asyncio.get_event_loop().time()})
                    except Exception as e:
                        logger.error(f"发送心跳失败: {e}")
                        self.is_connected = False

        except asyncio.CancelledError:
            logger.info("🛑 任务队列客户端被取消")
        finally:
            await self.disconnect()
