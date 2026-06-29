# backend/app/routers/compliance.py
import uuid
import re
import logging
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel, Field

from app.database import get_db

logger = logging.getLogger(__name__)
from app.models import (
    User,
    SecurityRequirement,
    SecurityRequirementCompliance,
    SecurityZone,
    Asset,
    Conduit,
    SecurityCapability,
    SRCapability,
    AssetCapability,
    SRAssessment,
    SRAssessmentEvidence,
    AssetZoneMembership,
    ConduitAsset
)
from app.services.auth import get_current_user
from app.services.audit_decorator import audit_log_action
from app.services.rbac import require_permission
from app.services.isa62443_compliance_engine import ISA62443ComplianceEngine
from app.services.isa62443_audit_export import audit_export_to_csv, build_zone_audit_export
from app.services.isa62443_assessment_utils import (
    applicable_requirements_for_target,
    compute_fr_summary_stats,
    excludes_from_sl_denominator,
    extract_assessment_status,
)
from app.models.requirement_enhancement import RequirementEnhancement
from app.errors.exceptions import ErrorCodeException
from app.errors.error_codes import ErrorCode
from app.crud import sr_assessments as crud_sr_assessments
from app.crud import asset_capabilities as crud_asset_capabilities
from app.schemas.sr_assessment import SRAssessmentCreate, SRAssessmentUpdate
from app.schemas.sr_assessment_evidence import SRAssessmentEvidenceCreate
from app.services.feature_guard import require_iec62443_enabled

router = APIRouter(
    prefix="/compliance",
    tags=["Compliance"],
    dependencies=[Depends(require_iec62443_enabled)],
)


# ============================================================================
# FOUNDATION REQUIREMENTS ENDPOINTS
# ============================================================================

@router.get("/zone/{zone_id}/foundation-requirements", response_model=List[dict])
def get_zone_foundation_requirements(
    zone_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("compliance", 1)),
):
    """Get Foundation Requirements (FR) grouped with compliance statistics for a zone"""
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
    
    # Get all FR requirements
    # Try both 'FR' category and requirement_id starting with 'FR'
    fr_requirements = (
        db.query(SecurityRequirement)
        .filter(
            or_(
                SecurityRequirement.requirement_category == 'FR',
                SecurityRequirement.requirement_id.like('FR%')
            ),
            SecurityRequirement.applies_to_zones == True
        )
        .order_by(SecurityRequirement.requirement_id)
        .all()
    )
    
    # If no FRs exist, create them dynamically from SRs
    if not fr_requirements:
        # Get all SRs that apply to zones
        all_srs = (
            db.query(SecurityRequirement)
            .filter(
                SecurityRequirement.applies_to_zones == True,
                SecurityRequirement.requirement_id.like('SR%')
            )
            .order_by(SecurityRequirement.requirement_id)
            .all()
        )
        
        # Group SRs by their FR number (e.g., SR1.1, SR1.2 -> FR1)
        fr_groups = {}
        for sr in all_srs:
            # Extract FR number from SR (e.g., "SR1.1" -> "1", "SR2.3" -> "2")
            sr_match = re.search(r'SR\s*(\d+)', sr.requirement_id, re.IGNORECASE)
            if sr_match:
                fr_number = sr_match.group(1)
                fr_id = f"FR{fr_number}"
                
                if fr_id not in fr_groups:
                    fr_groups[fr_id] = {
                        'id': f"fr-{fr_number}",  # Temporary ID
                        'requirement_id': fr_id,
                        'title': f"Foundation Requirement {fr_number}",
                        'description': f"FR{fr_number} - Foundation Requirements",
                        'srs': []
                    }
                fr_groups[fr_id]['srs'].append(sr)
        
        # Convert groups to FR-like objects
        fr_requirements = []
        for fr_id, fr_data in fr_groups.items():
            # Create a simple object that mimics SecurityRequirement
            class FakeFR:
                def __init__(self, fr_id, title, description, srs):
                    self.id = fr_data['id']
                    self.requirement_id = fr_id
                    self.title = title
                    self.description = description
                    self.srs = srs
            
            fr_requirements.append(FakeFR(
                fr_data['requirement_id'],
                fr_data['title'],
                fr_data['description'],
                fr_data['srs']
            ))
    
    # Get SR assessments for this zone (using new SRAssessment model)
    try:
        assessments = (
            db.query(SRAssessment)
            .filter(
                SRAssessment.object_type == 'zone',
                SRAssessment.object_id == zone_id,
                SRAssessment.tenant_id == current_user.tenant_id
            )
            .all()
        )
        # Create map using sr_id (UUID) as key
        compliance_map = {assessment.sr_id: assessment for assessment in assessments}
    except Exception as e:
        logger.warning(f"Error loading SR assessments for FR (tables may not exist yet): {e}")
        compliance_map = {}
    
    result = []
    for fr in fr_requirements:
        # Check if this is a dynamically created FR (has 'srs' attribute)
        if hasattr(fr, 'srs'):
            # Use the SRs already grouped
            sr_requirements = fr.srs
        else:
            # Get all SRs under this FR from database
            fr_id = fr.requirement_id.strip()
            
            # Extract the number from FR (e.g., "FR1" -> "1", "FR 1" -> "1", "FR1.1" -> "1")
            fr_number_match = re.search(r'FR\s*(\d+)', fr_id, re.IGNORECASE)
            if not fr_number_match:
                # Try to extract just the number
                fr_number_match = re.search(r'(\d+)', fr_id)
            
            if fr_number_match:
                fr_number = fr_number_match.group(1)
                # Look for SRs with this number (e.g., SR1.1, SR1.2, etc.)
                sr_pattern = f"SR {fr_number}.%"
            else:
                # Fallback: try to match SRs that start with the same base
                sr_pattern = f"SR{fr_id[2:]}.%" if len(fr_id) > 2 else "SR%.%"
            
            sr_requirements = (
                db.query(SecurityRequirement)
                .filter(
                    SecurityRequirement.requirement_id.like(sr_pattern),
                    SecurityRequirement.applies_to_zones == True
                )
                .all()
            )
        
        fr_stats = compute_fr_summary_stats(
            sr_requirements,
            compliance_map,
            target_sl=zone.security_level_target,
        )
        result.append({
            'id': str(fr.id) if hasattr(fr, 'id') else f"fr-{fr.requirement_id.replace('FR', '').strip()}",
            'requirement_id': fr.requirement_id,
            'title': fr.title,
            'description': fr.description,
            'compliant_count': fr_stats['compliant_count'],
            'partial_count': fr_stats['partial_count'],
            'non_compliant_count': fr_stats['non_compliant_count'],
            'not_applicable_count': fr_stats['not_applicable_count'],
            'not_assessed_count': fr_stats['not_assessed_count'],
            'total_sr': fr_stats['total_sr'],
            'in_scope_count': fr_stats['in_scope_count'],
            'compliance_percentage': fr_stats['compliance_percentage'],
        })
    
    return result


