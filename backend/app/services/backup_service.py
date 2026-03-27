"""Service helpers for backup endpoints."""
from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models.backup import Backup
from app.repositories.backup_repo import BackupRepository
from app.schemas.backup import BackupCreate, BackupResponse, RestoreResponse


def list_backups(db: Session, resource: Optional[str]) -> list[BackupResponse]:
    repo = BackupRepository(db)
    backups = repo.list_by_resource(resource)
    return [
        BackupResponse(
            id=backup.id,
            resource=backup.resource,
            description=backup.description,
            size_bytes=backup.size_bytes,
            created_at=backup.created_at,
        )
        for backup in backups
    ]


def create_backup(db: Session, backup_in: BackupCreate) -> BackupResponse:
    backup_id = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    backup = Backup(
        id=backup_id,
        resource=backup_in.resource,
        description=backup_in.description,
        size_bytes=None,
    )
    db.add(backup)
    db.commit()
    return BackupResponse(
        id=backup.id,
        resource=backup.resource,
        description=backup.description,
        size_bytes=None,
        created_at=backup.created_at,
    )


def run_backup(backup_id: str, resource: str):
    """Create mock backup file."""
    os.makedirs(settings.backups_dir, exist_ok=True)
    backup_file = os.path.join(settings.backups_dir, f"{backup_id}.sql")
    with open(backup_file, "w", encoding="utf-8") as f:
        f.write(f"-- Backup {backup_id} for {resource}\n")


def restore_backup() -> RestoreResponse:
    return RestoreResponse(
        restored_counts={
            "screens": 0,
            "elements": 0,
            "steps": 0,
            "flows": 0,
            "testcases": 0,
        }
    )


def delete_backup(db: Session, backup_id: str):
    backup = db.get(Backup, backup_id)
    if backup:
        db.delete(backup)
        db.commit()

    backup_file = os.path.join(settings.backups_dir, f"{backup_id}.sql")
    if os.path.exists(backup_file):
        os.remove(backup_file)
