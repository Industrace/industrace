from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime


class PrintTemplateBase(BaseModel):
    key: str = Field(..., max_length=100, description="Template key")
    name: str = Field(..., max_length=255, description="Template name")
    name_translations: Optional[Dict[str, str]] = Field(default_factory=dict)
    description: Optional[str] = Field(None, max_length=10000, description="Template description")
    description_translations: Optional[Dict[str, str]] = Field(default_factory=dict)
    icon: Optional[str] = Field(None, max_length=100, description="Icon class")
    component: Optional[str] = Field(None, max_length=100, description="Component name")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict)
    tenant_id: Optional[UUID] = None


class PrintTemplateCreate(PrintTemplateBase):
    pass


class PrintTemplateUpdate(BaseModel):
    name: Optional[str] = None
    name_translations: Optional[Dict[str, str]] = None
    description: Optional[str] = None
    description_translations: Optional[Dict[str, str]] = None
    icon: Optional[str] = None
    component: Optional[str] = None
    options: Optional[Dict[str, Any]] = None


class PrintTemplate(PrintTemplateBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
