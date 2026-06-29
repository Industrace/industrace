from pydantic import BaseModel, ConfigDict
from typing import Optional
import uuid
from datetime import datetime


class AuditLog(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    user_id: uuid.UUID
    action: str
    entity: str
    entity_id: Optional[uuid.UUID]
    entity_name: Optional[str] = None
    timestamp: datetime
    ip_address: Optional[str]
    old_data: Optional[str]
    new_data: Optional[str]
    description: Optional[str]

    model_config = ConfigDict(from_attributes=True)
