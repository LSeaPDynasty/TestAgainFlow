"""Scheduler schemas."""
from pydantic import BaseModel, Field


class SchedulerConfigResponse(BaseModel):
    enabled: bool
    max_inflight_tasks: int = Field(..., ge=1, le=100)
    default_priority: int = Field(..., ge=1, le=10)
    queue_strategy: str


class SchedulerConfigUpdate(BaseModel):
    enabled: bool | None = None
    max_inflight_tasks: int | None = Field(None, ge=1, le=100)
    default_priority: int | None = Field(None, ge=1, le=10)
    queue_strategy: str | None = None
