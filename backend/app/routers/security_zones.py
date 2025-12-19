# backend/app/routers/security_zones.py
import uuid
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel, Field

from app.database import get_db
from app.models import User, SecurityZone, Asset, Location
from app.models.asset_zone_membership import AssetZoneMembership
from app.services.auth import get_current_user
from app.services.audit_decorator import audit_log_action
from app.services.isa62443_compliance_engine import ISA62443ComplianceEngine
from app.services.zone_risk_calculator import ZoneRiskCalculator
from app.errors.exceptions import ErrorCodeException
from app.errors.error_codes import ErrorCode
from app.crud import asset_zone_memberships as crud_memberships
from app.schemas.asset_zone_membership import (
    AssetZoneMembershipCreate,
    AssetZoneMembershipUpdate,
    AssetZoneMembershipRead
)

router = APIRouter(prefix="/security-zones", tags=["Security Zones"])


class SecurityZoneBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    site_id: Optional[uuid.UUID] = None
    zone_type: Optional[str] = Field(None, max_length=50)
    security_level_target: Optional[int] = Field(None, ge=1, le=4)
    is_dmz: bool = False
    is_air_gapped: bool = False
    network_segment: Optional[str] = Field(None, max_length=100)


class SecurityZoneCreate(SecurityZoneBase):
    pass


class SecurityZoneUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    site_id: Optional[uuid.UUID] = None
    zone_type: Optional[str] = Field(None, max_length=50)
    security_level_target: Optional[int] = Field(None, ge=1, le=4)
    is_dmz: Optional[bool] = None
    is_air_gapped: Optional[bool] = None
    network_segment: Optional[str] = Field(None, max_length=100)