@router.get("/zone/{zone_id}/security-requirements/{fr_id}", response_model=List[dict])
def get_zone_security_requirements_by_fr(
    zone_id: uuid.UUID,
    fr_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("compliance", 1)),
):
    """Get Security Requirements for a specific Foundation Requirement"""
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
    
    # Extract FR number from fr_id (e.g., "FR1" -> "1", "FR 1" -> "1")
    fr_number_match = re.search(r'FR\s*(\d+)', fr_id, re.IGNORECASE)
    if not fr_number_match:
        fr_number_match = re.search(r'(\d+)', fr_id)
    
    if not fr_number_match:
        return []
    
    fr_number = fr_number_match.group(1)
    # Pattern to match SRs: "SR 1.%" (with space) or "SR1.%" (without space)
    sr_pattern = f"SR {fr_number}.%"
    
    logger.info(f"Searching for SRs with pattern: {sr_pattern}")
    
    # Natural sort key function
    def natural_sort_key(s):
        return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]
    
    # Get SRs for this FR
    sr_requirements = (
        db.query(SecurityRequirement)
        .filter(
            SecurityRequirement.requirement_id.like(sr_pattern),
            SecurityRequirement.applies_to_zones == True
        )
        .all()  # Fetch all first
    )
    
    # Sort numerically
    sr_requirements.sort(key=lambda sr: natural_sort_key(sr.requirement_id))
    
    logger.info(f"Found {len(sr_requirements)} SRs for FR {fr_id}")
    
    # Get SR assessments for this zone (using new SRAssessment model)
    try:
        assessments = (
            db.query(SRAssessment)
            .filter(
                SRAssessment.object_type == 'zone',
                SRAssessment.object_id == zone_id,
                SRAssessment.tenant_id == current_user.tenant_id
            )
            .all()
        )
        # Create map using sr_id (UUID) as key
        compliance_map = {assessment.sr_id: assessment for assessment in assessments}
    except Exception as e:
        logger.warning(f"Error loading SR assessments (tables may not exist yet): {e}")
        compliance_map = {}
    
    result = []
    for sr in sr_requirements:
        assessment = compliance_map.get(sr.id)
        
        result.append({
            'id': str(sr.id),
            'requirement_id': sr.requirement_id,
            'title': sr.title,
            'description': sr.description,
            'requirement_text': sr.requirement_text,
            'min_security_level': sr.min_security_level,
            'max_security_level': sr.max_security_level,
            'compliance_status': assessment.status if assessment else 'not_assessed',
            'compliance_percentage': None,  # Not used in new system
            'assessment_notes': assessment.justification if assessment else None,
            'evidence_notes': None  # Evidence is now in SRAssessmentEvidence
        })
    
    return result


@router.get("/zone/{zone_id}/sr/{sr_id}/assets", response_model=List[dict])
def get_sr_involved_assets(
    zone_id: uuid.UUID,
    sr_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("compliance", 1)),
):
    """Get assets involved in a Security Requirement (legacy endpoint)"""
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
    
    # Get assets in the zone
    zone_assets = (
        db.query(Asset)
        .join(AssetZoneMembership, Asset.id == AssetZoneMembership.asset_id)
        .filter(
            AssetZoneMembership.security_zone_id == zone_id,
            AssetZoneMembership.tenant_id == current_user.tenant_id,
            AssetZoneMembership.deleted_at.is_(None),
            Asset.deleted_at.is_(None)
        )
        .all()
    )
    
    return [{'id': str(asset.id), 'name': asset.name} for asset in zone_assets]


@router.get("/zone/{zone_id}/sr/{sr_id}/conduits", response_model=List[dict])
def get_sr_involved_conduits(
    zone_id: uuid.UUID,
    sr_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("compliance", 1)),
):
    """Get conduits involved in a Security Requirement (legacy endpoint)"""
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
    
    # Get conduits connected to this zone
    zone_conduits = (
        db.query(Conduit)
        .filter(
            or_(
                Conduit.from_zone_id == zone_id,
                Conduit.to_zone_id == zone_id
            ),
            Conduit.tenant_id == current_user.tenant_id,
            Conduit.deleted_at.is_(None)
        )
        .all()
    )
    
    return [{'id': str(conduit.id), 'name': conduit.name} for conduit in zone_conduits]


