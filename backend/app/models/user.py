"""User model."""
from sqlalchemy import Boolean, Column, String
import enum

from app.models.base import BaseModel


class UserRole(str, enum.Enum):
    """用户角色枚举"""
    MEMBER = "member"          # 普通成员
    ADMIN = "admin"            # 管理员
    SUPER_ADMIN = "super_admin"  # 超级管理员


class User(BaseModel):
    __tablename__ = "users"

    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=True, index=True)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(20), nullable=False, default=UserRole.MEMBER)
    is_active = Column(Boolean, nullable=False, default=True)
