"""WebSocket event schemas."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class WsErrorEvent(BaseModel):
    """Structured websocket error payload."""

    type: str = "error"
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")


class WsTaskStatusUpdateEvent(BaseModel):
    """Task status update broadcast payload."""

    type: str = "task_status_update"
    task_id: str
    status: str
    executor_id: str


class WsTaskLogEvent(BaseModel):
    """Task log broadcast payload."""

    type: str = "task_log"
    task_id: str
    log: Dict[str, Any]
    executor_id: str


class WsTaskScreenshotsEvent(BaseModel):
    """Task screenshots broadcast payload."""

    type: str = "task_screenshots"
    task_id: str
    screenshots: List[Dict[str, Any]]


class WsTaskCompleteEvent(BaseModel):
    """Task completion broadcast payload."""

    type: str = "task_complete"
    task_id: str
    result: Optional[str] = None
    executor_id: str


class WsNewTaskEvent(BaseModel):
    """New queued task push payload."""

    type: str = "new_task"
    task_id: str
    task_data: Dict[str, Any]


class WsTaskDataEvent(BaseModel):
    """Task data response payload."""

    type: str = "task_data"
    task_id: str
    task_data: Optional[Dict[str, Any]] = None


class WsConnectedEvent(BaseModel):
    """Generic websocket connected payload."""

    type: str = "connected"
    message: str
    executor_id: Optional[str] = None
    timestamp: Optional[str] = None
    server_info: Optional[Dict[str, Any]] = None


class WsQueueStatusEvent(BaseModel):
    """Queue status payload."""

    type: str = "queue_status"
    queue_size: int
    status: str


class WsRegisteredEvent(BaseModel):
    """Executor registration ack payload."""

    type: str = "registered"
    executor_id: str
    capabilities: Dict[str, Any] = Field(default_factory=dict)


class WsPongEvent(BaseModel):
    """Ping response payload."""

    type: str = "pong"
    timestamp: Optional[str] = None


class WsSubscribedEvent(BaseModel):
    """Subscription ack payload."""

    type: str = "subscribed"
    timestamp: str
    client_type: str


class WsCurrentStatusEvent(BaseModel):
    """Current status payload."""

    type: str = "current_status"
    timestamp: str
    connection_count: int