@router.get("/zone/{zone_id}", response_model=dict)
def get_zone_compliance_summary(
    zone_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("compliance", 1)),
):
    """Get compliance summary for a zone (using SRAssessment)"""
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
    
    # Get all SR assessments for this zone
    try:
        assessments = (
            db.query(SRAssessment)
            .filter(
                SRAssessment.object_type == 'zone',
                SRAssessment.object_id == zone_id,
                SRAssessment.tenant_id == current_user.tenant_id
            )
            .all()
        )
        
        # Count by status
        summary = {
            'compliant': 0,
            'partial': 0,
            'non_compliant': 0,
            'not_applicable': 0,
            'insufficient_info': 0
        }
        
        for assessment in assessments:
            status = assessment.status
            if status == 'compliant':
                summary['compliant'] += 1
            elif status == 'partial':
                summary['partial'] += 1
            elif status == 'non_compliant':
                summary['non_compliant'] += 1
            elif status == 'not_applicable':
                summary['not_applicable'] += 1
            elif status == 'insufficient_info':
                summary['insufficient_info'] += 1
    except Exception as e:
        logger.warning(f"Error loading SR assessments (tables may not exist yet): {e}")
        assessments = []
        summary = {
            'compliant': 0,
            'partial': 0,
            'non_compliant': 0,
            'not_applicable': 0,
            'insufficient_info': 0
        }

    zone_requirements = (
        db.query(SecurityRequirement)
        .filter(SecurityRequirement.applies_to_zones == True)
        .all()
    )
    compliance_map = {a.sr_id: a.status for a in assessments}
    sl_t = zone.security_level_target
    applicable = applicable_requirements_for_target(zone_requirements, sl_t) if sl_t else []
    in_scope = []
    for req in applicable:
        status = extract_assessment_status(compliance_map.get(req.id))
        if not excludes_from_sl_denominator(status):
            in_scope.append(req)
    assessed_count = sum(
        1 for req in in_scope if extract_assessment_status(compliance_map.get(req.id)) is not None
    )
    sl_a = zone.security_level_achieved
    if sl_a is None and sl_t:
        sl_a = ISA62443ComplianceEngine.calculate_zone_security_level_achieved(db, zone)
    compliance_status = zone.compliance_status
    if not compliance_status or compliance_status == 'not_assessed':
        compliance_status = ISA62443ComplianceEngine.calculate_zone_compliance_status(db, zone)

    return {
        **summary,
        'compliance_status': compliance_status,
        'security_level_target': sl_t,
        'security_level_achieved': sl_a,
        'security_level_capability': zone.security_level_capability,
        'sl_gap': (sl_t - sl_a) if (sl_t is not None and sl_a is not None) else None,
        'assessment_progress': {
            'assessed_count': assessed_count,
            'in_scope_count': len(in_scope),
            'percent': round((assessed_count / len(in_scope)) * 100, 1) if in_scope else 0.0,
        },
        'total_assessments': len(assessments),
    }


@router.get("/sr/{sr_id}/requirement-enhancements", response_model=List[dict])
def get_sr_requirement_enhancements(
    sr_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("compliance", 1)),
):
    """Requirement Enhancements (RE 1-4) for a Security Requirement."""
    sr = db.query(SecurityRequirement).filter(SecurityRequirement.id == sr_id).first()
    if not sr:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)

    enhancements = (
        db.query(RequirementEnhancement)
        .filter(RequirementEnhancement.security_requirement_id == sr_id)
        .order_by(RequirementEnhancement.enhancement_level)
        .all()
    )
    return [
        {
            'id': str(re.id),
            'enhancement_level': re.enhancement_level,
            'title': re.title,
            'description': re.description,
            'standard_version': re.standard_version,
        }
        for re in enhancements
    ]


# ============================================================================
# NEW CAPABILITY-BASED ASSESSMENT ENDPOINTS
# ============================================================================

