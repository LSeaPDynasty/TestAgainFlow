"""
Tag schemas
"""
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class TagBase(BaseModel):
    """Base tag fields"""
    name: str = Field(..., min_length=1, max_length=50, description="Tag name")
    color: str = Field("#3b82f6", description="Tag color (hex)")


class TagCreate(TagBase):
    """Tag creation schema"""
    pass


class TagUpdate(BaseModel):
    """Tag update schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    color: Optional[str] = None


class TagResponse(TagBase):
    """Tag response schema"""
    id: int
    usage_count: int = Field(0, description="Usage count")

    class Config:
        from_attributes = True
