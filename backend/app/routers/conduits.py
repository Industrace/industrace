# backend/app/routers/conduits.py
import uuid
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel, Field, ConfigDict

from app.database import get_db
from app.models import User, Conduit, SecurityZone
from app.services.auth import get_current_user
from app.services.audit_decorator import audit_log_action
from app.services.isa62443_compliance_engine import ISA62443ComplianceEngine
from app.errors.exceptions import ErrorCodeException
from app.errors.error_codes import ErrorCode
from app.services.feature_guard import require_iec62443_enabled
from app.services.rbac import require_section_access

router = APIRouter(
    prefix="/conduits",
    tags=["Conduits"],
    dependencies=[
        Depends(require_iec62443_enabled),
        Depends(require_section_access("compliance")),
    ],
)


class ConduitBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    from_zone_id: uuid.UUID
    to_zone_id: uuid.UUID
    conduit_type: Optional[str] = Field(None, max_length=50)
    is_encrypted: bool = False
    encryption_type: Optional[str] = Field(None, max_length=50)
    authentication_required: bool = True
    authentication_method: Optional[str] = Field(None, max_length=50)
    protocol: Optional[str] = Field(None, max_length=50)
    port_range: Optional[str] = Field(None, max_length=100)
    allowed_direction: str = Field("bidirectional", pattern="^(unidirectional|bidirectional|request_response)$")
    security_level_target: Optional[int] = Field(None, ge=1, le=4)
    flow_justification: Optional[str] = None
    ownership: Optional[str] = Field(None, max_length=255)


class ConduitCreate(ConduitBase):
    pass


class ConduitUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    from_zone_id: Optional[uuid.UUID] = None
    to_zone_id: Optional[uuid.UUID] = None
    conduit_type: Optional[str] = Field(None, max_length=50)
    is_encrypted: Optional[bool] = None
    encryption_type: Optional[str] = Field(None, max_length=50)
    authentication_required: Optional[bool] = None
    authentication_method: Optional[str] = Field(None, max_length=50)
    protocol: Optional[str] = Field(None, max_length=50)
    port_range: Optional[str] = Field(None, max_length=100)
    allowed_direction: Optional[str] = Field(None, pattern="^(unidirectional|bidirectional|request_response)$")
    security_level_target: Optional[int] = Field(None, ge=1, le=4)
    flow_justification: Optional[str] = None
    ownership: Optional[str] = Field(None, max_length=255)


class ConduitResponse(ConduitBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    security_level_achieved: Optional[int] = None
    sl_achieved_source: Optional[str] = None  # assessment | preliminary | none
    compliance_status: str
    last_assessment_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    from_zone_name: Optional[str] = None
    to_zone_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


def _conduit_response(db: Session, conduit: Conduit) -> ConduitResponse:
    meta = ISA62443ComplianceEngine.get_conduit_sl_metadata(db, conduit)
    response = ConduitResponse.model_validate(conduit)
    response.sl_achieved_source = meta["sl_achieved_source"]
    if conduit.from_zone:
        response.from_zone_name = conduit.from_zone.name
    if conduit.to_zone:
        response.to_zone_name = conduit.to_zone.name
    return response


@router.get("", response_model=List[ConduitResponse])
def list_conduits(
    zone_id: Optional[uuid.UUID] = Query(None, description="Filter by zone (from or to)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List conduits"""
    query = (
        db.query(Conduit)
        .filter(
            Conduit.tenant_id == current_user.tenant_id,
            Conduit.deleted_at.is_(None)
        )
    )
    
    if zone_id:
        query = query.filter(
            or_(
                Conduit.from_zone_id == zone_id,
                Conduit.to_zone_id == zone_id
            )
        )
    
    conduits = query.order_by(Conduit.name).all()
    
    return [_conduit_response(db, c) for c in conduits]


@router.get("/{conduit_id}", response_model=ConduitResponse)
def get_conduit(
    conduit_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get conduit details"""
    conduit = (
        db.query(Conduit)
        .filter(
            Conduit.id == conduit_id,
            Conduit.tenant_id == current_user.tenant_id,
            Conduit.deleted_at.is_(None)
        )
        .first()
    )
    
    if not conduit:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)
    
    return _conduit_response(db, conduit)


@router.post("", response_model=ConduitResponse, status_code=201)
@audit_log_action("create_conduit", "Conduit", model_class=Conduit)
def create_conduit(
    conduit_data: ConduitCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new conduit"""
    # Validate zones belong to tenant
    from_zone = (
        db.query(SecurityZone)
        .filter(
            SecurityZone.id == conduit_data.from_zone_id,
            SecurityZone.tenant_id == current_user.tenant_id
        )
        .first()
    )
    
    to_zone = (
        db.query(SecurityZone)
        .filter(
            SecurityZone.id == conduit_data.to_zone_id,
            SecurityZone.tenant_id == current_user.tenant_id
        )
        .first()
    )
    
    if not from_zone or not to_zone:
        raise ErrorCodeException(
            status_code=404,
            error_code=ErrorCode.ASSET_NOT_FOUND,
            detail="One or both zones not found"
        )
    
    if from_zone.id == to_zone.id:
        raise ErrorCodeException(
            status_code=400,
            error_code=ErrorCode.ASSET_NOT_FOUND,
            detail="From and to zones cannot be the same"
        )
    
    conduit = Conduit(
        tenant_id=current_user.tenant_id,
        **conduit_data.model_dump()
    )
    
    db.add(conduit)
    db.commit()
    db.refresh(conduit)
    
    return _conduit_response(db, conduit)


@router.put("/{conduit_id}", response_model=ConduitResponse)
@audit_log_action("update_conduit", "Conduit", model_class=Conduit)
def update_conduit(
    conduit_id: uuid.UUID,
    conduit_data: ConduitUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a conduit"""
    conduit = (
        db.query(Conduit)
        .filter(
            Conduit.id == conduit_id,
            Conduit.tenant_id == current_user.tenant_id,
            Conduit.deleted_at.is_(None)
        )
        .first()
    )
    
    if not conduit:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)
    
    # Update fields
    update_data = conduit_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(conduit, key, value)
    
    db.commit()
    db.refresh(conduit)
    
    return _conduit_response(db, conduit)


@router.delete("/{conduit_id}", status_code=204)
@audit_log_action("delete_conduit", "Conduit", model_class=Conduit)
def delete_conduit(
    conduit_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a conduit (soft delete)"""
    conduit = (
        db.query(Conduit)
        .filter(
            Conduit.id == conduit_id,
            Conduit.tenant_id == current_user.tenant_id,
            Conduit.deleted_at.is_(None)
        )
        .first()
    )
    
    if not conduit:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)
    
    conduit.deleted_at = datetime.utcnow()
    db.commit()
    
    return None


@router.post("/{conduit_id}/calculate-sl", response_model=ConduitResponse)
@audit_log_action("calculate_conduit_sl", "Conduit", model_class=Conduit)
def calculate_conduit_security_level(
    conduit_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Recalculate Security Level Achieved for a conduit"""
    conduit = (
        db.query(Conduit)
        .filter(
            Conduit.id == conduit_id,
            Conduit.tenant_id == current_user.tenant_id
        )
        .first()
    )
    
    if not conduit:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)
    
    updated = ISA62443ComplianceEngine.update_conduit_iec62443_levels(db, str(conduit_id))
    return _conduit_response(db, updated)

