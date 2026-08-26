from pydantic import BaseModel, Field, field_validator, ConfigDict, AliasChoices
from typing import Optional, Dict, Any, Union
from datetime import datetime
import uuid


def normalize_print_language(value: Optional[str]) -> str:
    if not value:
        return "en"
    lang = str(value).strip().lower().replace("_", "-")
    if lang.startswith("it"):
        return "it"
    return "en"


class PrintGenerateRequest(BaseModel):
    asset_id: uuid.UUID
    template_id: Union[str, int]
    options: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("template_id", mode="before")
    @classmethod
    def convert_template_id(cls, v):
        return str(v)

    @field_validator("options", mode="before")
    @classmethod
    def coerce_options(cls, v):
        return v or {}


class PrintGenerateResponse(BaseModel):
    print_id: uuid.UUID
    status: str = "completed"
    file_url: str
    file_size: int
    generated_at: datetime


class QRCodeRequest(BaseModel):
    text: str = Field(..., description="Text to encode in QR code")
    size: int = Field(200, ge=50, le=500, description="QR code size in pixels")


class PrintedKitRequest(BaseModel):
    """Accepts snake_case (canonical) and camelCase aliases from the frontend."""

    model_config = ConfigDict(populate_by_name=True)

    include_assets: bool = Field(
        True,
        description="Include asset sheets",
        validation_alias=AliasChoices("include_assets", "includeAssets"),
    )
    include_sites: bool = Field(
        True,
        description="Include site information",
        validation_alias=AliasChoices("include_sites", "includeSites"),
    )
    include_contacts: bool = Field(
        True,
        description="Include contacts",
        validation_alias=AliasChoices("include_contacts", "includeContacts"),
    )
    include_suppliers: bool = Field(
        True,
        description="Include suppliers",
        validation_alias=AliasChoices("include_suppliers", "includeSuppliers"),
    )
    format: str = Field("pdf", description="Output format (pdf)")
    language: str = Field(
        "en",
        description="Language for the printed kit (en/it)",
        validation_alias=AliasChoices("language", "lang"),
    )

    @field_validator("language", mode="before")
    @classmethod
    def coerce_language(cls, v):
        return normalize_print_language(v)


class PrintedKitResponse(BaseModel):
    file_url: str
    file_size: int
    generated_at: datetime
