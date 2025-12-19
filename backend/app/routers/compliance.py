# backend/app/routers/compliance.py
import uuid
import re
import logging
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query
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
from app.services.isa62443_compliance_engine import ISA62443ComplianceEngine
from app.errors.exceptions import ErrorCodeException
from app.errors.error_codes import ErrorCode
from app.crud import sr_assessments as crud_sr_assessments
from app.crud import asset_capabilities as crud_asset_capabilities
from app.schemas.sr_assessment import SRAssessmentCreate, SRAssessmentUpdate
from app.schemas.sr_assessment_evidence import SRAssessmentEvidenceCreate

router = APIRouter(prefix="/compliance", tags=["Compliance"])


# ============================================================================
# FOUNDATION REQUIREMENTS ENDPOINTS
# ============================================================================

@router.get("/zone/{zone_id}/foundation-requirements", response_model=List[dict])
def get_zone_foundation_requirements(
    zone_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
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
        
        # Calculate statistics
        total_sr = len(sr_requirements)
        compliant_count = 0
        partial_count = 0
        non_compliant_count = 0
        not_applicable_count = 0
        
        for sr in sr_requirements:
            # Check SR assessments - use sr.id (UUID) for lookup
            assessment = compliance_map.get(sr.id)
            if assessment:
                status = assessment.status
                if status == 'compliant':
                    compliant_count += 1
                elif status == 'partial':
                    partial_count += 1
                elif status == 'non_compliant':
                    non_compliant_count += 1
                elif status == 'not_applicable':
                    not_applicable_count += 1
        
        # Calculate compliance percentage
        # Consider: compliant = 100%, partial = 50%, non_compliant = 0%, not_applicable = excluded
        assessed_count = compliant_count + partial_count + non_compliant_count + not_applicable_count
        if total_sr > 0:
            # Calculate weighted percentage: (compliant * 1.0 + partial * 0.5) / total_sr
            weighted_score = (compliant_count * 1.0) + (partial_count * 0.5)
            compliance_percentage = (weighted_score / total_sr) * 100
        else:
            compliance_percentage = 0
        
        result.append({
            'id': str(fr.id) if hasattr(fr, 'id') else f"fr-{fr.requirement_id.replace('FR', '').strip()}",
            'requirement_id': fr.requirement_id,
            'title': fr.title,
            'description': fr.description,
            'compliant_count': compliant_count,
            'partial_count': partial_count,
            'non_compliant_count': non_compliant_count,
            'not_applicable_count': not_applicable_count,
            'total_sr': total_sr,
            'compliance_percentage': round(compliance_percentage, 1)
        })
    
    return result


@router.get("/zone/{zone_id}/security-requirements/{fr_id}", response_model=List[dict])
def get_zone_security_requirements_by_fr(
    zone_id: uuid.UUID,
    fr_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
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
        # Return empty summary if tables don't exist
        summary = {
            'compliant': 0,
            'partial': 0,
            'non_compliant': 0,
            'not_applicable': 0,
            'insufficient_info': 0
        }
    
    return summary


# ============================================================================
# NEW CAPABILITY-BASED ASSESSMENT ENDPOINTS
# ============================================================================

@router.get("/zone/{zone_id}/sr/{sr_id}/assessment-assist", response_model=dict)
def get_sr_assessment_assist(
    zone_id: uuid.UUID,
    sr_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
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
        raise ErrorCodeException(status_code=500, error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))
    
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
    
    # C. Get current assessment if exists
    assessment_data = None
    try:
        current_assessment = crud_sr_assessments.get_sr_assessment_by_sr_and_object(
            db, sr_id, 'zone', zone_id, current_user.tenant_id
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
    
    try:
        return {
            'sr': {
                'id': str(sr.id),
                'requirement_id': sr.requirement_id,
                'title': sr.title,
                'description': sr.description or '',
            },
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


@router.post("/zone/{zone_id}/sr/{sr_id}/assessment", response_model=dict, status_code=201)
@audit_log_action("create_sr_assessment", "SecurityZone", model_class=SecurityZone)
def create_or_update_sr_assessment(
    zone_id: uuid.UUID,
    sr_id: uuid.UUID,
    assessment_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
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
    
    status = assessment_data.get('status')
    if status not in ['compliant', 'non_compliant', 'partial', 'not_applicable', 'insufficient_info']:
        raise ErrorCodeException(status_code=400, error_code=ErrorCode.INVALID_INPUT, detail="Invalid status")
    
    justification = assessment_data.get('justification')
    if status != 'compliant' and not justification:
        raise ErrorCodeException(status_code=400, error_code=ErrorCode.INVALID_INPUT, detail="Justification required for non-compliant status")
    
    # Check if assessment already exists
    existing_assessment = crud_sr_assessments.get_sr_assessment_by_sr_and_object(
        db, sr_id, 'zone', zone_id, current_user.tenant_id
    )
    
    if existing_assessment:
        # Update existing assessment
        update_data = SRAssessmentUpdate(
            status=status,
            justification=justification,
            assessor_id=current_user.id
        )
        assessment = crud_sr_assessments.update_sr_assessment(
            db, existing_assessment.id, update_data, current_user.tenant_id
        )
        assessment_id = assessment.id
    else:
        # Create new assessment
        create_data = SRAssessmentCreate(
            sr_id=sr_id,
            object_type='zone',
            object_id=zone_id,
            status=status,
            justification=justification,
            assessor_id=current_user.id
        )
        assessment = crud_sr_assessments.create_sr_assessment(
            db, create_data, current_user.tenant_id
        )
        assessment_id = assessment.id
    
    # Handle evidence
    evidence_list = assessment_data.get('evidence', [])
    
    # Delete existing evidence
    db.query(SRAssessmentEvidence).filter(
        SRAssessmentEvidence.sr_assessment_id == assessment_id
    ).delete()
    
    # Create new evidence records
    for ev in evidence_list:
        evidence = SRAssessmentEvidence(
            tenant_id=current_user.tenant_id,
            sr_assessment_id=assessment_id,
            asset_id=uuid.UUID(ev['asset_id']),
            capability_id=uuid.UUID(ev['capability_id']),
            comment=ev.get('comment')
        )
        db.add(evidence)
    
    db.commit()
    
    # Recalculate zone SLA
    # TODO: Implement SLA recalculation based on assessments
    
    return {
        'id': str(assessment_id),
        'status': assessment.status,
        'justification': assessment.justification,
        'evidence_count': len(evidence_list)
    }
