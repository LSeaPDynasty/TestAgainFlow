"""
Import schemas for bulk data import
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class LocatorImportSchema(BaseModel):
    """Locator import schema"""
    type: str = Field(..., description="Locator type: resource-id, text, xpath, etc.")
    value: str = Field(..., description="Locator value")
    priority: int = Field(1, ge=1, description="Priority, 1 is highest")


class ElementImportSchema(BaseModel):
    """Element import schema"""
    name: str = Field(..., max_length=100, description="Element name")
    description: Optional[str] = Field(None, description="Description")
    locators: List[LocatorImportSchema] = Field(..., min_items=1, description="Locator list")


class ScreenImportSchema(BaseModel):
    """Screen import schema"""
    name: str = Field(..., min_length=1, max_length=100, description="Screen name")
    activity: Optional[str] = Field(None, max_length=255, description="Activity path")
    description: Optional[str] = Field(None, description="Description")
    elements: List[ElementImportSchema] = Field(default_factory=list, description="Elements in this screen")


class ProjectImportSchema(BaseModel):
    """Project import schema (optional)"""
    name: str = Field(..., max_length=100, description="Project name")
    description: Optional[str] = Field(None, description="Project description")


class AppImportSchema(BaseModel):
    """App import schema (optional)"""
    name: str = Field(..., max_length=100, description="App name")
    package_name: Optional[str] = Field(None, max_length=255, description="Package name")
    description: Optional[str] = Field(None, description="App description")


class BulkImportRequest(BaseModel):
    """Bulk import request schema"""
    version: Optional[str] = Field(None, description="Template version")
    project: Optional[ProjectImportSchema] = None
    app: Optional[AppImportSchema] = None
    screens: List[ScreenImportSchema] = Field(..., min_items=1, description="Screens to import")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Import options")


class ElementsOnlyImportRequest(BaseModel):
    """Elements-only import request (import to existing screen)"""
    target_screen: str = Field(..., description="Target screen name")
    elements: List[ElementImportSchema] = Field(..., min_items=1, description="Elements to import")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Import options")


class ImportResultSchema(BaseModel):
    """Import result schema"""
    success: bool = Field(..., description="Overall success status")
    message: str = Field(..., description="Result message")
    created_screens: int = Field(0, description="Number of screens created")
    created_elements: int = Field(0, description="Number of elements created")
    skipped_screens: List[str] = Field(default_factory=list, description="Names of skipped screens (already exist)")
    skipped_elements: List[str] = Field(default_factory=list, description="Names of skipped elements (already exist)")
    errors: List[str] = Field(default_factory=list, description="Error messages")
