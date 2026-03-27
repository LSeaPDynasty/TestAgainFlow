"""Tags router."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db_session
from app.schemas.common import ApiResponse, PaginatedResponse
from app.schemas.tag import TagCreate, TagResponse
from app.services.tag_service import (
    create_tag as create_tag_service,
    delete_tag as delete_tag_service,
    list_tags as list_tags_service,
)
from app.utils.pagination import calculate_offset
from app.utils.response import error, ok

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=ApiResponse[PaginatedResponse[TagResponse]])
def list_tags(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db_session),
):
    """Get tag list."""
    results, total = list_tags_service(
        db,
        skip=calculate_offset(page, page_size),
        limit=page_size,
    )
    return ok(data=PaginatedResponse(items=results, total=total, page=page, page_size=page_size))


@router.post("", response_model=ApiResponse[TagResponse])
def create_tag(tag_in: TagCreate, db: Session = Depends(get_db_session)):
    """Create tag."""
    response, validation_error = create_tag_service(db, tag_in)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(data=response, message="Tag created successfully")


@router.delete("/{tag_id}", response_model=ApiResponse)
def delete_tag(tag_id: int, db: Session = Depends(get_db_session)):
    """Delete tag."""
    validation_error = delete_tag_service(db, tag_id)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(message="Tag deleted successfully")
