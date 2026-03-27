"""
Profile schemas
"""
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from datetime import datetime


class ProfileBase(BaseModel):
    """Base profile fields"""
    name: str = Field(..., min_length=1, max_length=100, description="Profile name")
    description: Optional[str] = Field(None, description="Description")


class ProfileCreate(ProfileBase):
    """Profile creation schema"""
    variables: Optional[Dict[str, str]] = Field(None, description="Environment variables")
    tag_ids: Optional[List[int]] = Field(default_factory=list, description="Tag IDs")


class ProfileUpdate(BaseModel):
    """Profile update schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    variables: Optional[Dict[str, str]] = None
    tag_ids: Optional[List[int]] = None


class TagSchema(BaseModel):
    """Tag schema"""
    id: int
    name: str

    class Config:
        from_attributes = True


class ProfileResponse(ProfileBase):
    """Profile response schema"""
    id: int
    variable_count: int = Field(0, description="Number of variables")
    tags: List[TagSchema] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProfileDetailResponse(ProfileResponse):
    """Profile detail with variables"""
    variables: Dict[str, str] = Field(default_factory=dict)
