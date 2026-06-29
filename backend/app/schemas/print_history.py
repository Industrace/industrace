from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class PrintHistoryBase(BaseModel):
    asset_id: UUID = Field(..., description="Asset ID")
    template_id: int = Field(..., description="Template ID")
    file_path: Optional[str] = Field(None, description="File path")
    file_size: Optional[int] = Field(None, description="File size")
    status: str = Field(default="completed", description="Generation status")
    options: Dict[str, Any] = Field(
        default_factory=dict, description="Print options"
    )
    generated_by: Optional[UUID] = Field(
        None, description="User ID that generated the print"
    )


class PrintHistoryCreate(PrintHistoryBase):
    pass


class PrintHistory(PrintHistoryBase):
    id: UUID
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)
