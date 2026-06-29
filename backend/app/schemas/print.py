from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
import uuid


class PrintGenerateRequest(BaseModel):
    asset_id: uuid.UUID
    template_id: Union[str, int]  # Può essere ID (int) o key (str) del template
    options: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @field_validator("template_id", mode="before")
    @classmethod
    def convert_template_id(cls, v):
        return str(v)


class PrintGenerateResponse(BaseModel):
    print_id: uuid.UUID
    file_url: str
    file_size: int
    generated_at: datetime


class QRCodeRequest(BaseModel):
    text: str = Field(..., description="Text to encode in QR code")
    size: int = Field(200, ge=50, le=500, description="QR code size in pixels")


class PrintHistoryQuery(BaseModel):
    asset_id: Optional[uuid.UUID] = None
    template_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)


class PrintedKitRequest(BaseModel):
    include_assets: bool = Field(True, description="Include asset sheets")
    include_sites: bool = Field(True, description="Include site information")
    include_contacts: bool = Field(True, description="Include contacts")
    include_suppliers: bool = Field(True, description="Include suppliers")
    include_photos: bool = Field(True, description="Include asset photos")
    include_documents: bool = Field(True, description="Include asset documents")
    format: str = Field("pdf", description="Output format (pdf)")
    language: str = Field("en", description="Language for the printed kit (en/it)")


class PrintedKitResponse(BaseModel):
    file_url: str
    file_size: int
    generated_at: datetime
