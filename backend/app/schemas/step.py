"""
Step schemas
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class AssertConfigSchema(BaseModel):
    """Assertion configuration"""
    type: str = Field(..., description="Assert type: text, exists, not_exists, color")
    expected: Optional[str] = Field(None, description="Expected value")
    on_fail: str = Field("stop", description="Failure strategy")


class StepBase(BaseModel):
    """Base step fields"""
    name: str = Field(..., min_length=1, max_length=200, description="Step name")
    description: Optional[str] = Field(None, description="Description")
    screen_id: int = Field(..., description="Associated screen ID")
    action_type: str = Field(..., description="Action type: click, input, assert_text, etc.")
    element_id: Optional[int] = Field(None, description="Target element ID")
    flow_id: Optional[int] = Field(None, description="Target flow ID (for call action type)")
    action_value: Optional[str] = Field(None, description="Action value, supports {{variable}}")
    assert_config: Optional[AssertConfigSchema] = Field(None, description="Assertion config")
    wait_after_ms: int = Field(0, ge=0, description="Wait time after step (ms)")
    continue_on_error: bool = Field(False, description="Continue execution on error")


class StepCreate(StepBase):
    """Step creation schema"""
    tag_ids: Optional[List[int]] = Field(default_factory=list, description="Tag IDs")


class StepUpdate(BaseModel):
    """Step update schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    screen_id: Optional[int] = None
    action_type: Optional[str] = None
    element_id: Optional[int] = None
    flow_id: Optional[int] = None
    action_value: Optional[str] = None
    assert_config: Optional[AssertConfigSchema] = None
    wait_after_ms: Optional[int] = Field(None, ge=0)
    continue_on_error: Optional[bool] = None
    tag_ids: Optional[List[int]] = None


class TagSchema(BaseModel):
    """Tag schema"""
    id: int
    name: str

    class Config:
        from_attributes = True


class StepResponse(StepBase):
    """Step response schema"""
    id: int
    screen_name: str
    element_name: Optional[str]
    tags: List[TagSchema] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
