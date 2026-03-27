"""
TestPlan schemas
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class TestPlanSuiteSchema(BaseModel):
    """Test plan suite association"""
    suite_id: int = Field(..., description="Suite ID")
    suite_name: Optional[str] = Field(None, description="Suite name")
    order: int = Field(..., ge=1, description="Execution order in the plan")
    enabled: bool = Field(True, description="Enabled flag")
    execution_config: Optional[Dict[str, Any]] = Field(None, description="Execution configuration")


class TestPlanTestcaseOrderSchema(BaseModel):
    """Testcase order in test plan suite"""
    testcase_id: int = Field(..., description="Testcase ID")
    testcase_name: Optional[str] = Field(None, description="Testcase name")
    order_index: int = Field(..., ge=0, description="Execution order")
    priority: Optional[str] = Field(None, description="Testcase priority")

    class Config:
        from_attributes = True


class TestPlanBase(BaseModel):
    """Base test plan fields"""
    name: str = Field(..., min_length=1, max_length=200, description="Test plan name")
    description: Optional[str] = Field(None, description="Description")
    execution_strategy: str = Field("sequential", pattern="^(sequential|parallel)$", description="Execution strategy")
    max_parallel_tasks: int = Field(1, ge=1, le=10, description="Max parallel tasks")
    enabled: bool = Field(True, description="Enabled flag")


class TestPlanCreate(TestPlanBase):
    """Test plan creation schema"""
    project_id: Optional[int] = Field(None, description="Project ID")
    suites: Optional[List[TestPlanSuiteSchema]] = Field(None, min_length=1, description="List of suites")


class TestPlanUpdate(BaseModel):
    """Test plan update schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    execution_strategy: Optional[str] = Field(None, pattern="^(sequential|parallel)$")
    max_parallel_tasks: Optional[int] = Field(None, ge=1, le=10)
    enabled: Optional[bool] = None
    suites: Optional[List[TestPlanSuiteSchema]] = None


class TestPlanSuiteDetailSchema(BaseModel):
    """Test plan suite with testcases"""
    id: int = Field(..., description="Test plan suite ID")
    test_plan_id: int = Field(..., description="Test plan ID")
    suite_id: int = Field(..., description="Suite ID")
    suite_name: Optional[str] = Field(None, description="Suite name")
    order_index: int = Field(..., description="Execution order")
    enabled: bool = Field(..., description="Enabled flag")
    testcases: List[TestPlanTestcaseOrderSchema] = Field(default_factory=list, description="Testcases in order")


class TestPlanResponse(TestPlanBase):
    """Test plan response schema"""
    id: int
    project_id: Optional[int] = None
    suite_count: int = Field(0, description="Number of suites")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TestPlanDetailResponse(TestPlanResponse):
    """Test plan detail with suites"""
    suites: List[TestPlanSuiteDetailSchema] = Field(default_factory=list, description="Suites in the plan")


class TestPlanToggleRequest(BaseModel):
    """Test plan toggle request"""
    enabled: bool = Field(..., description="Enabled state")


class TestPlanAddSuitesRequest(BaseModel):
    """Add suites to test plan"""
    suite_ids: List[int] = Field(..., min_length=1, description="Suite IDs to add")


class TestPlanRemoveSuitesRequest(BaseModel):
    """Remove suites from test plan"""
    suite_ids: List[int] = Field(..., min_length=1, description="Suite IDs to remove")


class TestPlanReorderSuitesRequest(BaseModel):
    """Reorder suites in test plan"""
    suites: List[TestPlanSuiteSchema] = Field(..., min_length=1, description="Suites with new order")


class TestPlanSetTestcaseOrderRequest(BaseModel):
    """Set testcase order for a suite"""
    testcase_orders: List[TestPlanTestcaseOrderSchema] = Field(..., min_length=1, description="Testcase orders")


class TestPlanExecuteRequest(BaseModel):
    """Execute test plan request"""
    platform: str = Field(..., description="Execution platform (android/ios/web)")
    device_serial: Optional[str] = Field(None, description="Device serial for execution")
    profile_id: Optional[int] = Field(None, description="Profile ID for execution")
    timeout: Optional[int] = Field(None, ge=1, description="Execution timeout in seconds")
    extra_args: Optional[Dict[str, Any]] = Field(None, description="Extra execution arguments")
    priority: Optional[str] = Field("normal", description="Execution priority")


class TestPlanExecuteResponse(BaseModel):
    """Test plan execution response"""
    task_id: str = Field(..., description="Execution task ID")
    runs_count: int = Field(..., description="Number of runs created")
