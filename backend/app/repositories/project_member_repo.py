"""
Project Member Repository - 项目成员数据访问层
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.project_member import ProjectMember, ProjectMemberRole
from app.models.user import User


class ProjectMemberRepository:
    """项目成员数据访问类"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, project_id: int, user_id: int, role: ProjectMemberRole) -> ProjectMember:
        """创建项目成员"""
        member = ProjectMember(
            project_id=project_id,
            user_id=user_id,
            role=role.value if isinstance(role, ProjectMemberRole) else role
        )
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        return member

    def get(self, project_id: int, user_id: int) -> Optional[ProjectMember]:
        """获取项目成员"""
        return self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
        ).first()

    def get_by_id(self, member_id: int) -> Optional[ProjectMember]:
        """通过ID获取项目成员"""
        return self.db.query(ProjectMember).filter(ProjectMember.id == member_id).first()

    def list_by_project(self, project_id: int) -> List[ProjectMember]:
        """获取项目的所有成员"""
        return self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id
        ).all()

    def list_by_user(self, user_id: int) -> List[ProjectMember]:
        """获取用户加入的所有项目成员关系"""
        return self.db.query(ProjectMember).filter(
            ProjectMember.user_id == user_id
        ).all()

    def update_role(self, project_id: int, user_id: int, new_role: ProjectMemberRole) -> Optional[ProjectMember]:
        """更新成员角色"""
        member = self.get(project_id, user_id)
        if member:
            member.role = new_role.value if isinstance(new_role, ProjectMemberRole) else new_role
            self.db.commit()
            self.db.refresh(member)
        return member

    def delete(self, project_id: int, user_id: int) -> bool:
        """删除项目成员"""
        member = self.get(project_id, user_id)
        if member:
            self.db.delete(member)
            self.db.commit()
            return True
        return False

    def is_member(self, project_id: int, user_id: int) -> bool:
        """检查用户是否是项目成员"""
        return self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
        ).first() is not None

    def count_members(self, project_id: int) -> int:
        """统计项目成员数量"""
        return self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id
        ).count()

    def get_with_user_info(self, project_id: int) -> List[dict]:
        """获取项目成员及其用户信息"""
        members = self.db.query(ProjectMember, User).join(
            User, ProjectMember.user_id == User.id
        ).filter(
            ProjectMember.project_id == project_id
        ).all()

        result = []
        for member, user in members:
            result.append({
                "id": member.id,
                "project_id": member.project_id,
                "user_id": member.user_id,
                "username": user.username,
                "email": user.email,
                "role": member.role,
                "joined_at": member.joined_at.isoformat() if member.joined_at else None,
            })
        return result