@router.get("/zone/{zone_id}/sr/{sr_id}/assessment-assist", response_model=dict)
def get_sr_assessment_assist(
    zone_id: uuid.UUID,
    sr_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("compliance", 1)),
):
    """
    Get assisted SR assessment view.
    Returns:
    - A. What the SR requires (from SR → Capability mapping)
    - B. What EXISTS in the system (assets in zone with those capabilities, conduits with those capabilities)
    - C. Current assessment status if exists
    """
    try:
        # Verify zone exists and belongs to tenant
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
        
        # Verify SR exists
        sr = db.query(SecurityRequirement).filter(SecurityRequirement.id == sr_id).first()
        if not sr:
            raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)
    except ErrorCodeException:
        raise
    except Exception as e:
        logger.error(f"Error verifying zone/SR in assessment-assist: {e}", exc_info=True)
        raise ErrorCodeException(status_code=500, error_code=ErrorCode.INTERNAL_ERROR)
    
    # A. Get required capabilities for this SR
    # Check if SRCapability table exists and has data
    required_capabilities = []
    try:
        sr_capabilities = (
            db.query(SRCapability)
            .join(SecurityCapability, SRCapability.capability_id == SecurityCapability.id)
            .filter(SRCapability.sr_id == sr_id)
            .all()
        )
        
        for sr_cap in sr_capabilities:
            required_capabilities.append({
                'capability_id': str(sr_cap.capability_id),
                'code': sr_cap.capability.code,
                'name': sr_cap.capability.name,
                'importance': sr_cap.importance,  # 'primary' or 'supporting'
                'applies_to_asset': sr_cap.capability.applies_to_asset,
                'applies_to_conduit': sr_cap.capability.applies_to_conduit,
                'typical_roles': sr_cap.capability.typical_roles or [],  # For matching with asset types
            })
    except Exception as e:
        logger.warning(f"Error loading SR capabilities (tables may not exist yet): {e}")
        # If capabilities don't exist yet, return empty list
        required_capabilities = []
    
    # B. Get available evidence in the zone
    # Get assets in the zone (with asset_type loaded)
    from sqlalchemy.orm import joinedload
    zone_assets = (
        db.query(Asset)
        .options(joinedload(Asset.asset_type))
        .join(AssetZoneMembership, Asset.id == AssetZoneMembership.asset_id)
        .filter(
            AssetZoneMembership.security_zone_id == zone_id,
            AssetZoneMembership.tenant_id == current_user.tenant_id,
            AssetZoneMembership.deleted_at.is_(None),
            Asset.deleted_at.is_(None)
        )
        .all()
    )
    
    # Get asset capabilities for zone assets
    asset_ids = [asset.id for asset in zone_assets]
    asset_capabilities_map = {}
    if asset_ids:
        try:
            asset_caps = (
                db.query(AssetCapability)
                .join(SecurityCapability, AssetCapability.capability_id == SecurityCapability.id)
                .filter(
                    AssetCapability.asset_id.in_(asset_ids),
                    AssetCapability.tenant_id == current_user.tenant_id
                )
                .all()
            )
            
            for ac in asset_caps:
                if ac.asset_id not in asset_capabilities_map:
                    asset_capabilities_map[ac.asset_id] = []
                asset_capabilities_map[ac.asset_id].append({
                    'capability_id': str(ac.capability_id),
                    'code': ac.capability.code,
                    'name': ac.capability.name,
                    'support_level': ac.support_level,  # 'supported', 'not_supported', 'unknown'
                    'notes': ac.notes,
                    'evidence_ref': ac.evidence_ref,
                })
        except Exception as e:
            logger.warning(f"Error loading asset capabilities (tables may not exist yet): {e}")
            # If capabilities don't exist yet, continue with empty map
            asset_capabilities_map = {}
    
    # Helper function to map asset type name to typical_roles
    def asset_type_matches_typical_roles(asset_type_name, typical_roles):
        """Check if asset type name matches any of the typical_roles"""
        if not asset_type_name or not typical_roles:
            return False
        # Normalize: lowercase and remove spaces/special chars
        asset_type_normalized = asset_type_name.lower().replace(' ', '').replace('-', '').replace('_', '')
        for role in typical_roles:
            role_normalized = role.lower().replace(' ', '').replace('-', '').replace('_', '')
            # Check if asset type contains the role or vice versa
            if role_normalized in asset_type_normalized or asset_type_normalized in role_normalized:
                return True
            # Also check common mappings
            role_mappings = {
                'plc': ['plc', 'controller', 'programmable'],
                'hmi': ['hmi', 'human', 'machine', 'interface'],
                'server': ['server', 'scada', 'historian'],
                'firewall': ['firewall', 'fw'],
                'rtu': ['rtu', 'remote', 'terminal'],
                'router': ['router', 'switch'],
                'data_diode': ['diode', 'unidirectional']
            }
            if role_normalized in role_mappings:
                for keyword in role_mappings[role_normalized]:
                    if keyword in asset_type_normalized:
                        return True
        return False
    
    # Build evidence list for assets
    asset_evidence = []
    for asset in zone_assets:
        asset_caps = asset_capabilities_map.get(asset.id, [])
        asset_type_name = asset.asset_type.name if asset.asset_type else None
        
        # Check which required capabilities this asset has
        relevant_caps = []
        for req_cap in required_capabilities:
            if req_cap.get('applies_to_asset'):
                # First check: explicit asset capability
                matching_cap = next((ac for ac in asset_caps if ac.get('capability_id') == req_cap.get('capability_id')), None)
                if matching_cap:
                    relevant_caps.append({
                        'capability': req_cap,
                        'asset_capability': matching_cap,
                        'status': 'verified' if matching_cap.get('support_level') == 'supported' else 'declared' if matching_cap.get('support_level') != 'unknown' else 'unknown',
                        'source': 'explicit'  # Explicitly declared
                    })
                # Second check: infer from asset_type and typical_roles
                elif asset_type_name and req_cap.get('typical_roles'):
                    if asset_type_matches_typical_roles(asset_type_name, req_cap.get('typical_roles')):
                        relevant_caps.append({
                            'capability': req_cap,
                            'asset_capability': {
                                'capability_id': req_cap.get('capability_id'),
                                'code': req_cap.get('code'),
                                'name': req_cap.get('name'),
                                'support_level': 'unknown',  # Inferred, not verified
                                'notes': f"Inferred from asset type '{asset_type_name}' matching typical roles: {', '.join(req_cap.get('typical_roles', []))}",
                                'evidence_ref': None
                            },
                            'status': 'inferred',  # Inferred from asset type
                            'source': 'asset_type'  # Inferred from asset type
                        })
        
        if relevant_caps:
            asset_evidence.append({
                'asset_id': str(asset.id),
                'asset_name': asset.name,
                'asset_type': asset_type_name,
                'capabilities': relevant_caps,
                'status': 'verified' if any(c['status'] == 'verified' for c in relevant_caps) else 'declared' if any(c['status'] == 'declared' for c in relevant_caps) else 'inferred'
            })
    
    # Get conduits connected to this zone
    zone_conduits = (
        db.query(Conduit)
        .filter(
            or_(
                Conduit.from_zone_id == zone_id,
                Conduit.to_zone_id == zone_id
            ),
            Conduit.tenant_id == current_user.tenant_id,
            Conduit.deleted_at.is_(None)
        )
        .all()
    )
    
    # Get conduit assets and their capabilities
    conduit_evidence = []
    for conduit in zone_conduits:
        try:
            # Get assets associated with this conduit
            conduit_assets = (
                db.query(Asset)
                .join(ConduitAsset, Asset.id == ConduitAsset.asset_id)
                .filter(
                    ConduitAsset.conduit_id == conduit.id,
                    ConduitAsset.tenant_id == current_user.tenant_id,
                    Asset.deleted_at.is_(None)
                )
                .all()
            )
            
            # Check capabilities of conduit assets
            for ca in conduit_assets:
                ca_caps = asset_capabilities_map.get(ca.id, [])
                relevant_caps = []
                for req_cap in required_capabilities:
                    if req_cap.get('applies_to_conduit'):
                        matching_cap = next((ac for ac in ca_caps if ac.get('capability_id') == req_cap.get('capability_id')), None)
                        if matching_cap:
                            relevant_caps.append({
                                'capability': req_cap,
                                'asset_capability': matching_cap,
                                'status': 'verified' if matching_cap.get('support_level') == 'supported' else 'declared'
                            })
                
                if relevant_caps:
                    # Get role from ConduitAsset relationship
                    try:
                        conduit_asset_rel = (
                            db.query(ConduitAsset)
                            .filter(
                                ConduitAsset.conduit_id == conduit.id,
                                ConduitAsset.asset_id == ca.id
                            )
                            .first()
                        )
                        role = conduit_asset_rel.role if conduit_asset_rel else 'enforcement'
                    except Exception:
                        role = 'enforcement'
                    
                    conduit_evidence.append({
                        'conduit_id': str(conduit.id),
                        'conduit_name': conduit.name,
                        'asset_id': str(ca.id),
                        'asset_name': ca.name,
                        'role': role,
                        'capabilities': relevant_caps,
                        'status': 'verified' if any(c['status'] == 'verified' for c in relevant_caps) else 'declared'
                    })
        except Exception as e:
            logger.warning(f"Error loading conduit assets (tables may not exist yet): {e}")
            # Continue without conduit evidence if table doesn't exist
            pass
    
    # Check for missing capabilities (declared but not verified)
    missing_capabilities = []
    try:
        for req_cap in required_capabilities:
            # Check if we have any verified evidence for this capability
            has_verified = False
            if req_cap.get('applies_to_asset'):
                has_verified = any(
                    any(c.get('status') == 'verified' for c in ae.get('capabilities', []) if c.get('capability', {}).get('capability_id') == req_cap.get('capability_id'))
                    for ae in asset_evidence
                )
            if req_cap.get('applies_to_conduit') and not has_verified:
                has_verified = any(
                    any(c.get('status') == 'verified' for c in ce.get('capabilities', []) if c.get('capability', {}).get('capability_id') == req_cap.get('capability_id'))
                    for ce in conduit_evidence
                )
            
            if not has_verified:
                missing_capabilities.append({
                    'capability': req_cap,
                    'message': f"Nessun asset o conduit verificato con {req_cap.get('name', 'capability')}"
                })
    except Exception as e:
        logger.warning(f"Error checking missing capabilities: {e}")
        missing_capabilities = []
    
    # C. Get current assessment(s) if exist
    assessment_data = None
    re_assessments_payload = []
    try:
        all_assessments = crud_sr_assessments.list_sr_assessments_for_sr_and_object(
            db, sr_id, "zone", zone_id, current_user.tenant_id
        )
        for row in all_assessments:
            if row.enhancement_level is not None:
                re_assessments_payload.append(
                    {
                        "enhancement_level": row.enhancement_level,
                        "status": row.status,
                        "justification": row.justification,
                        "assessed_at": row.assessed_at.isoformat()
                        if row.assessed_at
                        else None,
                    }
                )

        current_assessment = next(
            (a for a in all_assessments if a.enhancement_level is None),
            all_assessments[0] if all_assessments and not re_assessments_payload else None,
        )

        if current_assessment:
            # Get evidence for this assessment
            try:
                evidence = (
                    db.query(SRAssessmentEvidence)
                    .join(Asset, SRAssessmentEvidence.asset_id == Asset.id)
                    .join(SecurityCapability, SRAssessmentEvidence.capability_id == SecurityCapability.id)
                    .filter(SRAssessmentEvidence.sr_assessment_id == current_assessment.id)
                    .all()
                )
                
                assessment_data = {
                    'id': str(current_assessment.id),
                    'status': current_assessment.status,
                    'justification': current_assessment.justification,
                    'assessed_at': current_assessment.assessed_at.isoformat() if current_assessment.assessed_at else None,
                    'evidence': [
                        {
                            'asset_id': str(e.asset_id),
                            'asset_name': e.asset.name if e.asset else None,
                            'capability_id': str(e.capability_id),
                            'capability_name': e.capability.name if e.capability else None,
                            'comment': e.comment
                        }
                        for e in evidence
                    ]
                }
            except Exception as e:
                logger.warning(f"Error loading assessment evidence (tables may not exist yet): {e}")
                # Return assessment without evidence if table doesn't exist
                assessment_data = {
                    'id': str(current_assessment.id),
                    'status': current_assessment.status,
                    'justification': current_assessment.justification,
                    'assessed_at': current_assessment.assessed_at.isoformat() if current_assessment.assessed_at else None,
                    'evidence': []
                }
    except Exception as e:
        logger.warning(f"Error loading current assessment (tables may not exist yet): {e}")
        # Continue without current assessment if table doesn't exist
        assessment_data = None

    re_rows = (
        db.query(RequirementEnhancement)
        .filter(RequirementEnhancement.security_requirement_id == sr_id)
        .order_by(RequirementEnhancement.enhancement_level)
        .all()
    )
    re_status_by_level = {
        item["enhancement_level"]: item["status"] for item in re_assessments_payload
    }
    requirement_enhancements = [
        {
            "enhancement_level": re.enhancement_level,
            "title": re.title,
            "description": re.description,
            "assessment_status": re_status_by_level.get(re.enhancement_level),
        }
        for re in re_rows
    ]

    try:
        return {
            'sr': {
                'id': str(sr.id),
                'requirement_id': sr.requirement_id,
                'title': sr.title,
                'description': sr.description or '',
            },
            'requirement_enhancements': requirement_enhancements,
            're_assessments': re_assessments_payload,
            'required_capabilities': required_capabilities or [],
            'available_evidence': {
                'assets': asset_evidence or [],
                'conduits': conduit_evidence or [],
            },
            'missing_capabilities': missing_capabilities or [],
            'current_assessment': assessment_data
        }
    except Exception as e:
        logger.error(f"Error building assessment-assist response: {e}", exc_info=True)
        # Return a minimal valid response even if there's an error
        return {
            'sr': {
                'id': str(sr.id),
                'requirement_id': sr.requirement_id,
                'title': sr.title,
                'description': sr.description or '',
            },
            'required_capabilities': [],
            'available_evidence': {
                'assets': [],
                'conduits': [],
            },
            'missing_capabilities': [],
            'current_assessment': None
        }
    except Exception as e:
        logger.error(f"Error building assessment-assist response: {e}", exc_info=True)
        # Return a minimal valid response even if there's an error
        return {
            'sr': {
                'id': str(sr.id),
                'requirement_id': sr.requirement_id,
                'title': sr.title,
                'description': sr.description or '',
            },
            'required_capabilities': [],
            'available_evidence': {
                'assets': [],
                'conduits': [],
            },
            'missing_capabilities': [],
            'current_assessment': None
        }


