"""
Impact analysis schemas
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class ImpactItem(BaseModel):
    """Impact item"""
    id: int
    name: str


class ImpactResponse(BaseModel):
    """Impact analysis response"""
    element_id: Optional[int] = None
    element_name: Optional[str] = None
    screen_id: Optional[int] = None
    screen_name: Optional[str] = None
    step_id: Optional[int] = None
    step_name: Optional[str] = None
    flow_id: Optional[int] = None
    flow_name: Optional[str] = None
    affected_steps: List[ImpactItem] = Field(default_factory=list)
    affected_flows: List[ImpactItem] = Field(default_factory=list)
    affected_testcases: List[ImpactItem] = Field(default_factory=list)
    total_affected: int = Field(0, description="Total affected count")


class HealthCheckRequest(BaseModel):
    """Health check request"""
    device_serial: str = Field(..., description="Device serial")
    screen_ids: Optional[List[int]] = Field(None, description="Screen IDs to check, all if None")


class HealthCheckResponse(BaseModel):
    """Health check response"""
    task_id: str = Field(..., description="Health check task ID")
    status: str = Field(..., description="Status: running, completed")
