"""Projects router."""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db_session
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
):
    """Get project list."""
    items, total = list_projects_service(
        db,
        skip=calculate_offset(page, page_size),
        limit=page_size,
        status=status,
        priority=priority,
        search=search,
    )
    return ok(data=PaginatedResponse(items=items, total=total, page=page, page_size=page_size))


@router.post("", response_model=ApiResponse[ProjectResponse])
def create_project(project_in: ProjectCreate, db: Session = Depends(get_db_session)):
    """Create project."""
    response, validation_error = create_project_service(db, project_in)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(data=response, message="Project created successfully")


@router.get("/{project_id}", response_model=ApiResponse[ProjectResponse])
def get_project(project_id: int, db: Session = Depends(get_db_session)):
    """Get project by ID."""
    response = get_project_service(db, project_id)
    if not response:
        return error(code=4004, message=f"Project not found: id={project_id}")
    return ok(data=response)


@router.put("/{project_id}", response_model=ApiResponse[ProjectResponse])
def update_project(project_id: int, project_in: ProjectUpdate, db: Session = Depends(get_db_session)):
    """Update project."""
    response, validation_error = update_project_service(db, project_id=project_id, project_in=project_in)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(data=response, message="Project updated successfully")


@router.delete("/{project_id}", response_model=ApiResponse)
def delete_project(project_id: int, db: Session = Depends(get_db_session)):
    """Delete project."""
    validation_error = delete_project_service(db, project_id)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(data={"project_id": project_id}, message="Project deleted successfully")


@router.get("/{project_id}/stats", response_model=ApiResponse[ProjectStatistics])
def get_project_statistics(project_id: int, db: Session = Depends(get_db_session)):
    """Get project statistics."""
    response, validation_error = get_project_statistics_service(db, project_id)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(data=response)
