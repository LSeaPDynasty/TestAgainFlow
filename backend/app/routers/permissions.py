"""
Project Members and Permissions Router - 项目成员和权限管理路由
"""
from typing import List
from fastapi import APIRouter, Depends, Query, Header
from sqlalchemy.orm import Session

from app.dependencies import get_db_session, require_auth, require_admin
from app.schemas.common import ApiResponse, PaginatedResponse
from app.schemas.project_member import (
    AddProjectMemberRequest,
    ProjectMemberCreate,
    ProjectMemberDetailResponse,
    ProjectMemberResponse,
    ProjectMemberUpdate,
    AuditLogResponse,
)
from app.repositories.project_member_repo import ProjectMemberRepository
from app.repositories.user_repo import UserRepository
from app.services.permission_service import PermissionService, PermissionDenied, ProjectMemberRole
from app.services.audit_log_service import AuditLogService, AuditAction
from app.models.user import User
from app.utils.response import error, ok

router = APIRouter(prefix="/permissions", tags=["permissions"])


@router.get("/projects/{project_id}/members", response_model=ApiResponse[List[ProjectMemberDetailResponse]])
def list_project_members(
    project_id: int,
    db: Session = Depends(get_db_session),
    auth: dict = Depends(require_auth)
):
    """获取项目成员列表"""
    try:
        user_id = int(auth["uid"])

        # 检查项目访问权限
        PermissionService.check_project_access(db, project_id, user_id)

        # 获取项目成员
        member_repo = ProjectMemberRepository(db)
        members_with_info = member_repo.get_with_user_info(project_id)

        return ok(data=members_with_info)

    except PermissionDenied as e:
        return error(code=4003, message=str(e))
    except Exception as e:
        return error(code=5000, message=f"Failed to list project members: {str(e)}")


@router.post("/projects/{project_id}/members", response_model=ApiResponse[ProjectMemberResponse])
def add_project_member(
    project_id: int,
    req: AddProjectMemberRequest,
    db: Session = Depends(get_db_session),
    auth: dict = Depends(require_auth)
):
    """添加项目成员"""
    try:
        user_id = int(auth["uid"])

        # 检查项目管理权限（需要ADMIN或OWNER角色）
        PermissionService.check_project_access(db, project_id, user_id, ProjectMemberRole.ADMIN)

        # 查找目标用户
        user_repo = UserRepository(db)
        target_user = user_repo.get_by_username(req.username)
        if not target_user:
            return error(code=4004, message=f"User '{req.username}' not found")

        # 检查目标用户是否已经是项目成员
        member_repo = ProjectMemberRepository(db)
        if member_repo.is_member(project_id, target_user.id):
            return error(code=4009, message=f"User '{req.username}' is already a member of this project")

        # 添加项目成员
        new_member = member_repo.create(
            project_id=project_id,
            user_id=target_user.id,
            role=ProjectMemberRole(req.role) if req.role in ProjectMemberRole._value2member_map_ else ProjectMemberRole.VIEWER
        )

        # 记录审计日志
        AuditLogService.log_member_action(
            db=db,
            user_id=user_id,
            action=AuditAction.MEMBER_ADD,
            project_id=project_id,
            target_user_id=target_user.id,
            target_username=target_user.username,
            role=req.role
        )

        return ok(data={
            "id": new_member.id,
            "project_id": new_member.project_id,
            "user_id": new_member.user_id,
            "username": target_user.username,
            "email": target_user.email,
            "role": new_member.role,
            "joined_at": new_member.joined_at
        }, message="Member added successfully")

    except PermissionDenied as e:
        return error(code=4003, message=str(e))
    except Exception as e:
        return error(code=5000, message=f"Failed to add project member: {str(e)}")


