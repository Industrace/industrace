from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import Dict, Optional
from datetime import datetime


class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: Dict[str, int]
    is_inheritable: bool = True
    parent_role_id: Optional[UUID] = None
    is_active: bool = True  


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[Dict[str, int]] = None
    is_inheritable: Optional[bool] = None
    parent_role_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class RoleRead(RoleBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
