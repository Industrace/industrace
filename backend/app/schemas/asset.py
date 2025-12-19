# backend/schemas/asset.py

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import uuid
from app.schemas.validators import *

from .site import Site
from .asset_type import AssetType
from .location import LocationRead
from .asset_document import AssetDocument
from .asset_photo import AssetPhoto
from .manufacturer import Manufacturer as ManufacturerSchema
from .asset_status import AssetStatus as AssetStatusSchema
from .contact import Contact
from .asset_interface import AssetInterface, AssetInterfaceUpdate, AssetInterfaceCreate


class AssetContact(BaseModel):
    """Asset contact with role information"""
    contact: Contact
    role: str = Field(..., description="Contact role: owner, point_of_contact, other, technical, administrative")
    
    class Config:
        from_attributes = True


class AssetContactCreate(BaseModel):
    """Create asset contact with role"""
    contact_id: uuid.UUID
    role: str = Field(..., description="Contact role: owner, point_of_contact, other, technical, administrative")
    
    class Config:
        from_attributes = True


class AssetCustomFieldUpdate(BaseModel):
    custom_fields: Dict[str, Optional[Any]]


class AssetSummary(BaseModel):
    id: uuid.UUID
    name: str

    class Config:
        from_attributes = True


class AssetBase(BaseModel):
    id: Optional[uuid.UUID]
    tenant_id: Optional[uuid.UUID]
    site_id: Optional[uuid.UUID]
    asset_type_id: Optional[uuid.UUID]
    location_id: Optional[uuid.UUID]
    area_id: Optional[uuid.UUID]
    name: str = Field(..., max_length=255, description="Asset name")
    tag: Optional[str] = Field(None, max_length=100, description="Asset tag")
    serial_number: Optional[str] = Field(None, max_length=100, description="Serial number")
    model: Optional[str] = Field(None, max_length=100, description="Model")
    manufacturer_id: Optional[uuid.UUID]
    firmware_version: Optional[str] = Field(None, max_length=50, description="Firmware version")
    description: Optional[str] = Field(None, max_length=10000, description="Asset description")
    custom_fields: Dict[str, Any]
    map_x: Optional[float] = None
    map_y: Optional[float] = None
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    status_id: Optional[uuid.UUID] = None
    security_zone_id: Optional[uuid.UUID] = None
    installation_date: Optional[date] = None
    business_criticality: Optional[str] = Field(None, max_length=50, description="Business criticality")
    protocols: Optional[List[str]] = []
    interfaces: Optional[List[AssetInterface]] = None
    manufacturer: Optional[ManufacturerSchema] = None
    site: Optional[Site] = None
    asset_type: Optional[AssetType] = None
    location: Optional[LocationRead] = None
    area_name: Optional[str] = None
    area_code: Optional[str] = None
    status: Optional[AssetStatusSchema] = None

    # Risk Scoring fields
    impact_value: Optional[int] = 1
    purdue_level: Optional[float] = 0.0
    exposure_level: Optional[str] = Field(None, max_length=50, description="Exposure level")
    update_status: Optional[str] = Field(None, max_length=50, description="Update status")
    risk_score: Optional[float] = 0.0

    # Validators
    _validate_impact_value = validator('impact_value', allow_reuse=True)(validate_impact_value)
    _validate_purdue_level = validator('purdue_level', allow_reuse=True)(validate_purdue_level)
    _validate_risk_score = validator('risk_score', allow_reuse=True)(validate_risk_score)
    _validate_business_criticality = validator('business_criticality', allow_reuse=True)(validate_business_criticality)
    _validate_remote_access_type = validator('remote_access_type', allow_reuse=True)(validate_remote_access_type)
    _validate_physical_access_ease = validator('physical_access_ease', allow_reuse=True)(validate_physical_access_ease)

    last_risk_assessment: Optional[datetime] = None
    remote_access: Optional[bool] = False
    remote_access_type: Optional[str] = Field(None, max_length=20, description="Remote access type")
    last_update_date: Optional[datetime] = None
    physical_access_ease: Optional[str] = Field(None, max_length=50, description="Physical access ease")

    documents: List[AssetDocument] = []
    photos: List[AssetPhoto] = []
    contacts: List[Contact] = []

    class Config:
        from_attributes = True


class AssetUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255, description="Asset name")
    tag: Optional[str] = Field(None, max_length=100, description="Asset tag")
    serial_number: Optional[str] = Field(None, max_length=100, description="Serial number")
    model: Optional[str] = Field(None, max_length=100, description="Model")
    manufacturer_id: Optional[uuid.UUID] = None
    firmware_version: Optional[str] = Field(None, max_length=50, description="Firmware version")
    description: Optional[str] = Field(None, max_length=10000, description="Asset description")
    custom_fields: Optional[Dict[str, Any]] = None
    map_x: Optional[float] = None
    map_y: Optional[float] = None
    remote_access: Optional[bool] = None
    remote_access_type: Optional[str] = Field(None, max_length=20, description="Remote access type")
    last_update_date: Optional[datetime] = None
    physical_access_ease: Optional[str] = Field(None, max_length=50, description="Physical access ease")
    installation_date: Optional[date] = None
    business_criticality: Optional[str] = Field(None, max_length=50, description="Business criticality")
    protocols: Optional[List[str]] = None
    interfaces: Optional[List[AssetInterfaceUpdate]] = None

    site_id: Optional[uuid.UUID] = None
    asset_type_id: Optional[uuid.UUID] = None
    location_id: Optional[uuid.UUID] = None
    area_id: Optional[uuid.UUID] = None
    status_id: Optional[uuid.UUID] = None
    security_zone_id: Optional[uuid.UUID] = None

    # Risk Scoring fields
    impact_value: Optional[int] = None
    purdue_level: Optional[float] = None
    exposure_level: Optional[str] = Field(None, max_length=50, description="Exposure level")
    update_status: Optional[str] = Field(None, max_length=50, description="Update status")
    risk_score: Optional[float] = None

    # Validators
    _validate_impact_value = validator('impact_value', allow_reuse=True)(validate_impact_value)
    _validate_purdue_level = validator('purdue_level', allow_reuse=True)(validate_purdue_level)
    _validate_risk_score = validator('risk_score', allow_reuse=True)(validate_risk_score)
    _validate_business_criticality = validator('business_criticality', allow_reuse=True)(validate_business_criticality)
    _validate_remote_access_type = validator('remote_access_type', allow_reuse=True)(validate_remote_access_type)
    _validate_physical_access_ease = validator('physical_access_ease', allow_reuse=True)(validate_physical_access_ease)


class AssetCreate(BaseModel):
    name: str = Field(..., max_length=255, description="Asset name")
    tag: Optional[str] = Field(None, max_length=100, description="Asset tag")
    serial_number: Optional[str] = Field(None, max_length=100, description="Serial number")
    model: Optional[str] = Field(None, max_length=100, description="Model")
    manufacturer_id: Optional[uuid.UUID] = None
    firmware_version: Optional[str] = Field(None, max_length=50, description="Firmware version")
    description: Optional[str] = Field(None, max_length=10000, description="Asset description")
    custom_fields: Dict[str, Any] = {}
    remote_access: Optional[bool] = False
    remote_access_type: Optional[str] = Field(None, max_length=20, description="Remote access type")
    last_update_date: Optional[datetime] = None
    physical_access_ease: Optional[str] = Field(None, max_length=50, description="Physical access ease")
    installation_date: Optional[date] = None
    business_criticality: Optional[str] = Field(None, max_length=50, description="Business criticality")
    protocols: Optional[List[str]] = []
    interfaces: Optional[List[AssetInterfaceCreate]] = None
    site_id: uuid.UUID
    asset_type_id: Optional[uuid.UUID] = None
    location_id: Optional[uuid.UUID] = None
    area_id: Optional[uuid.UUID] = None
    map_x: Optional[float] = None
    map_y: Optional[float] = None
    status_id: Optional[uuid.UUID] = None
    security_zone_id: Optional[uuid.UUID] = None

    # Risk Scoring fields
    impact_value: Optional[int] = 1
    purdue_level: Optional[float] = 0.0
    exposure_level: Optional[str] = Field(None, max_length=50, description="Exposure level")
    update_status: Optional[str] = Field(None, max_length=50, description="Update status")
    risk_score: Optional[float] = 0.0

    # Validators
    _validate_impact_value = validator('impact_value', allow_reuse=True)(validate_impact_value)
    _validate_purdue_level = validator('purdue_level', allow_reuse=True)(validate_purdue_level)
    _validate_risk_score = validator('risk_score', allow_reuse=True)(validate_risk_score)
    _validate_business_criticality = validator('business_criticality', allow_reuse=True)(validate_business_criticality)
    _validate_remote_access_type = validator('remote_access_type', allow_reuse=True)(validate_remote_access_type)
    _validate_physical_access_ease = validator('physical_access_ease', allow_reuse=True)(validate_physical_access_ease)


class AssetRead(AssetBase):
    location_id: Optional[uuid.UUID]
    contacts: List[Contact] = []
    protocols: Optional[List[str]] = []

    class Config:
        from_attributes = True


class AssetBulkUpdateRequest(BaseModel):
    ids: List[uuid.UUID]
    fields: Dict[str, Any]


class AssetBulkSoftDeleteRequest(BaseModel):
    ids: List[uuid.UUID]


class RiskScoreRequest(BaseModel):
    asset_id: uuid.UUID


class RiskScoreResponse(BaseModel):
    asset_id: uuid.UUID
    risk_score: Optional[float]
    risk_level: str
    risk_severity: str
    breakdown: Dict[str, Any]


class RiskOverviewResponse(BaseModel):
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    total_assets: int
    average_risk_score: float
    top_risk_assets: List[Dict[str, Any]]
