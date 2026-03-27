"""
Screen schemas
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class ScreenBase(BaseModel):
    """Base screen fields"""
    name: str = Field(..., min_length=1, max_length=100, description="Screen name")
    activity: Optional[str] = Field(None, max_length=255, description="Activity path")
    description: Optional[str] = Field(None, description="Description")
    project_id: Optional[int] = Field(None, description="Project ID")


class ScreenCreate(ScreenBase):
    """Screen creation schema"""
    pass


class ScreenUpdate(BaseModel):
    """Screen update schema - all fields optional"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    activity: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    project_id: Optional[int] = None


class LocatorSchema(BaseModel):
    """Locator schema"""
    id: int
    type: str = Field(..., description="Locator type")
    value: str = Field(..., description="Locator value")
    priority: int = Field(..., description="Priority, 1 is highest")

    class Config:
        from_attributes = True


class ElementBriefSchema(BaseModel):
    """Brief element info for screen detail"""
    id: int
    name: str

    class Config:
        from_attributes = True


class ScreenResponse(ScreenBase):
    """Screen response schema"""
    id: int
    element_count: int = Field(0, description="Number of elements")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScreenDetailResponse(ScreenResponse):
    """Screen detail with elements"""
    elements: List[ElementBriefSchema] = Field(default_factory=list)
