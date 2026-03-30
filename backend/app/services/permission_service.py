"""
Permission Service - 权限检查服务
提供项目访问权限检查、用户角色验证等功能
"""
import logging
from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.project import Project
from app.models.project_member import ProjectMember, ProjectMemberRole
from app.models.element import Element
from app.models.step import Step
from app.models.flow import Flow
from app.models.testcase import Testcase

logger = logging.getLogger(__name__)


class PermissionDenied(Exception):
    """权限拒绝异常"""
    def __init__(self, message: str = "Permission denied"):
        self.message = message
        super().__init__(self.message)


class PermissionService:
    """权限检查服务"""

    # 权限级别定义（数字越大权限越高）
    ROLE_HIERARCHY = {
        ProjectMemberRole.VIEWER: 1,
        ProjectMemberRole.EDITOR: 2,
        ProjectMemberRole.ADMIN: 3,
        ProjectMemberRole.OWNER: 4,
    }

    USER_ROLE_HIERARCHY = {
        UserRole.MEMBER: 1,
        UserRole.ADMIN: 2,
        UserRole.SUPER_ADMIN: 3,
    }

    @classmethod
    def get_project_role(cls, db: Session, project_id: int, user_id: int) -> Optional[ProjectMemberRole]:
        """
        获取用户在项目中的角色

        Args:
            db: 数据库会话
            project_id: 项目ID
            user_id: 用户ID

        Returns:
            项目成员角色，如果用户不是项目成员则返回None
        """
        member = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
        ).first()

        if member:
            return ProjectMemberRole(member.role)
        return None

    @classmethod
    def is_project_member(cls, db: Session, project_id: int, user_id: int) -> bool:
        """检查用户是否是项目成员"""
        return cls.get_project_role(db, project_id, user_id) is not None

    @classmethod
    def is_project_owner(cls, db: Session, project_id: int, user_id: int) -> bool:
        """检查用户是否是项目所有者"""
        role = cls.get_project_role(db, project_id, user_id)
        return role == ProjectMemberRole.OWNER

    @classmethod
    def is_project_admin(cls, db: Session, project_id: int, user_id: int) -> bool:
        """检查用户是否是项目管理员（包括所有者）"""
        role = cls.get_project_role(db, project_id, user_id)
        if not role:
            return False
        return cls.ROLE_HIERARCHY.get(role, 0) >= cls.ROLE_HIERARCHY[ProjectMemberRole.ADMIN]

    @classmethod
    def can_edit_project(cls, db: Session, project_id: int, user_id: int) -> bool:
        """检查用户是否可以编辑项目（编辑者及以上权限）"""
        role = cls.get_project_role(db, project_id, user_id)
        if not role:
            return False
        return cls.ROLE_HIERARCHY.get(role, 0) >= cls.ROLE_HIERARCHY[ProjectMemberRole.EDITOR]

    @classmethod
    def can_delete_project(cls, db: Session, project_id: int, user_id: int) -> bool:
        """检查用户是否可以删除项目（仅项目所有者）"""
        return cls.is_project_owner(db, project_id, user_id)

    @classmethod
    def is_system_admin(cls, db: Session, user_id: int) -> bool:
        """检查用户是否是系统管理员"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        return user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]

    @classmethod
    def is_super_admin(cls, db: Session, user_id: int) -> bool:
        """检查用户是否是超级管理员"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        return user.role == UserRole.SUPER_ADMIN

    @classmethod
    def check_project_access(cls, db: Session, project_id: int, user_id: int, require_role: Optional[ProjectMemberRole] = None):
        """
        检查项目访问权限

        Args:
            db: 数据库会话
            project_id: 项目ID
            user_id: 用户ID
            require_role: 需要的最低角色（None表示只需是成员）

        Raises:
            PermissionDenied: 如果没有权限
        """
        # 超级管理员可以访问所有项目
        if cls.is_super_admin(db, user_id):
            return

        # 检查是否是项目成员
        role = cls.get_project_role(db, project_id, user_id)
        if not role:
            raise PermissionDenied(f"User {user_id} is not a member of project {project_id}")

        # 检查角色级别
        if require_role:
            required_level = cls.ROLE_HIERARCHY.get(require_role, 0)
            user_level = cls.ROLE_HIERARCHY.get(role, 0)
            if user_level < required_level:
                raise PermissionDenied(
                    f"User {user_id} requires {require_role} role or higher for project {project_id}"
                )

    @classmethod
    def check_system_admin(cls, db: Session, user_id: int):
        """
        检查系统管理员权限

        Args:
            db: 数据库会话
            user_id: 用户ID

        Raises:
            PermissionDenied: 如果不是系统管理员
        """
        if not cls.is_system_admin(db, user_id):
            raise PermissionDenied(f"User {user_id} is not a system administrator")

    @classmethod
    def check_super_admin(cls, db: Session, user_id: int):
        """
        检查超级管理员权限

        Args:
            db: 数据库会话
            user_id: 用户ID

        Raises:
            PermissionDenied: 如果不是超级管理员
        """
        if not cls.is_super_admin(db, user_id):
            raise PermissionDenied(f"User {user_id} is not a super administrator")

    @classmethod
    def get_accessible_projects(cls, db: Session, user_id: int) -> List[int]:
        """
        获取用户有权限访问的项目ID列表

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            项目ID列表
        """
        # 超级管理员可以访问所有项目
        if cls.is_super_admin(db, user_id):
            all_projects = db.query(Project).all()
            return [p.id for p in all_projects]

        # 普通用户只能访问自己是成员的项目
        memberships = db.query(ProjectMember).filter(
            ProjectMember.user_id == user_id
        ).all()
        return [m.project_id for m in memberships]

    @classmethod
    def filter_accessible_projects(cls, db: Session, user_id: int, projects: List[Project]) -> List[Project]:
        """
        过滤出用户有权限访问的项目

        Args:
            db: 数据库会话
            user_id: 用户ID
            projects: 项目列表

        Returns:
            用户有权限访问的项目列表
        """
        accessible_ids = set(cls.get_accessible_projects(db, user_id))
        return [p for p in projects if p.id in accessible_ids]

    @classmethod
    def get_resource_project_id(cls, db: Session, resource_type: str, resource_id: int) -> Optional[int]:
        """
        获取资源所属的项目ID

        Args:
            db: 数据库会话
            resource_type: 资源类型（element/step/flow/testcase等）
            resource_id: 资源ID

        Returns:
            项目ID，如果资源不存在或不属于任何项目则返回None
        """
        if resource_type == "element":
            resource = db.query(Element).filter(Element.id == resource_id).first()
            return resource.screen.project_id if resource else None

        elif resource_type == "step":
            resource = db.query(Step).filter(Step.id == resource_id).first()
            return resource.project_id if resource else None

        elif resource_type == "flow":
            resource = db.query(Flow).filter(Flow.id == resource_id).first()
            return resource.project_id if resource else None

        elif resource_type == "testcase":
            resource = db.query(Testcase).filter(Testcase.id == resource_id).first()
            return resource.project_id if resource else None

        elif resource_type == "project":
            return resource_id

        return None

    @classmethod
    def check_resource_access(cls, db: Session, resource_type: str, resource_id: int, user_id: int, require_role: Optional[ProjectMemberRole] = None):
        """
        检查资源访问权限（通过项目权限）

        Args:
            db: 数据库会话
            resource_type: 资源类型
            resource_id: 资源ID
            user_id: 用户ID
            require_role: 需要的最低项目角色

        Raises:
            PermissionDenied: 如果没有权限
        """
        project_id = cls.get_resource_project_id(db, resource_type, resource_id)
        if not project_id:
            raise PermissionDenied(f"Resource {resource_type}:{resource_id} not found or has no project")

        cls.check_project_access(db, project_id, user_id, require_role)