class SecurityZoneResponse(SecurityZoneBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    security_level_achieved: Optional[int] = None
    security_level_capability: Optional[int] = None
    compliance_status: str
    last_assessment_date: Optional[datetime] = None
    next_assessment_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SecurityZoneDetailResponse(SecurityZoneResponse):
    asset_count: int = 0
    conduit_count: int = 0
    risk_score: Optional[float] = None


@router.get("", response_model=List[SecurityZoneResponse])
def list_security_zones(
    site_id: Optional[uuid.UUID] = Query(None, description="Filter by site"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List security zones"""
    query = (
        db.query(SecurityZone)
        .filter(
            SecurityZone.tenant_id == current_user.tenant_id,
            SecurityZone.deleted_at.is_(None)
        )
    )
    
    if site_id:
        query = query.filter(SecurityZone.site_id == site_id)
    
    zones = query.order_by(SecurityZone.name).all()
    
    return [SecurityZoneResponse.from_orm(zone) for zone in zones]


@router.get("/{zone_id}", response_model=SecurityZoneDetailResponse)
def get_security_zone(
    zone_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get security zone details"""
    zone = (
        db.query(SecurityZone)
        .filter(
            SecurityZone.id == zone_id,
            SecurityZone.tenant_id == current_user.tenant_id,
            SecurityZone.deleted_at.is_(None)
        )
        .first()
    )
    
    if not zone:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)
    
    # Get asset count via AssetZoneMembership (not via Asset.security_zone_id)
    from app.models.asset_zone_membership import AssetZoneMembership
    asset_count = (
        db.query(AssetZoneMembership)
        .filter(
            AssetZoneMembership.security_zone_id == zone.id,
            AssetZoneMembership.tenant_id == current_user.tenant_id,
            AssetZoneMembership.deleted_at.is_(None)
        )
        .count()
    )
    
    # Get conduit count
    from app.models import Conduit
    conduit_count = (
        db.query(Conduit)
        .filter(
            Conduit.deleted_at.is_(None),
            or_(
                Conduit.from_zone_id == zone.id,
                Conduit.to_zone_id == zone.id
            )
        )
        .count()
    )
    
    # Calculate risk
    risk_data = ZoneRiskCalculator.calculate_zone_risk(db, zone)
    
    response = SecurityZoneDetailResponse.from_orm(zone)
    response.asset_count = asset_count
    response.conduit_count = conduit_count
    response.risk_score = risk_data.get('zone_risk_score')
    
    return response


@router.post("", response_model=SecurityZoneResponse, status_code=201)
@audit_log_action("create_security_zone", "SecurityZone", model_class=SecurityZone)
def create_security_zone(
    zone_data: SecurityZoneCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new security zone"""
    zone = SecurityZone(
        tenant_id=current_user.tenant_id,
        **zone_data.dict()
    )
    
    db.add(zone)
    db.commit()
    db.refresh(zone)
    
    return SecurityZoneResponse.from_orm(zone)


@router.put("/{zone_id}", response_model=SecurityZoneResponse)
@audit_log_action("update_security_zone", "SecurityZone", model_class=SecurityZone)
def update_security_zone(
    zone_id: uuid.UUID,
    zone_data: SecurityZoneUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a security zone"""
    zone = (
        db.query(SecurityZone)
        .filter(
            SecurityZone.id == zone_id,
            SecurityZone.tenant_id == current_user.tenant_id,
            SecurityZone.deleted_at.is_(None)
        )
        .first()
    )
    
    if not zone:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)
    
    # Update fields
    update_data = zone_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(zone, key, value)
    
    db.commit()
    db.refresh(zone)
    
    return SecurityZoneResponse.from_orm(zone)


@router.delete("/{zone_id}", status_code=204)
@audit_log_action("delete_security_zone", "SecurityZone", model_class=SecurityZone)
def delete_security_zone(
    zone_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a security zone (soft delete)"""
    zone = (
        db.query(SecurityZone)
        .filter(
            SecurityZone.id == zone_id,
            SecurityZone.tenant_id == current_user.tenant_id,
            SecurityZone.deleted_at.is_(None)
        )
        .first()
    )
    
    if not zone:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)
    
    zone.deleted_at = datetime.utcnow()
    db.commit()
    
    return None


@router.get("/{zone_id}/assets", response_model=List[dict])
def list_zone_assets(
    zone_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List assets in a security zone (via memberships)"""
    from app.crud import asset_zone_memberships as crud_memberships
    from sqlalchemy.orm import joinedload
    
    zone = (
        db.query(SecurityZone)
        .filter(
            SecurityZone.id == zone_id,
            SecurityZone.tenant_id == current_user.tenant_id
        )
        .first()
    )
    
    if not zone:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)
    
    # Get assets via memberships
    memberships = crud_memberships.get_asset_zone_memberships(
        db, current_user.tenant_id, security_zone_id=zone_id
    )
    
    # Get unique assets and their memberships
    asset_ids = list(set([m.asset_id for m in memberships]))
    
    # If no memberships, return empty list
    if not asset_ids:
        return []
    
    try:
        # Load assets with their zone memberships and asset_type
        assets = (
            db.query(Asset)
            .options(
                joinedload(Asset.zone_memberships).joinedload(AssetZoneMembership.security_zone),
                joinedload(Asset.asset_type)
            )
            .filter(
                Asset.id.in_(asset_ids),
                Asset.tenant_id == current_user.tenant_id,
                Asset.deleted_at.is_(None)
            )
            .all()
        )
        
        result = []
        for asset in assets:
            # Get membership in this zone
            membership_in_zone = next(
                (m for m in asset.zone_memberships if m.security_zone_id == zone_id and m.deleted_at is None),
                None
            )
            
            # Get all other zone memberships for this asset
            other_memberships = [
                {
                    'zone_id': str(m.security_zone_id),
                    'zone_name': m.security_zone.name if m.security_zone else None,
                    'role': m.role,
                    'interface_scope': m.interface_scope,
                    'sl_target': m.sl_target
                }
                for m in asset.zone_memberships
                if m.security_zone_id != zone_id and m.deleted_at is None
            ]
            
            result.append({
                'id': str(asset.id),
                'name': asset.name,
                'asset_type': asset.asset_type.name if asset.asset_type else None,
                'risk_score': asset.risk_score,
                'role_in_zone': membership_in_zone.role if membership_in_zone else None,
                'interface_scope': membership_in_zone.interface_scope if membership_in_zone else None,
                'sl_target_override': membership_in_zone.sl_target if membership_in_zone else None,
                'other_zones': other_memberships
            })
        
        return result
    except Exception as e:
        # Log the error for debugging
        import traceback
        print(f"Error in list_zone_assets: {str(e)}")
        print(traceback.format_exc())
        raise ErrorCodeException(
            status_code=500,
            error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            detail=f"Error loading zone assets: {str(e)}"
        )


@router.get("/{zone_id}/compliance", response_model=dict)
def get_zone_compliance(
    zone_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get compliance status for a security zone"""
    zone = (
        db.query(SecurityZone)
        .filter(
            SecurityZone.id == zone_id,
            SecurityZone.tenant_id == current_user.tenant_id
        )
        .first()
    )
    
    if not zone:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)
    
    gap_analysis = ISA62443ComplianceEngine.get_compliance_gap_analysis(db, str(zone_id))
    
    return gap_analysis


@router.post("/{zone_id}/calculate-sl", response_model=SecurityZoneResponse)
@audit_log_action("calculate_zone_sl", "SecurityZone", model_class=SecurityZone)
def calculate_zone_security_level(
    zone_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Recalculate Security Level Achieved for a zone"""
    zone = (
        db.query(SecurityZone)
        .filter(
            SecurityZone.id == zone_id,
            SecurityZone.tenant_id == current_user.tenant_id
        )
        .first()
    )
    
    if not zone:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)
    
    updated_zone = ISA62443ComplianceEngine.update_zone_security_levels(db, str(zone_id))
    
    return SecurityZoneResponse.from_orm(updated_zone)


@router.get("/{zone_id}/risk", response_model=dict)
def get_zone_risk(
    zone_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get risk analysis for a security zone"""
    zone = (
        db.query(SecurityZone)
        .filter(
            SecurityZone.id == zone_id,
            SecurityZone.tenant_id == current_user.tenant_id
        )
        .first()
    )
    
    if not zone:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)
    
    risk_data = ZoneRiskCalculator.calculate_zone_risk(db, zone)
    
    return risk_data


# Asset Zone Memberships endpoints
@router.post("/{zone_id}/memberships", response_model=AssetZoneMembershipRead, status_code=201)
@audit_log_action("create_asset_zone_membership", "AssetZoneMembership")
def create_asset_zone_membership(
    zone_id: uuid.UUID,
    membership_data: AssetZoneMembershipCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add an asset to a security zone with a specific role"""
    # Verify zone exists
    zone = (
        db.query(SecurityZone)
        .filter(
            SecurityZone.id == zone_id,
            SecurityZone.tenant_id == current_user.tenant_id,
            SecurityZone.deleted_at.is_(None)
        )
        .first()
    )
    if not zone:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)
    
    # Verify asset exists and belongs to tenant
    asset = (
        db.query(Asset)
        .filter(
            Asset.id == membership_data.asset_id,
            Asset.tenant_id == current_user.tenant_id,
            Asset.deleted_at.is_(None)
        )
        .first()
    )
    if not asset:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)
    
    # Check if membership already exists
    if crud_memberships.check_membership_exists(
        db, membership_data.asset_id, zone_id, membership_data.role, current_user.tenant_id
    ):
        raise ErrorCodeException(
            status_code=400,
            error_code=ErrorCode.INVALID_REQUEST,
            detail=f"Asset already has role '{membership_data.role}' in this zone"
        )
    
    # Create membership data with zone_id from URL parameter
    membership_dict = membership_data.dict(exclude_unset=True)
    # Ensure security_zone_id is set from URL parameter (overrides any value from body)
    membership_dict['security_zone_id'] = zone_id
    membership_create = AssetZoneMembershipCreate(**membership_dict)
    
    try:
        membership = crud_memberships.create_asset_zone_membership(
            db, membership_create, current_user.tenant_id
        )
    except ValueError as e:
        # Convert ValueError to ErrorCodeException for better error handling
        raise ErrorCodeException(
            status_code=400,
            error_code=ErrorCode.INVALID_REQUEST,
            detail=str(e)
        )
    
    # Convert membership to response schema manually to avoid ORM relationship issues
    membership_dict = {
        'id': membership.id,
        'tenant_id': membership.tenant_id,
        'asset_id': membership.asset_id,
        'security_zone_id': membership.security_zone_id,
        'role': membership.role,
        'interface_scope': membership.interface_scope,
        'sl_target': membership.sl_target,
        'notes': membership.notes,
        'created_at': membership.created_at,
        'updated_at': membership.updated_at,
        'deleted_at': membership.deleted_at,
        'asset': None,  # Relationships not loaded by default
        'security_zone': None
    }
    
    return AssetZoneMembershipRead(**membership_dict)


@router.get("/{zone_id}/memberships", response_model=List[AssetZoneMembershipRead])
def list_zone_memberships(
    zone_id: uuid.UUID,
    role: Optional[str] = Query(None, description="Filter by role"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all asset memberships for a security zone"""
    # Verify zone exists
    zone = (
        db.query(SecurityZone)
        .filter(
            SecurityZone.id == zone_id,
            SecurityZone.tenant_id == current_user.tenant_id,
            SecurityZone.deleted_at.is_(None)
        )
        .first()
    )
    if not zone:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)
    
    memberships = crud_memberships.get_asset_zone_memberships(
        db, current_user.tenant_id, security_zone_id=zone_id, role=role
    )
    
    return [AssetZoneMembershipRead.from_orm(m) for m in memberships]


@router.put("/{zone_id}/memberships/{membership_id}", response_model=AssetZoneMembershipRead)
@audit_log_action("update_asset_zone_membership", "AssetZoneMembership")
def update_asset_zone_membership(
    zone_id: uuid.UUID,
    membership_id: uuid.UUID,
    membership_data: AssetZoneMembershipUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update an asset zone membership"""
    # Verify zone exists
    zone = (
        db.query(SecurityZone)
        .filter(
            SecurityZone.id == zone_id,
            SecurityZone.tenant_id == current_user.tenant_id,
            SecurityZone.deleted_at.is_(None)
        )
        .first()
    )
    if not zone:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)
    
    membership = crud_memberships.update_asset_zone_membership(
        db, membership_id, membership_data, current_user.tenant_id
    )
    
    if not membership:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)
    
    return AssetZoneMembershipRead.from_orm(membership)


@router.delete("/{zone_id}/memberships/{membership_id}", status_code=204)
@audit_log_action("delete_asset_zone_membership", "AssetZoneMembership")
def delete_asset_zone_membership(
    zone_id: uuid.UUID,
    membership_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove an asset from a security zone (soft delete membership)"""
    # Verify zone exists
    zone = (
        db.query(SecurityZone)
        .filter(
            SecurityZone.id == zone_id,
            SecurityZone.tenant_id == current_user.tenant_id,
            SecurityZone.deleted_at.is_(None)
        )
        .first()
    )
    if not zone:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)
    
    success = crud_memberships.delete_asset_zone_membership(
        db, membership_id, current_user.tenant_id
    )
    
    if not success:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)

