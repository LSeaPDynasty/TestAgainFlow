"""
Run schemas
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class RunCreate(BaseModel):
    """Run creation request"""
    type: str = Field(..., description="Run type")
    target_ids: List[int] = Field(..., description="Target IDs (testcase IDs or suite IDs)")
    profile_id: Optional[int] = Field(None, description="Profile ID")
    device_serial: Optional[str] = Field(None, description="Device serial")
    platform: str = Field("android", description="Execution platform: android/ios/web")
    timeout: Optional[int] = Field(120, ge=1, description="Timeout in seconds")
    extra_args: Optional[str] = Field(None, description="Extra pytest arguments")
    priority: Optional[int] = Field(None, ge=1, le=10, description="Task priority (1 highest)")


class BatchRunCreate(BaseModel):
    """Batch run creation request."""
    type: str = Field(..., description="Run type")
    target_ids: List[int] = Field(..., description="Target IDs")
    profile_id: Optional[int] = Field(None, description="Profile ID")
    device_serial: Optional[str] = Field(None, description="Device serial")
    platform: str = Field("android", description="Execution platform: android/ios/web")
    timeout: Optional[int] = Field(120, ge=1, description="Timeout in seconds")
    extra_args: Optional[str] = Field(None, description="Extra pytest arguments")
    mode: str = Field("parallel", description="Batch mode: parallel or sequential")
    priority: Optional[int] = Field(None, ge=1, le=10, description="Task priority (1 highest)")


class RunTargetSchema(BaseModel):
    """Run target info"""
    id: int
    name: str


class RunResponse(BaseModel):
    """Run response schema"""
    task_id: str = Field(..., description="Task ID")
    type: str = Field(..., description="Run type")
    targets: List[RunTargetSchema] = Field(default_factory=list, description="Target list")
    status: str = Field(..., description="Run status")
    cmd: Optional[List[str]] = Field(None, description="Command line")
    started_at: Optional[datetime] = None


class RunStatusResponse(BaseModel):
    """Run status response"""
    task_id: str
    status: str
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    returncode: Optional[int]
    result: Optional[str]
    progress: int = Field(0, description="Progress percentage (0-100)")


class LogEvent(BaseModel):
    """Log event for SSE"""
    type: str = Field(..., description="Event type: log, done, cancelled, timeout")
    text: Optional[str] = Field(None, description="Log text")
    timestamp: Optional[float] = None
    returncode: Optional[int] = None
    result: Optional[str] = None
    duration: Optional[float] = None


class ScreenshotSchema(BaseModel):
    """Screenshot info"""
    name: str = Field(..., description="Screenshot name")
    label: str = Field(..., description="Step label")
    path: str = Field(..., description="File path")
    url: str = Field(..., description="Download URL")
    taken_at: datetime


class ScreenshotsResponse(BaseModel):
    """Screenshots list response"""
    screenshots: List[ScreenshotSchema] = Field(default_factory=list)


class BatchRunResponse(BaseModel):
    """Batch run response."""
    task_ids: List[str] = Field(default_factory=list)
    mode: str = Field(..., description="Batch mode")
