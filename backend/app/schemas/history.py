"""
History schemas
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class HistoryResponse(BaseModel):
    """History record response"""
    id: int
    task_id: str
    testcase_id: int
    testcase_name: str
    result: str
    returncode: Optional[int]
    duration: Optional[float]
    profile_id: Optional[int]
    profile_name: Optional[str]
    device_serial: Optional[str]
    device_name: Optional[str]
    has_screenshots: bool
    started_at: Optional[datetime]
    finished_at: Optional[datetime]

    class Config:
        from_attributes = True


class DailyTrendSchema(BaseModel):
    """Daily trend data"""
    date: str = Field(..., description="Date string")
    pass_count: int = Field(..., description="Pass count")
    fail: int = Field(..., description="Fail count")


class TopFailedSchema(BaseModel):
    """Top failed testcase"""
    testcase_id: int
    testcase_name: str
    fail_count: int


class HistoryStats(BaseModel):
    """History statistics"""
    total_runs: int
    pass_count: int
    fail_count: int
    pass_rate: float
    avg_duration: Optional[float]
    daily_trend: List[DailyTrendSchema] = Field(default_factory=list)
    top_failed: List[TopFailedSchema] = Field(default_factory=list)
