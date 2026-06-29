# backend/app/routers/asset_capabilities.py
"""
API endpoints for managing Asset Capabilities
"""
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models import User, Asset
from app.models.asset_capability import AssetCapability
from app.models.security_capability import SecurityCapability
from app.services.auth import get_current_user
from app.services.audit_decorator import audit_log_action
from app.crud import asset_capabilities as crud_asset_caps
from app.errors.exceptions import ErrorCodeException
from app.errors.error_codes import ErrorCode
from app.schemas.asset_capability import (
    AssetCapabilityCreate,
    AssetCapabilityUpdate,
    AssetCapabilityResponse,
    SecurityCapabilityInfo,
    BulkCapabilityUpdate,
    BulkCapabilityResponse,
)
from app.services.feature_guard import require_iec62443_enabled
from app.services.rbac import require_section_access
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/assets",
    tags=["asset-capabilities"],
    dependencies=[
        Depends(require_iec62443_enabled),
        Depends(require_section_access("compliance")),
    ],
)


def calculate_capability_inference_confidence(
    asset_type_name: str,
    manufacturer_name: Optional[str],
    model: Optional[str],
    firmware_version: Optional[str],
    typical_roles: List[str]
) -> float:
    """
    Calculate confidence score (0.0-1.0) for inferring a capability from asset metadata.
    
    Factors considered:
    - asset_type match: +0.2 (base)
    - manufacturer match: +0.3 (if manufacturer name matches typical roles)
    - model match: +0.3 (if model name matches typical roles)
    - firmware match: +0.2 (if firmware indicates capability)
    
    Returns: confidence score (0.0-1.0)
    """
    if not typical_roles:
        return 0.0
    
    confidence = 0.0
    
    # Normalize strings for matching
    def normalize(s: str) -> str:
        return s.lower().replace(' ', '').replace('-', '').replace('_', '') if s else ''
    
    asset_type_normalized = normalize(asset_type_name) if asset_type_name else ''
    manufacturer_normalized = normalize(manufacturer_name) if manufacturer_name else ''
    model_normalized = normalize(model) if model else ''
    firmware_normalized = normalize(firmware_version) if firmware_version else ''
    
    # Common role mappings
    role_mappings = {
        'plc': ['plc', 'controller', 'programmable'],
        'hmi': ['hmi', 'human', 'machine', 'interface'],
        'server': ['server', 'scada', 'historian'],
        'firewall': ['firewall', 'fw'],
        'rtu': ['rtu', 'remote', 'terminal'],
        'router': ['router', 'switch'],
        'data_diode': ['diode', 'unidirectional']
    }
    
    # Check each typical role
    for role in typical_roles:
        role_normalized = normalize(role)
        
        # Asset type match (+0.2)
        if asset_type_normalized:
            if role_normalized in asset_type_normalized or asset_type_normalized in role_normalized:
                confidence = max(confidence, 0.2)
            # Check role mappings
            if role_normalized in role_mappings:
                for keyword in role_mappings[role_normalized]:
                    if keyword in asset_type_normalized:
                        confidence = max(confidence, 0.2)
                        break
        
        # Manufacturer match (+0.3)
        if manufacturer_normalized:
            if role_normalized in manufacturer_normalized:
                confidence = max(confidence, min(confidence + 0.3, 1.0))
        
        # Model match (+0.3)
        if model_normalized:
            if role_normalized in model_normalized or model_normalized in role_normalized:
                confidence = max(confidence, min(confidence + 0.3, 1.0))
            # Check if model contains role keywords
            if role_normalized in role_mappings:
                for keyword in role_mappings[role_normalized]:
                    if keyword in model_normalized:
                        confidence = max(confidence, min(confidence + 0.3, 1.0))
                        break
        
        # Firmware match (+0.2) - firmware version might indicate capability
        # This is more heuristic, could be improved with firmware database
        if firmware_normalized and len(firmware_normalized) > 0:
            # If firmware exists, it suggests the device is configurable/capable
            confidence = max(confidence, min(confidence + 0.1, 1.0))
    
    return min(confidence, 1.0)


def asset_type_matches_typical_roles(asset_type_name: str, typical_roles: List[str]) -> bool:
    """
    Check if asset type name matches any of the typical_roles.
    Legacy function for backward compatibility.
    Returns True if confidence >= 0.2 (basic match).
    """
    confidence = calculate_capability_inference_confidence(
        asset_type_name, None, None, None, typical_roles
    )
    return confidence >= 0.2


