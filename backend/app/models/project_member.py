"""
Project Member model - 项目成员关联表
"""
from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .base import BaseModel, Base


class ProjectMemberRole(str, enum.Enum):
    """项目成员角色枚举"""
    VIEWER = "viewer"      # 查看者：只能查看
    EDITOR = "editor"      # 编辑者：可以编辑但不能删除
    ADMIN = "admin"        # 项目管理员：完全控制项目
    OWNER = "owner"        # 项目所有者：最高权限


class ProjectMember(Base):
    """项目成员关联表"""
    __tablename__ = "project_members"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(
        String(20),
        default=ProjectMemberRole.VIEWER,
        nullable=False,
        comment="成员角色"
    )
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="加入时间")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship('Project', backref='members')
    user = relationship('User', backref='project_memberships')

    # Unique constraint: 一个用户在一个项目中只能有一个角色
    __table_args__ = (
        UniqueConstraint('project_id', 'user_id', name='unique_project_user'),
    )

    def __repr__(self):
        return f"<ProjectMember(project_id={self.project_id}, user_id={self.user_id}, role='{self.role}')>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "user_id": self.user_id,
            "role": self.role,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
