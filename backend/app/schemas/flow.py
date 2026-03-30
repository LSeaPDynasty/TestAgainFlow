"""
Flow schemas
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class FlowStepSchema(BaseModel):
    """Flow step schema"""
    step_id: Optional[int] = Field(None, description="Step ID")
    sub_flow_id: Optional[int] = Field(None, description="Sub Flow ID (for nested flows)")
    order: int = Field(..., ge=1, description="Execution order")
    override_value: Optional[str] = Field(None, description="Override action_value")


class FlowBase(BaseModel):
    """Base flow fields"""
    name: str = Field(..., max_length=200, description="Flow name")
    description: Optional[str] = Field(None, description="Description")
    flow_type: str = Field("standard", description="Flow type")


class FlowCreate(FlowBase):
    """Flow creation schema"""
    requires: Optional[List[str]] = Field(default_factory=list, description="Required parameter names")
    default_params: Optional[Dict[str, Any]] = Field(None, description="Default parameter values")
    dsl_content: Optional[str] = Field(None, description="DSL content (for dsl type)")
    py_file: Optional[str] = Field(None, description="Python file path (for python type)")
    tag_ids: Optional[List[int]] = Field(default_factory=list, description="Tag IDs")
    steps: Optional[List[FlowStepSchema]] = Field(None, description="Steps (for standard type)")


class FlowUpdate(BaseModel):
    """Flow update schema"""
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    flow_type: Optional[str] = None
    requires: Optional[List[str]] = None
    default_params: Optional[Dict[str, Any]] = None
    dsl_content: Optional[str] = None
    py_file: Optional[str] = None
    tag_ids: Optional[List[int]] = None
    steps: Optional[List[FlowStepSchema]] = None


class FlowStepDetailSchema(BaseModel):
    """Flow step detail in response"""
    order: int
    step_id: Optional[int]
    sub_flow_id: Optional[int]
    step_name: Optional[str]
    sub_flow_name: Optional[str]
    action_type: Optional[str]
    screen_name: Optional[str]
    element_name: Optional[str]
    element_description: Optional[str] = None  # 新增：元素描述
    override_value: Optional[str]
    is_sub_flow: bool = False

    class Config:
        from_attributes = True


class TagSchema(BaseModel):
    """Tag schema"""
    id: int
    name: str

    class Config:
        from_attributes = True


class FlowResponse(FlowBase):
    """Flow response schema"""
    id: int
    step_count: int = Field(0, description="Number of steps")
    expanded_step_count: int = Field(0, description="Number of expanded steps (including called flows)")
    requires: List[str] = Field(default_factory=list)
    default_params: Optional[Dict[str, Any]] = None
    tags: List[TagSchema] = Field(default_factory=list)
    referenced_by_testcase_count: int = Field(0, description="Number of testcases using this flow")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FlowDetailResponse(FlowResponse):
    """Flow detail with steps"""
    dsl_content: Optional[str] = None
    py_file: Optional[str] = None
    steps: List[FlowStepDetailSchema] = Field(default_factory=list)
    expanded_count: int = Field(0, description="Total count after expanding calls")


class DslValidateRequest(BaseModel):
    """DSL validation request"""
    dsl_content: str = Field(..., description="DSL content to validate")


class ExpandedStepSchema(BaseModel):
    """Expanded step from DSL"""
    order: int
    type: str = Field(..., description="Step type: step, call, repeat, break_if")
    step_id: Optional[int] = None
    target: Optional[str] = Field(None, description="Target flow name for call type")


class DslValidateResponse(BaseModel):
    """DSL validation response"""
    valid: bool = Field(..., description="Whether DSL is valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    expanded_steps: List[ExpandedStepSchema] = Field(default_factory=list, description="Expanded steps")
    expanded_count: int = Field(0, description="Count of expanded steps")


class FlowDuplicateRequest(BaseModel):
    """Flow duplicate request"""
    new_name: str = Field(..., description="New flow name")
