"""Service helpers for project endpoints."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from app.repositories.project_repo import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.permission_service import PermissionService


@dataclass
class ServiceValidationError:
    code: int
    message: str
    data: Optional[dict] = None


def list_projects(
    db: Session,
    *,
    skip: int,
    limit: int,
    status: Optional[str],
    priority: Optional[str],
    search: Optional[str],
    user_id: Optional[int] = None,
):
    repo = ProjectRepository(db)
    projects, total = repo.list(
        skip=skip,
        limit=limit,
        status=status,
        priority=priority,
        search=search,
    )

    # 如果指定了用户ID，过滤出用户有权限访问的项目
    if user_id is not None:
        projects = PermissionService.filter_accessible_projects(db, user_id, projects)
        total = len(projects)
        # 重新应用分页
        projects = projects[skip:skip + limit]

    items_with_stats = []
    for project in projects:
        project_dict = project.to_dict()
        project_dict["statistics"] = repo.get_statistics(project.id)
        items_with_stats.append(project_dict)

    return items_with_stats, total


def get_project(db: Session, project_id: int) -> Optional[dict]:
    repo = ProjectRepository(db)
    project = repo.get(project_id)
    if not project:
        return None
    payload = project.to_dict()
    payload["statistics"] = repo.get_statistics(project.id)
    return payload


def create_project(db: Session, project_in: ProjectCreate) -> tuple[Optional[dict], Optional[ServiceValidationError]]:
    repo = ProjectRepository(db)
    if repo.get_by_name(project_in.name):
        return None, ServiceValidationError(code=4009, message=f"Project name already exists: {project_in.name}")
    project = repo.create(project_in.model_dump())
    payload = project.to_dict()
    payload["statistics"] = repo.get_statistics(project.id)
    return payload, None


def update_project(
    db: Session,
    *,
    project_id: int,
    project_in: ProjectUpdate,
) -> tuple[Optional[dict], Optional[ServiceValidationError]]:
    repo = ProjectRepository(db)
    project = repo.get(project_id)
    if not project:
        return None, ServiceValidationError(code=4004, message=f"Project not found: id={project_id}")

    if project_in.name and project_in.name != project.name and repo.get_by_name(project_in.name):
        return None, ServiceValidationError(code=4009, message=f"Project name already exists: {project_in.name}")

    updated = repo.update(project, project_in.model_dump(exclude_unset=True))
    payload = updated.to_dict()
    payload["statistics"] = repo.get_statistics(updated.id)
    return payload, None


def delete_project(db: Session, project_id: int) -> Optional[ServiceValidationError]:
    repo = ProjectRepository(db)
    project = repo.get(project_id)
    if not project:
        return ServiceValidationError(code=4004, message=f"Project not found: id={project_id}")
    repo.delete(project)
    return None


def get_project_statistics(db: Session, project_id: int) -> tuple[Optional[dict], Optional[ServiceValidationError]]:
    repo = ProjectRepository(db)
    project = repo.get(project_id)
    if not project:
        return None, ServiceValidationError(code=4004, message=f"Project not found: id={project_id}")
    return repo.get_statistics(project_id), None
