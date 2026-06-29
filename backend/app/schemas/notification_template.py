from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime


class NotificationTemplateBase(BaseModel):
    template_code: str = Field(..., max_length=50, description="Template code (unique identifier)")
    name: str = Field(..., max_length=255, description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    subject_template: str = Field(..., max_length=500, description="Email subject template")
    body_template_html: str = Field(..., description="HTML email body template")
    body_template_text: Optional[str] = Field(None, description="Plain text email body template")
    variables: Optional[List[str]] = Field(default_factory=list, description="Available template variables")
    enabled: bool = Field(default=True, description="Whether template is enabled")


class NotificationTemplateCreate(NotificationTemplateBase):
    tenant_id: Optional[UUID] = None


class NotificationTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    subject_template: Optional[str] = None
    body_template_html: Optional[str] = None
    body_template_text: Optional[str] = None
    variables: Optional[List[str]] = None
    enabled: Optional[bool] = None


class NotificationTemplateRead(NotificationTemplateBase):
    id: UUID
    tenant_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

