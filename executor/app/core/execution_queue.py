"""
Execution Queue
Manages the queue of pending execution tasks
"""
import asyncio
from typing import Optional
from .task import ExecutionTask


class ExecutionQueue:
    """
    Async queue for managing execution tasks
    """

    def __init__(self, max_size: int = 10):
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=max_size)
        self.max_size = max_size

    async def put(self, task: ExecutionTask):
        """Add task to queue"""
        await self.queue.put(task)

    async def get(self) -> ExecutionTask:
        """Get next task from queue"""
        return await self.queue.get()

    def qsize(self) -> int:
        """Get current queue size"""
        return self.queue.qsize()

    def empty(self) -> bool:
        """Check if queue is empty"""
        return self.queue.empty()

    def full(self) -> bool:
        """Check if queue is full"""
        return self.queue.full()

    async def clear(self):
        """Clear all tasks from queue"""
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except asyncio.QueueEmpty:
                break
