"""
Testcase schemas
"""
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class TestcaseFlowSchema(BaseModel):
    """Testcase flow association"""
    flow_id: int = Field(..., description="Flow ID")
    order: int = Field(..., ge=1, description="Execution order")
    enabled: bool = Field(True, description="Enabled flag")
    params: Optional[Dict[str, Any]] = Field(None, description="Override parameters")


class InlineStepSchema(BaseModel):
    """Inline step schema"""
    step_id: int = Field(..., description="Step ID")
    order: int = Field(..., ge=1, description="Execution order")
    override_value: Optional[str] = Field(None, description="Override action_value")


class TestcaseItemSchema(BaseModel):
    """Testcase item schema - unified flow/step mixed ordering"""
    item_type: Literal['flow', 'step'] = Field(..., description="Item type: flow or step")
    flow_id: Optional[int] = Field(None, description="Flow ID (required when item_type=flow)")
    step_id: Optional[int] = Field(None, description="Step ID (required when item_type=step)")
    order_index: int = Field(..., ge=1, description="Execution order (1-based)")
    enabled: bool = Field(True, description="Enabled flag")
    continue_on_error: Optional[bool] = Field(None, description="Continue execution on error (overrides item-level setting)")
    params: Optional[Dict[str, Any]] = Field(None, description="Override parameters for flow/step")

    class Config:
        json_schema_extra = {
            "example": {
                "item_type": "flow",
                "flow_id": 101,
                "order_index": 1,
                "enabled": True,
                "continue_on_error": False,
                "params": None
            }
        }


class TestcaseItemUpdateSchema(BaseModel):
    """Testcase items bulk update schema"""
    items: List[TestcaseItemSchema] = Field(..., description="List of testcase items (will replace all existing items)")


class TestcaseItemResponseSchema(BaseModel):
    """Testcase item response with expanded flow/step info"""
    id: int
    testcase_id: int
    item_type: str
    flow_id: Optional[int] = None
    step_id: Optional[int] = None
    order_index: int
    enabled: bool
    continue_on_error: Optional[bool] = None
    params: Optional[Dict[str, Any]] = None
    # Expanded fields
    flow_name: Optional[str] = None
    step_name: Optional[str] = None
    step_action_type: Optional[str] = None

    class Config:
        from_attributes = True


class TestcaseBase(BaseModel):
    """Base testcase fields"""
    name: str = Field(..., max_length=200, description="Testcase name")
    description: Optional[str] = Field(None, description="Description")
    priority: str = Field("P2", description="Priority: P0, P1, P2, P3")
    timeout: int = Field(120, ge=1, le=3600, description="Timeout in seconds")


class TestcaseCreate(TestcaseBase):
    """Testcase creation schema"""
    params: Optional[Dict[str, Any]] = Field(None, description="Testcase-level parameters")
    tag_ids: Optional[List[int]] = Field(default_factory=list, description="Tag IDs")
    setup_flows: Optional[List[TestcaseFlowSchema]] = Field(default_factory=list)
    main_flows: Optional[List[TestcaseFlowSchema]] = Field(None, description="Main flows, at least one")
    teardown_flows: Optional[List[TestcaseFlowSchema]] = Field(default_factory=list)
    inline_steps: Optional[List[InlineStepSchema]] = Field(default_factory=list)


class TestcaseUpdate(BaseModel):
    """Testcase update schema"""
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    priority: Optional[str] = None
    timeout: Optional[int] = Field(None, ge=1, le=3600)
    params: Optional[Dict[str, Any]] = None
    tag_ids: Optional[List[int]] = None
    setup_flows: Optional[List[TestcaseFlowSchema]] = None
    main_flows: Optional[List[TestcaseFlowSchema]] = None
    teardown_flows: Optional[List[TestcaseFlowSchema]] = None
    inline_steps: Optional[List[InlineStepSchema]] = None


class TestcaseFlowDetailSchema(BaseModel):
    """Testcase flow detail"""
    order: int
    flow_id: int
    flow_name: str
    enabled: bool
    params: Optional[Dict[str, Any]]
    requires: List[str] = Field(default_factory=list, description="Required parameters")

    class Config:
        from_attributes = True


class TagSchema(BaseModel):
    """Tag schema"""
    id: int
    name: str

    class Config:
        from_attributes = True


class TestcaseResponse(TestcaseBase):
    """Testcase response schema"""
    id: int
    params: Optional[Dict[str, Any]] = None
    tags: List[TagSchema] = Field(default_factory=list)
    setup_flow_count: int = Field(0, description="Number of setup flows")
    main_flow_count: int = Field(0, description="Number of main flows")
    teardown_flow_count: int = Field(0, description="Number of teardown flows")
    step_count: int = Field(0, description="Total step count")
    testcase_item_count: int = Field(0, description="Number of testcase items (mixed flow/step)")
    estimated_duration: int = Field(0, description="Estimated duration in seconds")
    suite_count: int = Field(0, description="Number of suites referencing this testcase")
    last_run_result: Optional[str] = Field(None, description="Last run result")
    last_run_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TestcaseDetailResponse(TestcaseResponse):
    """Testcase detail with flows"""
    setup_flows: List[TestcaseFlowDetailSchema] = Field(default_factory=list)
    main_flows: List[TestcaseFlowDetailSchema] = Field(default_factory=list)
    teardown_flows: List[TestcaseFlowDetailSchema] = Field(default_factory=list)
    inline_steps: List[InlineStepSchema] = Field(default_factory=list)
    testcase_items: List[TestcaseItemResponseSchema] = Field(default_factory=list, description="Unified execution sequence (mixed flow/step)")


class DependencyChainStepSchema(BaseModel):
    """Step in dependency chain"""
    order: int
    step_id: int
    step_name: str
    action_type: str
    screen_name: Optional[str]
    element_name: Optional[str]


class DependencyChainFlowSchema(BaseModel):
    """Flow in dependency chain"""
    flow_id: int
    flow_name: str
    steps: List[DependencyChainStepSchema] = Field(default_factory=list)
    requires: List[str] = Field(default_factory=list)


class DependencyChainResponse(BaseModel):
    """Dependency chain response"""
    testcase_id: int
    testcase_name: str
    setup_flows: List[DependencyChainFlowSchema] = Field(default_factory=list)
    main_flows: List[DependencyChainFlowSchema] = Field(default_factory=list)
    teardown_flows: List[DependencyChainFlowSchema] = Field(default_factory=list)
    all_steps: List[DependencyChainStepSchema] = Field(default_factory=list, description="All steps flattened")
    required_profiles: List[str] = Field(default_factory=list, description="Required profile names")


class TestcaseDuplicateRequest(BaseModel):
    """Testcase duplicate request"""
    new_name: str = Field(..., description="New testcase name")
