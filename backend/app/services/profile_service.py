"""Service helpers for profiles endpoints."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from app.models.tag import Tag
from app.repositories.profile_repo import ProfileRepository
from app.schemas.profile import (
    ProfileCreate,
    ProfileDetailResponse,
    ProfileResponse,
    ProfileUpdate,
    TagSchema,
)
from app.utils.exceptions import NotFoundError


@dataclass
class ServiceValidationError:
    code: int
    message: str
    data: Optional[dict] = None


def list_profiles(db: Session, *, skip: int, limit: int):
    repo = ProfileRepository(db)
    return repo.list_with_details(skip=skip, limit=limit)


def get_profile_detail(db: Session, profile_id: int) -> ProfileDetailResponse:
    repo = ProfileRepository(db)
    profile = repo.get_with_variables(profile_id)
    if not profile:
        raise NotFoundError(f"Profile not found: id={profile_id}")

    return ProfileDetailResponse(
        id=profile.id,
        name=profile.name,
        description=profile.description,
        variable_count=len(profile.variables) if profile.variables else 0,
        variables=profile.variables or {},
        tags=[TagSchema(id=t.id, name=t.name) for t in profile.tags],
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


def create_profile(
    db: Session,
    profile_in: ProfileCreate,
) -> tuple[Optional[ProfileResponse], Optional[ServiceValidationError]]:
    repo = ProfileRepository(db)
    if repo.get_by_name(profile_in.name):
        return None, ServiceValidationError(code=4009, message="Profile name already exists")

    profile = repo.create(profile_in.model_dump(exclude={"tag_ids"}))

    if profile_in.tag_ids:
        for tag_id in profile_in.tag_ids:
            tag = db.get(Tag, tag_id)
            if tag:
                profile.tags.append(tag)
        db.commit()

    return build_profile_response(profile), None


def update_profile(
    db: Session,
    *,
    profile_id: int,
    profile_in: ProfileUpdate,
) -> tuple[Optional[ProfileResponse], Optional[ServiceValidationError]]:
    repo = ProfileRepository(db)
    profile = repo.get(profile_id)
    if not profile:
        raise NotFoundError(f"Profile not found: id={profile_id}")

    if profile_in.name and profile_in.name != profile.name and repo.get_by_name(profile_in.name):
        return None, ServiceValidationError(code=4009, message="Profile name already exists")

    update_data = {
        k: v
        for k, v in profile_in.model_dump().items()
        if v is not None and k != "tag_ids"
    }
    updated = repo.update(profile_id, update_data)

    if profile_in.tag_ids is not None:
        updated.tags.clear()
        for tag_id in profile_in.tag_ids:
            tag = db.get(Tag, tag_id)
            if tag:
                updated.tags.append(tag)
        db.commit()

    return build_profile_response(updated), None


def delete_profile(db: Session, profile_id: int) -> None:
    repo = ProfileRepository(db)
    if not repo.delete(profile_id):
        raise NotFoundError(f"Profile not found: id={profile_id}")


def build_profile_response(profile: object) -> ProfileResponse:
    return ProfileResponse(
        id=profile.id,
        name=profile.name,
        description=profile.description,
        variable_count=len(profile.variables) if profile.variables else 0,
        tags=[TagSchema(id=t.id, name=t.name) for t in profile.tags],
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )
