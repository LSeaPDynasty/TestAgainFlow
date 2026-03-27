"""Service helpers for tags endpoints."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from app.repositories.tag_repo import TagRepository
from app.schemas.tag import TagCreate, TagResponse


@dataclass
class ServiceValidationError:
    code: int
    message: str
    data: Optional[dict] = None


def list_tags(db: Session, *, skip: int, limit: int):
    repo = TagRepository(db)
    return repo.list_with_usage_count(skip=skip, limit=limit)


def create_tag(db: Session, tag_in: TagCreate) -> tuple[Optional[TagResponse], Optional[ServiceValidationError]]:
    repo = TagRepository(db)
    if repo.get_by_name(tag_in.name):
        return None, ServiceValidationError(code=4009, message="Tag name already exists")
    tag = repo.create(tag_in.model_dump())
    return TagResponse(id=tag.id, name=tag.name, color=tag.color, usage_count=0), None


def delete_tag(db: Session, tag_id: int) -> Optional[ServiceValidationError]:
    repo = TagRepository(db)
    if not repo.delete(tag_id):
        return ServiceValidationError(code=4004, message=f"Tag not found: id={tag_id}")
    return None
