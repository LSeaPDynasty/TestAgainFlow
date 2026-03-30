"""Service helpers for project endpoints."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from app.repositories.project_repo import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.permission_service import PermissionService
from app.utils.cache import cache, cached
from app.middleware import ConflictException, NotFoundException


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
        raise ConflictException(f"Project name already exists: {project_in.name}")
    project = repo.create(project_in.model_dump())
    payload = project.to_dict()
    payload["statistics"] = repo.get_statistics(project.id)

    # 清除项目列表缓存
    cache.clear_pattern("project_list:*")

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
        raise NotFoundException(f"Project not found: id={project_id}")

    if project_in.name and project_in.name != project.name and repo.get_by_name(project_in.name):
        raise ConflictException(f"Project name already exists: {project_in.name}")

    updated = repo.update(project, project_in.model_dump(exclude_unset=True))
    payload = updated.to_dict()
    payload["statistics"] = repo.get_statistics(updated.id)

    # 清除相关缓存
    cache.delete(f"project_statistics:{project_id}")
    cache.clear_pattern("project_list:*")

    return payload, None


def delete_project(db: Session, project_id: int) -> Optional[ServiceValidationError]:
    repo = ProjectRepository(db)
    project = repo.get(project_id)
    if not project:
        raise NotFoundException(f"Project not found: id={project_id}")
    repo.delete(project)

    # 清除相关缓存
    cache.delete(f"project_statistics:{project_id}")
    cache.clear_pattern("project_list:*")

    return None


def get_project_statistics(db: Session, project_id: int) -> tuple[Optional[dict], Optional[ServiceValidationError]]:
    # 先检查缓存
    cache_key = f"project_statistics:{project_id}"
    cached_stats = cache.get(cache_key)
    if cached_stats is not None:
        return cached_stats, None

    repo = ProjectRepository(db)
    project = repo.get(project_id)
    if not project:
        raise NotFoundException(f"Project not found: id={project_id}")

    stats = repo.get_statistics(project_id)
    # 缓存统计信息，TTL设置为5分钟（300秒）
    cache.set(cache_key, stats, ttl=300)
    return stats, None