_VALID_ASSESSMENT_STATUSES = frozenset({
    "compliant",
    "non_compliant",
    "partial",
    "not_applicable",
    "insufficient_info",
})


def _validate_assessment_status(status: str, justification: Optional[str]) -> None:
    if status not in _VALID_ASSESSMENT_STATUSES:
        raise ErrorCodeException(status_code=400, error_code=ErrorCode.INVALID_INPUT)
    if status != "compliant" and not justification:
        raise ErrorCodeException(status_code=400, error_code=ErrorCode.INVALID_INPUT)


def _upsert_single_sr_assessment(
    db: Session,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    sr_id: uuid.UUID,
    object_type: str,
    object_id: uuid.UUID,
    status: str,
    justification: Optional[str],
    enhancement_level: Optional[int],
) -> SRAssessment:
    if enhancement_level is not None and not (1 <= enhancement_level <= 4):
        raise ErrorCodeException(status_code=400, error_code=ErrorCode.INVALID_INPUT)

    existing = crud_sr_assessments.get_sr_assessment_by_sr_and_object(
        db, sr_id, object_type, object_id, tenant_id, enhancement_level
    )
    if existing:
        return crud_sr_assessments.update_sr_assessment(
            db,
            existing.id,
            SRAssessmentUpdate(
                status=status,
                justification=justification,
                assessor_id=user_id,
            ),
            tenant_id,
        )
    return crud_sr_assessments.create_sr_assessment(
        db,
        SRAssessmentCreate(
            sr_id=sr_id,
            object_type=object_type,
            object_id=object_id,
            status=status,
            justification=justification,
            assessor_id=user_id,
            enhancement_level=enhancement_level,
        ),
        tenant_id,
    )


