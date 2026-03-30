"""
Backend Log Handler
自动将日志发送到后端数据库
只发送任务执行期间的日志
"""
import logging
import asyncio
from typing import Optional
from contextvars import ContextVar

# 使用 ContextVar 存储当前任务 ID，这样可以在线程/异步上下文中安全传递
current_task_id: ContextVar[Optional[str]] = ContextVar('current_task_id', default=None)

logger = logging.getLogger(__name__)


class BackendLogHandler(logging.Handler):
    """
    自定义日志处理器，将日志发送到后端数据库

    日志层级：
    - DEBUG: 详细操作细节（元素定位、参数值）
    - INFO: 主要步骤信息（步骤名称、流程名称、用例名称）
    - WARNING: 警告信息
    - ERROR: 错误信息
    """

    def __init__(self, task_queue_client):
        super().__init__()
        self.task_queue_client = task_queue_client
        self.loop = asyncio.get_event_loop()

    def emit(self, record: logging.LogRecord) -> None:
        """
        处理日志记录

        Args:
            record: Python logging 记录
        """
        try:
            # 获取当前任务 ID
            task_id = current_task_id.get()

            if not task_id:
                # 如果没有任务 ID，说明不在任务执行期间，不发送到后端
                return

            # 过滤掉不需要发送的日志
            # 1. 跳过执行引擎本身的高层日志（避免重复）
            if 'executor' in record.name and any(keyword in record.getMessage() for keyword in [
                '开始执行任务',
                '任务完成',
                '任务失败',
                '执行引擎',
                '工作线程',
            ]):
                return

            # 2. 跳过设备和连接相关的系统日志
            if any(name in record.name for name in [
                'device_discovery',
                'websocket_client',
                'task_queue_client',
            ]):
                return

            # 3. 根据模块和级别决定是否发送
            should_send = False

            # 所有 WARNING 及以上级别的日志都发送
            if record.levelno >= logging.WARNING:
                should_send = True
            # 特定模块的 INFO 和 DEBUG 日志也发送
            elif any(module in record.name for module in [
                'ui_automator',      # UIAutomator 操作（DEBUG级）
                'adb_service',       # ADB 操作（DEBUG级）
                'step_executor',     # 步骤执行（INFO级）
                'executor',          # 流程和用例（INFO级）
            ]):
                should_send = True

            if not should_send:
                return

            # 转换日志级别
            level_map = {
                logging.DEBUG: "DEBUG",
                logging.INFO: "INFO",
                logging.WARNING: "WARNING",
                logging.ERROR: "ERROR",
                logging.CRITICAL: "ERROR",
            }
            level = level_map.get(record.levelno, "INFO")

            # 格式化日志消息
            message = self.format(record)

            # 创建异步任务发送日志
            asyncio.create_task(self._send_log(task_id, level, message))

        except Exception:
            # 日志处理器本身不应该抛出异常
            self.handleError(record)

    async def _send_log(self, task_id: str, level: str, message: str):
        """异步发送日志到后端"""
        try:
            await self.task_queue_client.send_task_log(task_id, {
                "level": level,
                "message": message,
                "timestamp": asyncio.get_event_loop().time()
            })
        except Exception as e:
            # 发送失败也不应该影响主流程
            logger.debug(f"Failed to send log to backend: {e}")


def set_current_task_id(task_id: str):
    """设置当前任务 ID"""
    current_task_id.set(task_id)


def get_current_task_id() -> Optional[str]:
    """获取当前任务 ID"""
    return current_task_id.get()


def clear_current_task_id():
    """清除当前任务 ID"""
    current_task_id.set(None)
