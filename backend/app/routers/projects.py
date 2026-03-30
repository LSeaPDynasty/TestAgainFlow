"""Projects router."""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db_session, require_auth
from app.schemas.common import ApiResponse, PaginatedResponse
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectStatistics, ProjectUpdate
from app.services.project_service import (
    create_project as create_project_service,
    delete_project as delete_project_service,
    get_project as get_project_service,
    get_project_statistics as get_project_statistics_service,
    list_projects as list_projects_service,
    update_project as update_project_service,
)
from app.services.permission_service import PermissionService, PermissionDenied, ProjectMemberRole
from app.services.audit_log_service import AuditLogService, AuditAction
from app.repositories.project_member_repo import ProjectMemberRepository
from app.utils.pagination import calculate_offset
from app.utils.response import error, ok

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=ApiResponse[PaginatedResponse])
def list_projects(
    page: int = Query(1, ge=1, description="page number"),
    page_size: int = Query(20, ge=1, le=100, description="page size"),
    status: Optional[str] = Query(None, description="status filter"),
    priority: Optional[str] = Query(None, description="priority filter"),
    search: Optional[str] = Query(None, description="search"),
    db: Session = Depends(get_db_session),
    auth: dict = Depends(require_auth)
):
    """Get project list - only returns projects user has access to."""
    user_id = int(auth["uid"])
    items, total = list_projects_service(
        db,
        skip=calculate_offset(page, page_size),
        limit=page_size,
        status=status,
        priority=priority,
        search=search,
        user_id=user_id
    )
    return ok(data=PaginatedResponse(items=items, total=total, page=page, page_size=page_size))


@router.post("", response_model=ApiResponse[ProjectResponse])
def create_project(
    project_in: ProjectCreate,
    db: Session = Depends(get_db_session),
    auth: dict = Depends(require_auth)
):
    """Create project."""
    user_id = int(auth["uid"])
    response, validation_error = create_project_service(db, project_in)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)

    # 创建者自动成为项目所有者
    member_repo = ProjectMemberRepository(db)
    member_repo.create(response["id"], user_id, ProjectMemberRole.OWNER)

    # 记录审计日志
    AuditLogService.log_project_action(
        db=db,
        user_id=user_id,
        action=AuditAction.PROJECT_CREATE,
        project_id=response["id"],
        details={"project_name": project_in.name}
    )

    return ok(data=response, message="Project created successfully")


@router.get("/{project_id}", response_model=ApiResponse[ProjectResponse])
def get_project(
    project_id: int,
    db: Session = Depends(get_db_session),
    auth: dict = Depends(require_auth)
):
    """Get project by ID."""
    try:
        user_id = int(auth["uid"])
        # 检查项目访问权限
        PermissionService.check_project_access(db, project_id, user_id)

        response = get_project_service(db, project_id)
        if not response:
            return error(code=4004, message=f"Project not found: id={project_id}")

        return ok(data=response)

    except PermissionDenied as e:
        return error(code=4003, message=str(e))


@router.put("/{project_id}", response_model=ApiResponse[ProjectResponse])
def update_project(
    project_id: int,
    project_in: ProjectUpdate,
    db: Session = Depends(get_db_session),
    auth: dict = Depends(require_auth)
):
    """Update project."""
    try:
        user_id = int(auth["uid"])
        # 检查编辑权限
        PermissionService.check_project_access(db, project_id, user_id, ProjectMemberRole.EDITOR)

        response, validation_error = update_project_service(db, project_id=project_id, project_in=project_in)
        if validation_error:
            return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)

        # 记录审计日志
        AuditLogService.log_project_action(
            db=db,
            user_id=user_id,
            action=AuditAction.PROJECT_UPDATE,
            project_id=project_id,
            details={"changes": project_in.model_dump(exclude_unset=True)}
        )

        return ok(data=response, message="Project updated successfully")

    except PermissionDenied as e:
        return error(code=4003, message=str(e))


@router.delete("/{project_id}", response_model=ApiResponse)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db_session),
    auth: dict = Depends(require_auth)
):
    """Delete project."""
    try:
        user_id = int(auth["uid"])
        # 检查删除权限（仅所有者）
        PermissionService.check_project_access(db, project_id, user_id, ProjectMemberRole.OWNER)

        validation_error = delete_project_service(db, project_id)
        if validation_error:
            return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)

        # 记录审计日志
        AuditLogService.log_project_action(
            db=db,
            user_id=user_id,
            action=AuditAction.PROJECT_DELETE,
            project_id=project_id,
            details={"project_id": project_id}
        )

        return ok(data={"project_id": project_id}, message="Project deleted successfully")

    except PermissionDenied as e:
        return error(code=4003, message=str(e))


@router.get("/{project_id}/stats", response_model=ApiResponse[ProjectStatistics])
def get_project_statistics(project_id: int, db: Session = Depends(get_db_session)):
    """Get project statistics."""
    response, validation_error = get_project_statistics_service(db, project_id)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(data=response)