@router.get("/{asset_id}/capabilities", response_model=List[AssetCapabilityResponse])
def get_asset_capabilities(
    asset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all relevant capabilities for an asset.
    Returns explicit AssetCapabilities, inferred capabilities (from asset_type), and available capabilities.
    """
    # Verify asset exists and belongs to tenant
    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.tenant_id == current_user.tenant_id,
        Asset.deleted_at == None
    ).first()
    
    if not asset:
        raise ErrorCodeException(
            status_code=404,
            error_code=ErrorCode.ASSET_NOT_FOUND
        )
    
    # Get all SecurityCapabilities that apply to assets
    all_capabilities = db.query(SecurityCapability).filter(
        SecurityCapability.applies_to_asset == True
    ).all()
    
    # Get explicit AssetCapabilities for this asset
    explicit_caps = crud_asset_caps.get_asset_capabilities_by_asset(
        db, asset_id, current_user.tenant_id
    )
    explicit_caps_map = {ac.capability_id: ac for ac in explicit_caps}
    
    # Get asset metadata for inference
    asset_type_name = asset.asset_type.name if asset.asset_type else None
    manufacturer_name = asset.manufacturer.name if asset.manufacturer else None
    model = asset.model
    firmware_version = asset.firmware_version
    
    # Build response
    result = []
    for sec_cap in all_capabilities:
        # Check if explicit capability exists
        explicit_cap = explicit_caps_map.get(sec_cap.id)
        
        if explicit_cap:
            # Explicit capability
            result.append(AssetCapabilityResponse(
                id=explicit_cap.id,
                capability_id=sec_cap.id,
                capability=SecurityCapabilityInfo(
                    id=sec_cap.id,
                    code=sec_cap.code,
                    name=sec_cap.name,
                    category=sec_cap.category,
                    description=sec_cap.description,
                    typical_roles=sec_cap.typical_roles if sec_cap.typical_roles else []
                ),
                support_level=explicit_cap.support_level,
                source='explicit',
                inference_confidence=None,  # Not applicable for explicit
                notes=explicit_cap.notes,
                evidence_ref=explicit_cap.evidence_ref,
                created_at=explicit_cap.created_at,
                updated_at=explicit_cap.updated_at
            ))
        elif sec_cap.typical_roles:
            # Calculate inference confidence
            confidence = calculate_capability_inference_confidence(
                asset_type_name,
                manufacturer_name,
                model,
                firmware_version,
                sec_cap.typical_roles
            )
            
            if confidence >= 0.2:  # Minimum threshold for inference
                # Inferred capability
                confidence_label = "high" if confidence >= 0.7 else "medium" if confidence >= 0.4 else "low"
                result.append(AssetCapabilityResponse(
                    id=None,
                    capability_id=sec_cap.id,
                    capability=SecurityCapabilityInfo(
                        id=sec_cap.id,
                        code=sec_cap.code,
                        name=sec_cap.name,
                        category=sec_cap.category,
                        description=sec_cap.description,
                        typical_roles=sec_cap.typical_roles if sec_cap.typical_roles else []
                    ),
                    support_level='unknown',
                    source='inferred',
                    inference_confidence=confidence,
                    notes=f"Inferred ({confidence_label} confidence, {confidence:.2f}) from asset metadata matching typical roles: {', '.join(sec_cap.typical_roles)}",
                    evidence_ref=None,
                    created_at=None,
                    updated_at=None
                ))
            else:
                # Available capability (not inferred, not explicit)
                result.append(AssetCapabilityResponse(
                    id=None,
                    capability_id=sec_cap.id,
                    capability=SecurityCapabilityInfo(
                        id=sec_cap.id,
                        code=sec_cap.code,
                        name=sec_cap.name,
                        category=sec_cap.category,
                        description=sec_cap.description,
                        typical_roles=sec_cap.typical_roles if sec_cap.typical_roles else []
                    ),
                    support_level='available',
                    source='available',
                    inference_confidence=None,
                    notes=None,
                    evidence_ref=None,
                    created_at=None,
                    updated_at=None
                ))
        else:
            # Available capability (no typical_roles)
            result.append(AssetCapabilityResponse(
                id=None,
                capability_id=sec_cap.id,
                capability=SecurityCapabilityInfo(
                    id=sec_cap.id,
                    code=sec_cap.code,
                    name=sec_cap.name,
                    category=sec_cap.category,
                    description=sec_cap.description,
                    typical_roles=sec_cap.typical_roles if sec_cap.typical_roles else []
                ),
                support_level='available',
                source='available',
                inference_confidence=None,
                notes=None,
                evidence_ref=None,
                created_at=None,
                updated_at=None
            ))
    
    return result


@router.post("/{asset_id}/capabilities", response_model=AssetCapabilityResponse, status_code=201)
@audit_log_action("create", "AssetCapability", model_class=AssetCapability)
def create_asset_capability(
    asset_id: uuid.UUID,
    capability_in: AssetCapabilityCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new explicit AssetCapability"""
    # Verify asset exists and belongs to tenant
    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.tenant_id == current_user.tenant_id,
        Asset.deleted_at == None
    ).first()
    
    if not asset:
        raise ErrorCodeException(
            status_code=404,
            error_code=ErrorCode.ASSET_NOT_FOUND
        )
    
    # Verify SecurityCapability exists and applies to assets
    sec_cap = db.query(SecurityCapability).filter(
        SecurityCapability.id == capability_in.capability_id,
        SecurityCapability.applies_to_asset == True
    ).first()
    
    if not sec_cap:
        raise ErrorCodeException(
            status_code=404,
            error_code=ErrorCode.ASSET_NOT_FOUND,
            detail="SecurityCapability not found or does not apply to assets"
        )
    
    # Check if already exists for this asset
    existing_caps = crud_asset_caps.get_asset_capabilities(
        db, current_user.tenant_id, asset_id=asset_id, capability_id=capability_in.capability_id
    )
    if existing_caps:
        raise ErrorCodeException(
            status_code=400,
            error_code=ErrorCode.INVALID_INPUT,
            detail="AssetCapability already exists for this asset"
        )
    
    # Create AssetCapability
    from app.schemas.asset_capability import AssetCapabilityBase
    create_data = AssetCapabilityBase(
        asset_id=asset_id,
        capability_id=capability_in.capability_id,
        support_level=capability_in.support_level,
        notes=capability_in.notes,
        evidence_ref=capability_in.evidence_ref
    )
    
    asset_cap = crud_asset_caps.create_asset_capability(
        db,
        create_data,
        current_user.tenant_id
    )
    
    # Return response with full details
    return AssetCapabilityResponse(
        id=asset_cap.id,
        capability_id=sec_cap.id,
        capability=SecurityCapabilityInfo(
            id=sec_cap.id,
            code=sec_cap.code,
            name=sec_cap.name,
            category=sec_cap.category,
            description=sec_cap.description,
            typical_roles=sec_cap.typical_roles if sec_cap.typical_roles else []
        ),
        support_level=asset_cap.support_level,
        source='explicit',
        notes=asset_cap.notes,
        evidence_ref=asset_cap.evidence_ref,
        created_at=asset_cap.created_at,
        updated_at=asset_cap.updated_at
    )


