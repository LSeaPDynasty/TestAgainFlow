"""
Log Service - 统一日志发送服务
提取重复的日志发送逻辑
"""
import asyncio
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class LogService:
    """日志发送服务 - 统一处理日志发送到后端"""

    def __init__(self, task_queue_client):
        """
        Args:
            task_queue_client: TaskQueueClient实例
        """
        self.task_queue_client = task_queue_client

    async def info(self, task_id: str, message: str, extra: Dict[str, Any] = None):
        """发送INFO级别日志"""
        await self._send_log(task_id, "INFO", message, extra)

    async def error(self, task_id: str, message: str, extra: Dict[str, Any] = None):
        """发送ERROR级别日志"""
        await self._send_log(task_id, "ERROR", message, extra)

    async def warning(self, task_id: str, message: str, extra: Dict[str, Any] = None):
        """发送WARNING级别日志"""
        await self._send_log(task_id, "WARNING", message, extra)

    async def debug(self, task_id: str, message: str, extra: Dict[str, Any] = None):
        """发送DEBUG级别日志"""
        await self._send_log(task_id, "DEBUG", message, extra)

    async def _send_log(self, task_id: str, level: str, message: str, extra: Dict[str, Any] = None):
        """内部方法：发送日志到后端"""
        try:
            log_data = {
                "level": level,
                "message": message,
                "timestamp": asyncio.get_event_loop().time()
            }
            if extra:
                log_data.update(extra)

            await self.task_queue_client.send_task_log(task_id, log_data)
        except Exception as e:
            logger.error(f"Failed to send log: {e}")

    async def send_batch_logs(self, task_id: str, logs: list):
        """批量发送日志（优化性能）"""
        for log in logs:
            await self._send_log(task_id, log.get("level", "INFO"), log.get("message", ""))
