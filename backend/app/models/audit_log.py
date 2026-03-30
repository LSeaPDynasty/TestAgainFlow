"""
Audit Log model - 操作审计日志
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .base import Base


class AuditAction(str, enum.Enum):
    """审计操作类型枚举"""
    # 用户操作
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_REGISTER = "user_register"

    # 项目操作
    PROJECT_CREATE = "project_create"
    PROJECT_UPDATE = "project_update"
    PROJECT_DELETE = "project_delete"
    PROJECT_VIEW = "project_view"

    # 元素操作
    ELEMENT_CREATE = "element_create"
    ELEMENT_UPDATE = "element_update"
    ELEMENT_DELETE = "element_delete"

    # 步骤操作
    STEP_CREATE = "step_create"
    STEP_UPDATE = "step_update"
    STEP_DELETE = "step_delete"

    # 流程操作
    FLOW_CREATE = "flow_create"
    FLOW_UPDATE = "flow_update"
    FLOW_DELETE = "flow_delete"

    # 测试用例操作
    TESTCASE_CREATE = "testcase_create"
    TESTCASE_UPDATE = "testcase_update"
    TESTCASE_DELETE = "testcase_delete"
    TESTCASE_EXECUTE = "testcase_execute"

    # 权限操作
    MEMBER_ADD = "member_add"
    MEMBER_REMOVE = "member_remove"
    MEMBER_ROLE_UPDATE = "member_role_update"

    # 系统操作
    SYSTEM_CONFIG = "system_config"
    SYSTEM_ERROR = "system_error"


class AuditLog(Base):
    """操作审计日志表"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    username = Column(String(50), nullable=True, index=True, comment="操作用户名（冗余字段）")
    action = Column(String(50), nullable=False, index=True, comment="操作类型")
    resource_type = Column(String(50), nullable=True, index=True, comment="资源类型（project/element/step等）")
    resource_id = Column(Integer, nullable=True, index=True, comment="资源ID")
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True, comment="关联项目ID")

    # 操作详情
    details = Column(JSON, nullable=True, comment="操作详情（JSON格式）")
    ip_address = Column(String(50), nullable=True, comment="IP地址")
    user_agent = Column(String(500), nullable=True, comment="用户代理")

    # 结果
    status = Column(String(20), nullable=False, default="success", comment="操作结果：success/failed")
    error_message = Column(Text, nullable=True, comment="错误信息（如果失败）")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True, comment="操作时间")

    # Relationships
    user = relationship('User', backref='audit_logs')
    project = relationship('Project', backref='audit_logs')

    def __repr__(self):
        return f"<AuditLog(id={self.id}, user_id={self.user_id}, action='{self.action}', resource='{self.resource_type}:{self.resource_id}')>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "project_id": self.project_id,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "status": self.status,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