@router.put("/{asset_id}/capabilities/{capability_id}", response_model=AssetCapabilityResponse)
@audit_log_action("update", "AssetCapability", model_class=AssetCapability)
def update_asset_capability(
    asset_id: uuid.UUID,
    capability_id: uuid.UUID,
    capability_update: AssetCapabilityUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update an existing AssetCapability"""
    # Verify asset exists and belongs to tenant
    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.tenant_id == current_user.tenant_id,
        Asset.deleted_at == None
    ).first()
    
    if not asset:
        raise ErrorCodeException(
            status_code=404,
            error_code=ErrorCode.ASSET_NOT_FOUND
        )
    
    # Get AssetCapability (using the ID from the path, not capability_id)
    # The capability_id in path is actually the AssetCapability.id
    asset_cap = crud_asset_caps.get_asset_capability(
        db, capability_id, current_user.tenant_id
    )
    
    if not asset_cap or asset_cap.asset_id != asset_id:
        raise ErrorCodeException(
            status_code=404,
            error_code=ErrorCode.ASSET_NOT_FOUND,
            detail="AssetCapability not found"
        )
    
    # Update
    updated_cap = crud_asset_caps.update_asset_capability(
        db, capability_id, capability_update, current_user.tenant_id
    )
    
    if not updated_cap:
        raise ErrorCodeException(
            status_code=404,
            error_code=ErrorCode.ASSET_NOT_FOUND
        )
    
    # Get SecurityCapability details
    sec_cap = db.query(SecurityCapability).filter(
        SecurityCapability.id == updated_cap.capability_id
    ).first()
    
    if not sec_cap:
        raise ErrorCodeException(
            status_code=404,
            error_code=ErrorCode.ASSET_NOT_FOUND,
            detail="SecurityCapability not found"
        )
    
    return AssetCapabilityResponse(
        id=updated_cap.id,
        capability_id=sec_cap.id,
        capability=SecurityCapabilityInfo(
            id=sec_cap.id,
            code=sec_cap.code,
            name=sec_cap.name,
            category=sec_cap.category,
            description=sec_cap.description,
            typical_roles=sec_cap.typical_roles if sec_cap.typical_roles else []
        ),
        support_level=updated_cap.support_level,
        source='explicit',
        notes=updated_cap.notes,
        evidence_ref=updated_cap.evidence_ref,
        created_at=updated_cap.created_at,
        updated_at=updated_cap.updated_at
    )


@router.delete("/{asset_id}/capabilities/{capability_id}", status_code=204)
@audit_log_action("delete", "AssetCapability", model_class=AssetCapability)
def delete_asset_capability(
    asset_id: uuid.UUID,
    capability_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete an AssetCapability"""
    # Verify asset exists and belongs to tenant
    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.tenant_id == current_user.tenant_id,
        Asset.deleted_at == None
    ).first()
    
    if not asset:
        raise ErrorCodeException(
            status_code=404,
            error_code=ErrorCode.ASSET_NOT_FOUND
        )
    
    # Get AssetCapability
    asset_cap = crud_asset_caps.get_asset_capability(
        db, capability_id, current_user.tenant_id
    )
    
    if not asset_cap or asset_cap.asset_id != asset_id:
        raise ErrorCodeException(
            status_code=404,
            error_code=ErrorCode.ASSET_NOT_FOUND,
            detail="AssetCapability not found"
        )
    
    # Delete
    success = crud_asset_caps.delete_asset_capability(
        db, capability_id, current_user.tenant_id
    )
    
    if not success:
        raise ErrorCodeException(
            status_code=404,
            error_code=ErrorCode.ASSET_NOT_FOUND
        )


