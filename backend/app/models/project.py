"""
Project model - 项目管理
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .base import BaseModel, Base


class ProjectStatus(str, enum.Enum):
    """项目状态枚举"""
    ACTIVE = "active"      # 活跃
    ARCHIVED = "archived"  # 已归档
    CLOSED = "closed"      # 已关闭


class ProjectPriority(str, enum.Enum):
    """项目优先级枚举"""
    LOW = "low"       # 低
    MEDIUM = "medium" # 中
    HIGH = "high"     # 高
    URGENT = "urgent" # 紧急


class Project(BaseModel):
    """项目模型"""
    __tablename__ = "projects"

    name = Column(String(200), unique=True, nullable=False, index=True, comment="项目名称")
    description = Column(Text, nullable=True, comment="项目描述")
    status = Column(
        Enum(ProjectStatus),
        default=ProjectStatus.ACTIVE,
        nullable=False,
        comment="项目状态"
    )
    tags = Column(String(500), nullable=True, comment="项目标签（逗号分隔）")
    owner_id = Column(Integer, nullable=True, comment="负责人ID")
    priority = Column(
        Enum(ProjectPriority),
        default=ProjectPriority.MEDIUM,
        nullable=False,
        comment="优先级"
    )
    start_date = Column(DateTime, nullable=True, comment="开始日期")
    end_date = Column(DateTime, nullable=True, comment="结束日期")

    # Relationships
    test_plans = relationship('TestPlan', back_populates='project')

    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}', status='{self.status}')>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value if isinstance(self.status, ProjectStatus) else self.status,
            "tags": self.tags.split(",") if self.tags else [],
            "owner_id": self.owner_id,
            "priority": self.priority.value if isinstance(self.priority, ProjectPriority) else self.priority,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