def _clear_conflicting_assessments(
    db: Session,
    tenant_id: uuid.UUID,
    sr_id: uuid.UUID,
    object_type: str,
    object_id: uuid.UUID,
    *,
    per_re: bool,
) -> None:
    """Legacy SR-level vs per-RE assessments are mutually exclusive for one SR/object."""
    rows = crud_sr_assessments.list_sr_assessments_for_sr_and_object(
        db, sr_id, object_type, object_id, tenant_id
    )
    for row in rows:
        if per_re and row.enhancement_level is None:
            db.delete(row)
        elif not per_re and row.enhancement_level is not None:
            db.delete(row)


def _attach_evidence(
    db: Session,
    tenant_id: uuid.UUID,
    assessment_id: uuid.UUID,
    evidence_list: list,
) -> int:
    db.query(SRAssessmentEvidence).filter(
        SRAssessmentEvidence.sr_assessment_id == assessment_id
    ).delete()
    for ev in evidence_list:
        db.add(
            SRAssessmentEvidence(
                tenant_id=tenant_id,
                sr_assessment_id=assessment_id,
                asset_id=uuid.UUID(ev["asset_id"]),
                capability_id=uuid.UUID(ev["capability_id"]),
                comment=ev.get("comment"),
            )
        )
    return len(evidence_list)


def _save_sr_assessment(
    db: Session,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    sr_id: uuid.UUID,
    object_type: str,
    object_id: uuid.UUID,
    assessment_data: dict,
) -> tuple:
    """
    Persist SR or per-RE assessments + optional evidence.
    Body may include:
    - status + optional enhancement_level (single)
    - re_assessments: [{enhancement_level, status, justification?}, ...]
    """
    evidence_list = assessment_data.get("evidence", [])
    re_assessments = assessment_data.get("re_assessments")

    if re_assessments:
        _clear_conflicting_assessments(
            db, tenant_id, sr_id, object_type, object_id, per_re=True
        )
        last_assessment = None
        for item in re_assessments:
            level = item.get("enhancement_level")
            status = item.get("status")
            if level is None or status is None:
                raise ErrorCodeException(status_code=400, error_code=ErrorCode.INVALID_INPUT)
            justification = item.get("justification") or assessment_data.get("justification")
            _validate_assessment_status(status, justification)
            last_assessment = _upsert_single_sr_assessment(
                db,
                tenant_id,
                user_id,
                sr_id,
                object_type,
                object_id,
                status,
                justification,
                int(level),
            )
        evidence_count = 0
        if last_assessment and evidence_list:
            evidence_count = _attach_evidence(
                db, tenant_id, last_assessment.id, evidence_list
            )
        db.commit()
        return last_assessment, last_assessment.id if last_assessment else None, evidence_count

    status = assessment_data.get("status")
    if not status:
        raise ErrorCodeException(status_code=400, error_code=ErrorCode.INVALID_INPUT)
    justification = assessment_data.get("justification")
    _validate_assessment_status(status, justification)

    enhancement_level = assessment_data.get("enhancement_level")
    if enhancement_level is not None:
        enhancement_level = int(enhancement_level)
        _clear_conflicting_assessments(
            db, tenant_id, sr_id, object_type, object_id, per_re=True
        )
    else:
        _clear_conflicting_assessments(
            db, tenant_id, sr_id, object_type, object_id, per_re=False
        )

    assessment = _upsert_single_sr_assessment(
        db,
        tenant_id,
        user_id,
        sr_id,
        object_type,
        object_id,
        status,
        justification,
        enhancement_level,
    )
    evidence_count = _attach_evidence(db, tenant_id, assessment.id, evidence_list)
    db.commit()
    return assessment, assessment.id, evidence_count


@router.post("/zone/{zone_id}/sr/{sr_id}/assessment", response_model=dict, status_code=201)
@audit_log_action("create_sr_assessment", "SecurityZone", model_class=SecurityZone)
def create_or_update_sr_assessment(
    zone_id: uuid.UUID,
    sr_id: uuid.UUID,
    assessment_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("compliance", 2)),
):
    """
    Create or update SR assessment for a zone.
    Body should contain:
    - status: 'compliant', 'non_compliant', 'partial', 'not_applicable', 'insufficient_info'
    - justification: required if status != 'compliant'
    - evidence: list of {asset_id, capability_id, comment}
    """
    # Verify zone exists
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
    
    # Verify SR exists
    sr = db.query(SecurityRequirement).filter(SecurityRequirement.id == sr_id).first()
    if not sr:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)
    
    if not sr.applies_to_zones:
        raise ErrorCodeException(status_code=400, error_code=ErrorCode.INVALID_INPUT)

    assessment, assessment_id, evidence_count = _save_sr_assessment(
        db,
        current_user.tenant_id,
        current_user.id,
        sr_id,
        "zone",
        zone_id,
        assessment_data,
    )

    # Recalculate zone SL-A and compliance status from SRAssessment data
    try:
        updated_zone = ISA62443ComplianceEngine.update_zone_security_levels(db, str(zone_id))
        zone_updated = {
            'security_level_achieved': updated_zone.security_level_achieved,
            'compliance_status': updated_zone.compliance_status,
            'security_level_capability': updated_zone.security_level_capability,
            'last_assessment_date': updated_zone.last_assessment_date.isoformat() if updated_zone.last_assessment_date else None,
        }
    except Exception as e:
        logger.warning(f"Zone SL recalculation after assessment failed: {e}")
        zone_updated = None
    
    return {
        'id': str(assessment_id),
        'status': assessment.status,
        'justification': assessment.justification,
        'evidence_count': evidence_count,
        'zone_updated': zone_updated
    }


