"""
Suite schemas
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class SuiteTestcaseSchema(BaseModel):
    """Suite testcase association"""
    testcase_id: int = Field(..., description="Testcase ID")
    testcase_name: Optional[str] = Field(None, description="Testcase name")
    order: int = Field(..., ge=1, description="Execution order")
    enabled: bool = Field(True, description="Enabled flag")


class SuiteBase(BaseModel):
    """Base suite fields"""
    name: str = Field(..., min_length=1, max_length=200, description="Suite name")
    description: Optional[str] = Field(None, description="Description")
    priority: str = Field("P1", pattern="^(P0|P1|P2|P3)$", description="Priority")
    enabled: bool = Field(True, description="Enabled flag")


class SuiteCreate(SuiteBase):
    """Suite creation schema"""
    testcases: Optional[List[SuiteTestcaseSchema]] = Field(None, min_length=1, description="Testcase list")


class SuiteUpdate(BaseModel):
    """Suite update schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    priority: Optional[str] = Field(None, pattern="^(P0|P1|P2|P3)$")
    enabled: Optional[bool] = None
    testcases: Optional[List[SuiteTestcaseSchema]] = None


class SuiteResponse(SuiteBase):
    """Suite response schema"""
    id: int
    testcase_count: int = Field(0, description="Number of testcases")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SuiteDetailResponse(SuiteResponse):
    """Suite detail with testcases"""
    testcases: List[SuiteTestcaseSchema] = Field(default_factory=list)


class SuiteToggleRequest(BaseModel):
    """Suite toggle request"""
    enabled: bool = Field(..., description="Enabled state")
