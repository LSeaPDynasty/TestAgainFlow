"""
Project schemas - 项目数据模型
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ProjectBase(BaseModel):
    """项目基础模型"""
    name: str = Field(..., max_length=200, description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    status: Optional[str] = Field("active", description="项目状态")
    tags: Optional[List[str]] = Field(default_factory=list, description="项目标签")
    owner_id: Optional[int] = Field(None, description="负责人ID")
    priority: Optional[str] = Field("medium", description="优先级")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")


class ProjectCreate(ProjectBase):
    """创建项目请求"""
    pass


class ProjectUpdate(BaseModel):
    """更新项目请求"""
    name: Optional[str] = Field(None, max_length=200, description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    status: Optional[str] = Field(None, description="项目状态")
    tags: Optional[List[str]] = Field(None, description="项目标签")
    owner_id: Optional[int] = Field(None, description="负责人ID")
    priority: Optional[str] = Field(None, description="优先级")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")


class ProjectStatistics(BaseModel):
    """项目统计信息"""
    testcase_count: int = Field(0, description="用例数量")
    suite_count: int = Field(0, description="套件数量")
    run_count: int = Field(0, description="执行次数")
    pass_count: int = Field(0, description="通过次数")
    pass_rate: float = Field(0.0, description="通过率")


class ProjectResponse(ProjectBase):
    """项目响应"""
    id: int = Field(..., description="项目ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    statistics: Optional[ProjectStatistics] = Field(None, description="统计信息")

    class Config:
        from_attributes = True
