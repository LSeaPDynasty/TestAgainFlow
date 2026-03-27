"""Profiles router."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db_session
from app.schemas.common import ApiResponse, PaginatedResponse
from app.schemas.profile import ProfileCreate, ProfileDetailResponse, ProfileResponse, ProfileUpdate
from app.services.profile_service import (
    create_profile as create_profile_service,
    delete_profile as delete_profile_service,
    get_profile_detail,
    list_profiles as list_profiles_service,
    update_profile as update_profile_service,
)
from app.utils.pagination import calculate_offset
from app.utils.response import error, ok

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("", response_model=ApiResponse[PaginatedResponse[ProfileResponse]])
def list_profiles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db_session),
):
    """Get profile list."""
    results, total = list_profiles_service(
        db,
        skip=calculate_offset(page, page_size),
        limit=page_size,
    )
    return ok(data=PaginatedResponse(items=results, total=total, page=page, page_size=page_size))


@router.get("/{profile_id}", response_model=ApiResponse[ProfileDetailResponse])
def get_profile(profile_id: int, db: Session = Depends(get_db_session)):
    """Get profile by ID."""
    return ok(data=get_profile_detail(db, profile_id))


@router.post("", response_model=ApiResponse[ProfileResponse])
def create_profile(profile_in: ProfileCreate, db: Session = Depends(get_db_session)):
    """Create profile."""
    response, validation_error = create_profile_service(db, profile_in)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(data=response, message="Profile created successfully")


@router.put("/{profile_id}", response_model=ApiResponse[ProfileResponse])
def update_profile(profile_id: int, profile_in: ProfileUpdate, db: Session = Depends(get_db_session)):
    """Update profile."""
    response, validation_error = update_profile_service(db, profile_id=profile_id, profile_in=profile_in)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(data=response, message="Profile updated successfully")


@router.delete("/{profile_id}", response_model=ApiResponse)
def delete_profile(profile_id: int, db: Session = Depends(get_db_session)):
    """Delete profile."""
    delete_profile_service(db, profile_id)
    return ok(message="Profile deleted successfully")
