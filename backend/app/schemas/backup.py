"""
Backup schemas
"""
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class BackupCreate(BaseModel):
    """Backup creation request"""
    resource: str = Field(..., description="Resource type: all, elements, flows, etc.")
    description: Optional[str] = Field(None, description="Backup description")


class BackupResponse(BaseModel):
    """Backup response"""
    id: str
    resource: str
    description: Optional[str]
    size_bytes: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class RestoreRequest(BaseModel):
    """Restore request"""
    resource: str = Field(..., description="Resource type")
    confirm: bool = Field(False, description="Confirmation flag")


class RestoreResponse(BaseModel):
    """Restore response"""
    restored_counts: dict = Field(..., description="Restored record counts")