@router.get("/asset/{asset_id}/security-requirements", response_model=List[dict])
def get_asset_security_requirements(
    asset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("compliance", 1)),
):
    """SR applicable to assets with assessment status."""
    asset = (
        db.query(Asset)
        .filter(Asset.id == asset_id, Asset.tenant_id == current_user.tenant_id)
        .first()
    )
    if not asset:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)

    requirements = (
        db.query(SecurityRequirement)
        .filter(SecurityRequirement.applies_to_assets == True)
        .order_by(SecurityRequirement.requirement_id)
        .all()
    )
    assessments = (
        db.query(SRAssessment)
        .filter(
            SRAssessment.object_type == "asset",
            SRAssessment.object_id == asset_id,
            SRAssessment.tenant_id == current_user.tenant_id,
        )
        .all()
    )
    assessment_map = {a.sr_id: a for a in assessments}

    result = []
    for req in requirements:
        assessment = assessment_map.get(req.id)
        result.append({
            "sr_id": str(req.id),
            "requirement_id": req.requirement_id,
            "title": req.title,
            "min_security_level": req.min_security_level,
            "max_security_level": req.max_security_level,
            "status": assessment.status if assessment else None,
            "justification": assessment.justification if assessment else None,
            "assessed_at": assessment.assessed_at.isoformat() if assessment and assessment.assessed_at else None,
        })
    return result


@router.post("/asset/{asset_id}/sr/{sr_id}/assessment", response_model=dict, status_code=201)
@audit_log_action("create_sr_assessment", "Asset", model_class=Asset)
def create_or_update_asset_sr_assessment(
    asset_id: uuid.UUID,
    sr_id: uuid.UUID,
    assessment_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("compliance", 2)),
):
    asset = (
        db.query(Asset)
        .filter(Asset.id == asset_id, Asset.tenant_id == current_user.tenant_id)
        .first()
    )
    if not asset:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)

    sr = db.query(SecurityRequirement).filter(SecurityRequirement.id == sr_id).first()
    if not sr or not sr.applies_to_assets:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)

    assessment, assessment_id, evidence_count = _save_sr_assessment(
        db,
        current_user.tenant_id,
        current_user.id,
        sr_id,
        "asset",
        asset_id,
        assessment_data,
    )

    try:
        updated_asset = ISA62443ComplianceEngine.update_asset_iec62443_levels(db, str(asset_id))
        asset_updated = {
            "security_level_achieved": updated_asset.security_level_achieved,
            "isa62443_compliance_status": updated_asset.isa62443_compliance_status,
            "isa62443_last_assessment": (
                updated_asset.isa62443_last_assessment.isoformat()
                if updated_asset.isa62443_last_assessment
                else None
            ),
        }
    except Exception as e:
        logger.warning(f"Asset SL recalculation failed: {e}")
        asset_updated = None

    return {
        "id": str(assessment_id),
        "status": assessment.status,
        "justification": assessment.justification,
        "evidence_count": evidence_count,
        "asset_updated": asset_updated,
    }


@router.post("/asset/{asset_id}/recalculate", response_model=dict)
def recalculate_asset_iec62443(
    asset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("compliance", 2)),
):
    asset = (
        db.query(Asset)
        .filter(Asset.id == asset_id, Asset.tenant_id == current_user.tenant_id)
        .first()
    )
    if not asset:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)
    updated = ISA62443ComplianceEngine.update_asset_iec62443_levels(db, str(asset_id))
    return {
        "asset_id": str(updated.id),
        "security_level_target": updated.security_level_target,
        "security_level_achieved": updated.security_level_achieved,
        "isa62443_compliance_status": updated.isa62443_compliance_status,
    }


@router.get("/conduit/{conduit_id}/security-requirements", response_model=dict)
def get_conduit_security_requirements(
    conduit_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("compliance", 1)),
):
    conduit = (
        db.query(Conduit)
        .filter(Conduit.id == conduit_id, Conduit.tenant_id == current_user.tenant_id)
        .first()
    )
    if not conduit:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)

    requirements = (
        db.query(SecurityRequirement)
        .filter(SecurityRequirement.applies_to_conduits == True)
        .order_by(SecurityRequirement.requirement_id)
        .all()
    )
    assessments = (
        db.query(SRAssessment)
        .filter(
            SRAssessment.object_type == "conduit",
            SRAssessment.object_id == conduit_id,
            SRAssessment.tenant_id == current_user.tenant_id,
        )
        .all()
    )
    assessment_map = {a.sr_id: a for a in assessments}
    meta = ISA62443ComplianceEngine.get_conduit_sl_metadata(db, conduit)

    result = []
    for req in requirements:
        assessment = assessment_map.get(req.id)
        result.append({
            "sr_id": str(req.id),
            "requirement_id": req.requirement_id,
            "title": req.title,
            "min_security_level": req.min_security_level,
            "status": assessment.status if assessment else None,
            "justification": assessment.justification if assessment else None,
        })
    return {
        "requirements": result,
        "security_level_achieved": meta["security_level_achieved"],
        "sl_achieved_source": meta["sl_achieved_source"],
    }


@router.post("/conduit/{conduit_id}/sr/{sr_id}/assessment", response_model=dict, status_code=201)
@audit_log_action("create_sr_assessment", "Conduit", model_class=Conduit)
def create_or_update_conduit_sr_assessment(
    conduit_id: uuid.UUID,
    sr_id: uuid.UUID,
    assessment_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("compliance", 2)),
):
    conduit = (
        db.query(Conduit)
        .filter(Conduit.id == conduit_id, Conduit.tenant_id == current_user.tenant_id)
        .first()
    )
    if not conduit:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)

    sr = db.query(SecurityRequirement).filter(SecurityRequirement.id == sr_id).first()
    if not sr or not sr.applies_to_conduits:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)

    assessment, assessment_id, evidence_count = _save_sr_assessment(
        db,
        current_user.tenant_id,
        current_user.id,
        sr_id,
        "conduit",
        conduit_id,
        assessment_data,
    )

    try:
        updated = ISA62443ComplianceEngine.update_conduit_iec62443_levels(db, str(conduit_id))
        meta = ISA62443ComplianceEngine.get_conduit_sl_metadata(db, updated)
        conduit_updated = {
            "security_level_achieved": updated.security_level_achieved,
            "compliance_status": updated.compliance_status,
            "sl_achieved_source": meta["sl_achieved_source"],
        }
    except Exception as e:
        logger.warning(f"Conduit SL recalculation failed: {e}")
        conduit_updated = None

    return {
        "id": str(assessment_id),
        "status": assessment.status,
        "justification": assessment.justification,
        "evidence_count": evidence_count,
        "conduit_updated": conduit_updated,
    }


