"""Scheduled Job schemas."""
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ScheduledJobBase(BaseModel):
    """Base scheduled job fields"""
    name: str = Field(..., min_length=1, max_length=200, description="Job name")
    description: Optional[str] = Field(None, description="Job description")
    job_type: str = Field(..., pattern="^(testcase|suite)$", description="Job type: testcase or suite")
    target_id: int = Field(..., description="Target testcase or suite ID")
    cron_expression: str = Field(..., description="Cron expression (e.g., '0 9 * * *' for daily 9am)")
    device_serial: Optional[str] = Field(None, description="Device serial for execution")
    enabled: bool = Field(True, description="Job enabled flag")
    project_id: Optional[int] = Field(None, description="Project ID")


class ScheduledJobCreate(ScheduledJobBase):
    """Scheduled job creation schema"""
    pass


class ScheduledJobUpdate(BaseModel):
    """Scheduled job update schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    job_type: Optional[str] = Field(None, pattern="^(testcase|suite)$")
    target_id: Optional[int] = None
    cron_expression: Optional[str] = None
    device_serial: Optional[str] = None
    enabled: Optional[bool] = None
    project_id: Optional[int] = None


class ScheduledJobResponse(ScheduledJobBase):
    """Scheduled job response schema"""
    id: int
    status: str = Field(..., description="Job status")
    last_run_time: Optional[datetime] = None
    next_run_time: Optional[datetime] = None
    last_run_status: Optional[str] = None
    last_run_message: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JobRunRequest(BaseModel):
    """Request to manually run a scheduled job"""
    device_serial: str = Field(..., description="Device serial for execution")