@router.post("/{asset_id}/capabilities/bulk", response_model=BulkCapabilityResponse)
@audit_log_action("update", "AssetCapability", model_class=AssetCapability)
def bulk_update_asset_capabilities(
    asset_id: uuid.UUID,
    bulk_update: BulkCapabilityUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Bulk create or update AssetCapabilities"""
    # Verify asset exists and belongs to tenant
    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.tenant_id == current_user.tenant_id,
        Asset.deleted_at == None
    ).first()
    
    if not asset:
        raise ErrorCodeException(
            status_code=404,
            error_code=ErrorCode.ASSET_NOT_FOUND
        )
    
    # Get existing capabilities for this asset
    existing_caps = crud_asset_caps.get_asset_capabilities_by_asset(
        db, asset_id, current_user.tenant_id
    )
    existing_caps_map = {ac.capability_id: ac for ac in existing_caps}
    
    created_count = 0
    updated_count = 0
    
    try:
        for cap_item in bulk_update.capabilities:
            # Verify SecurityCapability exists and applies to assets
            sec_cap = db.query(SecurityCapability).filter(
                SecurityCapability.id == cap_item.capability_id,
                SecurityCapability.applies_to_asset == True
            ).first()
            
            if not sec_cap:
                logger.warning(f"SecurityCapability {cap_item.capability_id} not found or does not apply to assets, skipping")
                continue
            
            # Check if exists
            existing_cap = existing_caps_map.get(cap_item.capability_id)
            
            if existing_cap:
                # Update existing
                update_data = AssetCapabilityUpdate(
                    support_level=cap_item.support_level,
                    notes=cap_item.notes,
                    evidence_ref=cap_item.evidence_ref
                )
                crud_asset_caps.update_asset_capability(
                    db, existing_cap.id, update_data, current_user.tenant_id
                )
                updated_count += 1
            else:
                # Create new
                from app.schemas.asset_capability import AssetCapabilityBase
                create_data = AssetCapabilityBase(
                    asset_id=asset_id,
                    capability_id=cap_item.capability_id,
                    support_level=cap_item.support_level,
                    notes=cap_item.notes,
                    evidence_ref=cap_item.evidence_ref
                )
                crud_asset_caps.create_asset_capability(
                    db, create_data, current_user.tenant_id
                )
                created_count += 1
        
        db.commit()
        
        return BulkCapabilityResponse(
            created=created_count,
            updated=updated_count,
            total=created_count + updated_count
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error in bulk update: {str(e)}", exc_info=True)
        raise ErrorCodeException(
            status_code=500,
            error_code=ErrorCode.INTERNAL_ERROR,
            detail=f"Error updating capabilities: {str(e)}"
        )