# ============================================================================
# COMPLIANCE OVERVIEW ENDPOINTS
# ============================================================================

@router.get("/requirements", response_model=List[dict])
def get_security_requirements(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("compliance", 1)),
):
    """Get all security requirements"""
    requirements = (
        db.query(SecurityRequirement)
        .order_by(SecurityRequirement.requirement_id)
        .all()
    )
    
    result = []
    for req in requirements:
        result.append({
            'requirement_id': req.requirement_id,
            'title': req.title,
            'description': req.description,
            'requirement_category': req.requirement_category,
            'applies_to_zones': req.applies_to_zones,
            'applies_to_conduits': req.applies_to_conduits,
            'applies_to_assets': req.applies_to_assets,
            'min_security_level': req.min_security_level,
            'max_security_level': req.max_security_level,
        })
    
    return result


@router.get("/gap-analysis", response_model=dict)
def get_gap_analysis(
    zone_id: Optional[uuid.UUID] = Query(None, description="Filter by zone ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("compliance", 1)),
):
    """Get gap analysis for all zones or a specific zone"""
    # Build query for zones - filter out deleted zones
    query = (
        db.query(SecurityZone)
        .filter(
            SecurityZone.tenant_id == current_user.tenant_id,
            SecurityZone.deleted_at.is_(None)
        )
    )
    
    if zone_id:
        query = query.filter(SecurityZone.id == zone_id)
    
    zones = query.all()
    
    if not zones:
        return {
            'zones': [],
            'summary': {
                'total': 0,
                'compliant': 0,
                'partial': 0,
                'non_compliant': 0,
                'not_assessed': 0
            }
        }
    
    # Get all SR assessments for these zones
    zone_ids = [zone.id for zone in zones]
    try:
        assessments = (
            db.query(SRAssessment)
            .filter(
                SRAssessment.object_type == 'zone',
                SRAssessment.object_id.in_(zone_ids),
                SRAssessment.tenant_id == current_user.tenant_id
            )
            .all()
        )
        
        # Group assessments by zone
        assessments_by_zone = {}
        for assessment in assessments:
            zone_id_str = str(assessment.object_id)
            if zone_id_str not in assessments_by_zone:
                assessments_by_zone[zone_id_str] = []
            assessments_by_zone[zone_id_str].append(assessment)
    except Exception as e:
        logger.warning(f"Error loading SR assessments for gap analysis: {e}")
        assessments_by_zone = {}
    
    result_zones = []
    summary = {
        'total': 0,
        'compliant': 0,
        'partial': 0,
        'non_compliant': 0,
        'not_assessed': 0
    }
    
    for zone in zones:
        zone_id_str = str(zone.id)
        zone_assessments = assessments_by_zone.get(zone_id_str, [])
        
        # Count assessments by status
        compliant_count = sum(1 for a in zone_assessments if a.status == 'compliant')
        partial_count = sum(1 for a in zone_assessments if a.status == 'partial')
        non_compliant_count = sum(1 for a in zone_assessments if a.status == 'non_compliant')
        not_applicable_count = sum(1 for a in zone_assessments if a.status == 'not_applicable')
        
        # Use the compliance_status from the zone model if available, otherwise calculate it
        # This ensures consistency with the security zones page
        compliance_status = zone.compliance_status
        if not compliance_status or compliance_status == 'not_assessed':
            compliance_status = ISA62443ComplianceEngine.calculate_zone_compliance_status(
                db, zone
            )
        
        # Calculate gap
        gap = None
        if zone.security_level_target and zone.security_level_achieved:
            gap = zone.security_level_target - zone.security_level_achieved
        
        result_zones.append({
            'zone_id': str(zone.id),
            'zone_name': zone.name,
            'security_level_target': zone.security_level_target,
            'security_level_achieved': zone.security_level_achieved,
            'gap': gap,
            'compliance_status': compliance_status,
            'non_compliant_count': non_compliant_count,
            'missing_requirements_count': 0  # Could be calculated based on total SRs vs assessed
        })
        
        # Update summary
        summary['total'] += 1
        if compliance_status == 'compliant':
            summary['compliant'] += 1
        elif compliance_status == 'partial':
            summary['partial'] += 1
        elif compliance_status == 'non_compliant':
            summary['non_compliant'] += 1
        else:
            summary['not_assessed'] += 1
    
    return {
        'zones': result_zones,
        'summary': summary
    }


@router.get("/zone/{zone_id}/audit-export")
def export_zone_audit(
    zone_id: uuid.UUID,
    format: str = Query("json", pattern="^(json|csv)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("compliance", 1)),
):
    """
    Audit matrix: zone × SR × RE × assessment status.
    format=json (default) or csv for spreadsheet / external auditor.
    """
    zone = (
        db.query(SecurityZone)
        .filter(
            SecurityZone.id == zone_id,
            SecurityZone.tenant_id == current_user.tenant_id,
            SecurityZone.deleted_at.is_(None),
        )
        .first()
    )
    if not zone:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)

    if zone.security_level_achieved is None and zone.security_level_target:
        zone.security_level_achieved = (
            ISA62443ComplianceEngine.calculate_zone_security_level_achieved(db, zone)
        )

    payload = build_zone_audit_export(db, zone)
    if format == "csv":
        csv_body = audit_export_to_csv(payload)
        filename = f"iec62443-audit-{zone.name.replace(' ', '_')[:40]}.csv"
        return PlainTextResponse(
            content=csv_body,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    return payload