@router.put("/projects/{project_id}/members/{member_user_id}", response_model=ApiResponse)
def update_member_role(
    project_id: int,
    member_user_id: int,
    req: ProjectMemberUpdate,
    db: Session = Depends(get_db_session),
    auth: dict = Depends(require_auth)
):
    """更新项目成员角色"""
    try:
        user_id = int(auth["uid"])

        # 检查项目管理权限
        PermissionService.check_project_access(db, project_id, user_id, ProjectMemberRole.ADMIN)

        # 不能修改自己的角色（防止意外失去权限）
        if member_user_id == user_id:
            return error(code=4000, message="Cannot modify your own role")

        # 更新成员角色
        member_repo = ProjectMemberRepository(db)
        new_role = ProjectMemberRole(req.role) if req.role in ProjectMemberRole._value2member_map_ else ProjectMemberRole.VIEWER
        updated_member = member_repo.update_role(project_id, member_user_id, new_role)

        if not updated_member:
            return error(code=4004, message="Member not found")

        # 获取目标用户信息
        target_user = db.query(User).filter(User.id == member_user_id).first()

        # 记录审计日志
        AuditLogService.log_member_action(
            db=db,
            user_id=user_id,
            action=AuditAction.MEMBER_ROLE_UPDATE,
            project_id=project_id,
            target_user_id=member_user_id,
            target_username=target_user.username if target_user else None,
            role=req.role
        )

        return ok(message="Member role updated successfully")

    except PermissionDenied as e:
        return error(code=4003, message=str(e))
    except Exception as e:
        return error(code=5000, message=f"Failed to update member role: {str(e)}")


@router.delete("/projects/{project_id}/members/{member_user_id}", response_model=ApiResponse)
def remove_project_member(
    project_id: int,
    member_user_id: int,
    db: Session = Depends(get_db_session),
    auth: dict = Depends(require_auth)
):
    """移除项目成员"""
    try:
        user_id = int(auth["uid"])

        # 检查项目管理权限
        PermissionService.check_project_access(db, project_id, user_id, ProjectMemberRole.ADMIN)

        # 不能移除自己
        if member_user_id == user_id:
            return error(code=4000, message="Cannot remove yourself from the project")

        # 移除成员
        member_repo = ProjectMemberRepository(db)
        success = member_repo.delete(project_id, member_user_id)

        if not success:
            return error(code=4004, message="Member not found")

        # 获取目标用户信息
        target_user = db.query(User).filter(User.id == member_user_id).first()

        # 记录审计日志
        AuditLogService.log_member_action(
            db=db,
            user_id=user_id,
            action=AuditAction.MEMBER_REMOVE,
            project_id=project_id,
            target_user_id=member_user_id,
            target_username=target_user.username if target_user else None
        )

        return ok(message="Member removed successfully")

    except PermissionDenied as e:
        return error(code=4003, message=str(e))
    except Exception as e:
        return error(code=5000, message=f"Failed to remove project member: {str(e)}")


@router.get("/audit-logs", response_model=ApiResponse[PaginatedResponse[AuditLogResponse]])
def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    project_id: int = Query(None),
    resource_type: str = Query(None),
    resource_id: int = Query(None),
    action: str = Query(None),
    db: Session = Depends(get_db_session),
    auth: dict = Depends(require_auth)
):
    """查询审计日志"""
    try:
        user_id = int(auth["uid"])

        # 只有管理员可以查看所有日志
        if not PermissionService.is_system_admin(db, user_id):
            # 普通用户只能查看自己有权限的项目的日志
            if project_id:
                PermissionService.check_project_access(db, project_id, user_id)
            else:
                return error(code=4003, message="Only administrators can view all audit logs")

        # 构建查询
        from app.models.audit_log import AuditLog
        from app.utils.pagination import calculate_offset

        query = db.query(AuditLog)

        if project_id:
            query = query.filter(AuditLog.project_id == project_id)
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        if resource_id:
            query = query.filter(AuditLog.resource_id == resource_id)
        if action:
            query = query.filter(AuditLog.action == action)

        # 分页
        total = query.count()
        logs = query.order_by(AuditLog.created_at.desc()).offset(
            calculate_offset(page, page_size)
        ).limit(page_size).all()

        return ok(data=PaginatedResponse(
            items=logs,
            total=total,
            page=page,
            page_size=page_size
        ))

    except PermissionDenied as e:
        return error(code=4003, message=str(e))
    except Exception as e:
        return error(code=5000, message=f"Failed to list audit logs: {str(e)}")


@router.get("/my-projects", response_model=ApiResponse[List[int]])
def get_my_accessible_projects(
    db: Session = Depends(get_db_session),
    auth: dict = Depends(require_auth)
):
    """获取当前用户有权限访问的项目ID列表"""
    try:
        user_id = int(auth["uid"])
        project_ids = PermissionService.get_accessible_projects(db, user_id)
        return ok(data=project_ids)

    except Exception as e:
        return error(code=5000, message=f"Failed to get accessible projects: {str(e)}")
