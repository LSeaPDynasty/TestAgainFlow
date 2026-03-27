"""
Executor and Action Type schemas
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ============ Action Type Schemas ============

class ActionTypeBase(BaseModel):
    """操作类型基础字段"""
    type_code: str = Field(..., description="操作类型代码")
    display_name: str = Field(..., description="显示名称")
    category: Optional[str] = Field(None, description="分类")
    description: Optional[str] = Field(None, description="描述")
    color: Optional[str] = Field(None, description="前端显示颜色")
    requires_element: bool = Field(False, description="是否需要元素")
    requires_value: bool = Field(False, description="是否需要参数值")
    config_schema: Optional[Dict[str, Any]] = Field(None, description="配置Schema")


class ActionTypeCreate(ActionTypeBase):
    """创建操作类型（执行器注册时使用）"""
    first_seen_executor_id: str = Field(..., description="首次注册的执行器ID")
    implementation_version: Optional[str] = Field(None, description="实现版本")


class ActionTypeResponse(ActionTypeBase):
    """操作类型响应"""
    id: int
    first_seen_executor_id: Optional[str]
    first_seen_at: datetime
    is_deprecated: bool
    created_at: datetime
    updated_at: datetime
    supported_by_executors: List[str] = Field(default_factory=list, description="支持的执行器ID列表")

    class Config:
        from_attributes = True


# ============ Executor Schemas ============

class ExecutorBase(BaseModel):
    """执行器基础字段"""
    executor_id: str = Field(..., description="执行器唯一标识")
    executor_version: str = Field(..., description="执行器版本")
    hostname: Optional[str] = Field(None, description="主机名")
    ip_address: Optional[str] = Field(None, description="IP地址")


class ExecutorCreate(ExecutorBase):
    """创建执行器（注册时使用）"""
    capabilities: List[ActionTypeCreate] = Field(..., description="支持的操作类型列表")


class ExecutorResponse(ExecutorBase):
    """执行器响应"""
    id: int
    last_seen: datetime
    is_online: bool
    created_at: datetime
    updated_at: datetime
    capabilities: List[ActionTypeResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


# ============ Registration Request/Response ============

class ExecutorRegistrationRequest(BaseModel):
    """执行器注册请求"""
    executor_id: str = Field(..., description="执行器唯一标识")
    executor_version: str = Field(..., description="执行器版本")
    hostname: Optional[str] = Field(None, description="主机名")
    ip_address: Optional[str] = Field(None, description="IP地址")
    capabilities: List[ActionTypeCreate] = Field(..., description="支持的操作类型列表", min_length=1)


class ExecutorRegistrationResponse(BaseModel):
    """执行器注册响应"""
    executor_id: str
    registered: bool
    new_actions_count: int
    total_actions_count: int
    message: str


class ExecutorHeartbeatRequest(BaseModel):
    """执行器心跳请求"""
    executor_id: str
    executor_version: Optional[str] = None


# ============ Action Type Query ============

class ActionTypesResponse(BaseModel):
    """获取操作类型列表响应"""
    total: int
    items: List[ActionTypeResponse]
    categories: Dict[str, List[str]] = Field(default_factory=dict, description="按分类分组的操作类型")


# ============ Validation ============

class ActionCapabilityCheckRequest(BaseModel):
    """操作能力检查请求"""
    executor_id: Optional[str] = Field(None, description="指定执行器ID，不指定则检查所有在线执行器")
    action_types: List[str] = Field(..., description="需要检查的操作类型列表", min_length=1)


class ActionCapabilityCheckResponse(BaseModel):
    """操作能力检查响应"""
    is_supported: bool
    executor_id: Optional[str]
    supported_actions: List[str]
    unsupported_actions: List[str]
    can_execute: bool
    warnings: List[str] = Field(default_factory=list)


class TestcaseValidationRequest(BaseModel):
    """用例验证请求（执行前）"""
    testcase_id: int
    executor_id: Optional[str] = Field(None, description="指定执行器ID")
    skip_unsupported: bool = Field(False, description="是否跳过不支持的用例")


class TestcaseValidationResponse(BaseModel):
    """用例验证响应"""
    testcase_id: int
    testcase_name: str
    can_execute: bool
    executor_id: Optional[str]
    all_actions_supported: bool
    unsupported_actions: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    recommendation: str
