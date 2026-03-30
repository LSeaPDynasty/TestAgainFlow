"""
Project Member Schemas - 项目成员相关的Pydantic模型
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ProjectMemberBase(BaseModel):
    """项目成员基础模型"""
    user_id: int = Field(..., description="用户ID")
    role: str = Field(default="viewer", description="成员角色")


class ProjectMemberCreate(ProjectMemberBase):
    """创建项目成员请求"""
    pass


class ProjectMemberUpdate(BaseModel):
    """更新项目成员请求"""
    role: str = Field(..., description="新角色")


class ProjectMemberResponse(BaseModel):
    """项目成员响应"""
    id: int
    project_id: int
    user_id: int
    username: Optional[str] = None
    email: Optional[str] = None
    role: str
    joined_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProjectMemberDetailResponse(BaseModel):
    """项目成员详细信息响应"""
    id: int
    project_id: int
    user_id: int
    username: str
    email: Optional[str] = None
    role: str
    joined_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AddProjectMemberRequest(BaseModel):
    """添加项目成员请求"""
    username: str = Field(..., description="用户名")
    role: str = Field(default="viewer", description="成员角色")


class AuditLogResponse(BaseModel):
    """审计日志响应"""
    id: int
    user_id: Optional[int] = None
    username: Optional[str] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    project_id: Optional[int] = None
    details: Optional[dict] = None
    ip_address: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
