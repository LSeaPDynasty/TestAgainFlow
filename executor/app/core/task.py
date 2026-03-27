"""
Execution Task Model
"""
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List
import asyncio


class TaskStatus(str, Enum):
    """Task status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskResult(str, Enum):
    """Task execution result"""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class ExecutionType(str):
    """Execution type"""
    STEP = "step"
    FLOW = "flow"
    TESTCASE = "testcase"
    SUITE = "suite"
    TEST_PLAN = "test_plan"


class ExecutionTask:
    """
    Represents a single execution task
    """

    def __init__(
        self,
        task_id: str,
        execution_type: str,
        target_id: int,
        device_serial: str,
        config: Dict[str, Any]
    ):
        self.task_id = task_id
        self.execution_type = execution_type
        self.target_id = target_id
        self.device_serial = device_serial
        self.config = config

        # Database reference
        self.execution_id: Optional[int] = None

        # Status
        self.status = TaskStatus.PENDING
        self.result: Optional[TaskResult] = None
        self.error: Optional[str] = None

        # Progress
        self.progress = 0
        self.current_step = 0
        self.total_steps = 0

        # Timing
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None

        # Logs
        self.logs: List[str] = []

        # Cancellation
        self._cancel_event = asyncio.Event()

    @property
    def duration(self) -> Optional[float]:
        """Get task duration in seconds"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    async def start(self):
        """Mark task as started"""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now()
        self.log(f"▶️  Task started: {self.task_id}")

    async def complete(self, result: TaskResult):
        """Mark task as completed"""
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.completed_at = datetime.now()
        self.progress = 100
        self.log(f"✅ Task completed: {self.task_id} -> {result.value}")

    async def fail(self, error: str):
        """Mark task as failed"""
        self.status = TaskStatus.FAILED
        self.result = TaskResult.ERROR
        self.error = error
        self.completed_at = datetime.now()
        self.log(f"❌ Task failed: {self.task_id} - {error}")

    async def cancel(self):
        """Cancel the task"""
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.now()
        self._cancel_event.set()
        self.log(f"🚫 Task cancelled: {self.task_id}")

    def is_cancelled(self) -> bool:
        """Check if task is cancelled"""
        return self._cancel_event.is_set()

    def log(self, message: str):
        """Add log message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] {message}")

    def update_progress(self, current: int, total: int):
        """Update task progress"""
        self.current_step = current
        self.total_steps = total
        if total > 0:
            self.progress = int((current / total) * 100)
        else:
            self.progress = 0
