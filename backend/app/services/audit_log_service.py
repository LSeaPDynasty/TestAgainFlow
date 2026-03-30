"""
Audit Log Service - 操作审计日志服务
记录所有敏感操作，包括用户操作、资源变更等
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog, AuditAction
from app.models.user import User

logger = logging.getLogger(__name__)


class AuditLogService:
    """操作审计日志服务"""

    @staticmethod
    def create_log(
        db: Session,
        user_id: Optional[int],
        action: AuditAction,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        project_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None
    ) -> AuditLog:
        """
        创建操作日志

        Args:
            db: 数据库会话
            user_id: 用户ID
            action: 操作类型
            resource_type: 资源类型
            resource_id: 资源ID
            project_id: 项目ID
            details: 操作详情（JSON格式）
            ip_address: IP地址
            user_agent: 用户代理
            status: 操作结果（success/failed）
            error_message: 错误信息

        Returns:
            创建的审计日志对象
        """
        try:
            # 获取用户名（冗余字段，便于查询）
            username = None
            if user_id:
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    username = user.username

            log_entry = AuditLog(
                user_id=user_id,
                username=username,
                action=action.value if isinstance(action, AuditAction) else action,
                resource_type=resource_type,
                resource_id=resource_id,
                project_id=project_id,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent,
                status=status,
                error_message=error_message
            )

            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)

            logger.debug(f"Created audit log: {action} by user {user_id} on {resource_type}:{resource_id}")
            return log_entry

        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            db.rollback()
            # 不抛出异常，避免影响主业务流程
            return None

    @staticmethod
    def log_user_action(
        db: Session,
        user_id: int,
        action: AuditAction,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[AuditLog]:
        """记录用户操作（登录、登出等）"""
        return AuditLogService.create_log(
            db=db,
            user_id=user_id,
            action=action,
            resource_type="user",
            resource_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )

    @staticmethod
    def log_project_action(
        db: Session,
        user_id: int,
        action: AuditAction,
        project_id: int,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None
    ) -> Optional[AuditLog]:
        """记录项目操作"""
        return AuditLogService.create_log(
            db=db,
            user_id=user_id,
            action=action,
            resource_type="project",
            resource_id=project_id,
            project_id=project_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            error_message=error_message
        )

    @staticmethod
    def log_element_action(
        db: Session,
        user_id: int,
        action: AuditAction,
        element_id: int,
        project_id: int,
        element_name: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[AuditLog]:
        """记录元素操作"""
        details = {"element_name": element_name}
        if changes:
            details["changes"] = changes

        return AuditLogService.create_log(
            db=db,
            user_id=user_id,
            action=action,
            resource_type="element",
            resource_id=element_id,
            project_id=project_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )

    @staticmethod
    def log_step_action(
        db: Session,
        user_id: int,
        action: AuditAction,
        step_id: int,
        project_id: int,
        step_name: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[AuditLog]:
        """记录步骤操作"""
        details = {"step_name": step_name}
        if changes:
            details["changes"] = changes

        return AuditLogService.create_log(
            db=db,
            user_id=user_id,
            action=action,
            resource_type="step",
            resource_id=step_id,
            project_id=project_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )

    @staticmethod
    def log_flow_action(
        db: Session,
        user_id: int,
        action: AuditAction,
        flow_id: int,
        project_id: int,
        flow_name: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[AuditLog]:
        """记录流程操作"""
        details = {"flow_name": flow_name}
        if changes:
            details["changes"] = changes

        return AuditLogService.create_log(
            db=db,
            user_id=user_id,
            action=action,
            resource_type="flow",
            resource_id=flow_id,
            project_id=project_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )

    @staticmethod
    def log_testcase_action(
        db: Session,
        user_id: int,
        action: AuditAction,
        testcase_id: int,
        project_id: int,
        testcase_name: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[AuditLog]:
        """记录测试用例操作"""
        details = {"testcase_name": testcase_name}
        if changes:
            details["changes"] = changes

        return AuditLogService.create_log(
            db=db,
            user_id=user_id,
            action=action,
            resource_type="testcase",
            resource_id=testcase_id,
            project_id=project_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )

    @staticmethod
    def log_member_action(
        db: Session,
        user_id: int,
        action: AuditAction,
        project_id: int,
        target_user_id: int,
        target_username: Optional[str] = None,
        role: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[AuditLog]:
        """记录成员管理操作"""
        details = {
            "target_user_id": target_user_id,
            "target_username": target_username,
        }
        if role:
            details["role"] = role

        return AuditLogService.create_log(
            db=db,
            user_id=user_id,
            action=action,
            resource_type="project_member",
            resource_id=target_user_id,
            project_id=project_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )

    @staticmethod
    def get_user_logs(
        db: Session,
        user_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> list[AuditLog]:
        """获取用户的操作日志"""
        return db.query(AuditLog).filter(
            AuditLog.user_id == user_id
        ).order_by(
            AuditLog.created_at.desc()
        ).offset(offset).limit(limit).all()

    @staticmethod
    def get_project_logs(
        db: Session,
        project_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> list[AuditLog]:
        """获取项目的操作日志"""
        return db.query(AuditLog).filter(
            AuditLog.project_id == project_id
        ).order_by(
            AuditLog.created_at.desc()
        ).offset(offset).limit(limit).all()

    @staticmethod
    def get_resource_logs(
        db: Session,
        resource_type: str,
        resource_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> list[AuditLog]:
        """获取资源的操作日志"""
        return db.query(AuditLog).filter(
            AuditLog.resource_type == resource_type,
            AuditLog.resource_id == resource_id
        ).order_by(
            AuditLog.created_at.desc()
        ).offset(offset).limit(limit).all()
