# backend/app/services/isa62443_compliance_engine.py
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models import (
    SecurityZone,
    Conduit,
    Asset,
    SecurityRequirement,
    SecurityRequirementCompliance,
    AssetZoneMembership,
    SRAssessment,
)
from app.models.security_capability import SecurityCapability
from app.models.asset_capability import AssetCapability
from app.models.sr_capability import SRCapability
import logging

logger = logging.getLogger(__name__)


class ISA62443ComplianceEngine:
    """Engine for calculating ISA/IEC 62443 compliance and Security Levels"""
    
    @staticmethod
    def calculate_zone_security_level_achieved(
        db: Session,
        zone: SecurityZone
    ) -> Optional[int]:
        """
        Calculate Security Level Achieved (SL-A) for a Security Zone.
        
        ISA/IEC 62443 Compliance: SL-A is the highest SL where ALL requirements
        for that SL are compliant. Requirements are cumulative (SL-2 includes SL-1, etc.).
        
        Logic:
        1. Get all compliance records for the zone
        2. For each Security Level (1 to SL-T), get ALL requirements (cumulative)
        3. SL-A is the highest SL where ALL requirements are compliant
        4. No requirement can be "partial" or "non_compliant" to achieve an SL
        
        Returns: SL-A (1-4) or None if not calculable
        """
        if not zone.security_level_target:
            return None
        
        target_sl = zone.security_level_target
        
        # Get all requirements applicable to zones
        all_requirements = (
            db.query(SecurityRequirement)
            .filter(
                SecurityRequirement.applies_to_zones == True
            )
            .all()
        )
        
        if not all_requirements:
            return None
        
        # Prefer SRAssessment (new model); fallback to SecurityRequirementCompliance (legacy)
        compliance_map = {}  # req.id (UUID) -> status or record
        try:
            zone_assessments = (
                db.query(SRAssessment)
                .filter(
                    SRAssessment.object_type == 'zone',
                    SRAssessment.object_id == zone.id,
                    SRAssessment.tenant_id == zone.tenant_id
                )
                .all()
            )
            if zone_assessments:
                for a in zone_assessments:
                    compliance_map[a.sr_id] = a.status
        except Exception as e:
            logger.debug(f"SRAssessment not available for zone SL-A, using legacy: {e}")
        if not compliance_map:
            compliance_records = (
                db.query(SecurityRequirementCompliance)
                .filter(
                    SecurityRequirementCompliance.zone_id == zone.id,
                    SecurityRequirementCompliance.tenant_id == zone.tenant_id
                )
                .all()
            )
            compliance_map = {record.requirement_id: record for record in compliance_records}
        
        # Helper: is this requirement compliant? (map value is either status string or legacy record)
        def is_compliant(req_id, val):
            if val is None:
                return False
            if isinstance(val, str):
                return val == 'compliant'
            return getattr(val, 'compliance_status', None) == 'compliant'
        
        # Calculate SL-A: highest SL where ALL requirements are compliant
        # Requirements are cumulative: SL-2 includes all SL-1 requirements, etc.
        achieved_sl = None
        
        for sl in range(target_sl, 0, -1):
            # Get ALL requirements for this SL (cumulative)
            # SL-1: requirements with min_security_level = 1
            # SL-2: requirements with min_security_level <= 2 (includes SL-1)
            # SL-3: requirements with min_security_level <= 3 (includes SL-1, SL-2)
            # SL-4: requirements with min_security_level <= 4 (includes all)
            sl_requirements = [
                req for req in all_requirements
                if req.min_security_level <= sl and (
                    req.max_security_level is None or req.max_security_level >= sl
                )
            ]
            
            if not sl_requirements:
                continue
            
            # Check if ALL requirements for this SL are compliant
            all_compliant = True
            missing_requirements = []
            
            for req in sl_requirements:
                val = compliance_map.get(req.id)
                if not is_compliant(req.id, val):
                    all_compliant = False
                    missing_requirements.append(req.requirement_id)
            
            if all_compliant:
                # All requirements for this SL are compliant
                achieved_sl = sl
                logger.debug(f"Zone {zone.id}: SL-A = {sl} (all {len(sl_requirements)} requirements compliant)")
                break
            else:
                logger.debug(f"Zone {zone.id}: SL-{sl} not achieved - {len(missing_requirements)} requirements not compliant")
        
        return achieved_sl
    
    @staticmethod
    def calculate_asset_security_level_achieved(
        db: Session,
        asset: Asset
    ) -> Optional[int]:
        """
        Calculate Security Level Achieved (SL-A) for an Asset.
        
        Logic:
        1. If asset has explicit SL-A, use it
        2. If asset has zone memberships, consider all zones and use minimum SL-A (worst case)
        3. If asset is in a zone (deprecated security_zone_id), use zone SL-A
        4. Otherwise, calculate based on asset compliance records
        """
        # Check if asset has explicit SL-A
        if asset.security_level_achieved is not None:
            return asset.security_level_achieved
        
        # Check for zone memberships (new approach)
        memberships = (
            db.query(AssetZoneMembership)
            .filter(
                AssetZoneMembership.asset_id == asset.id,
                AssetZoneMembership.tenant_id == asset.tenant_id,
                AssetZoneMembership.deleted_at.is_(None)
            )
            .all()
        )
        
        if memberships:
            # Get SL-A for each zone membership
            zone_sl_as = []
            for membership in memberships:
                zone = db.query(SecurityZone).filter(SecurityZone.id == membership.security_zone_id).first()
                if zone:
                    zone_sl_a = ISA62443ComplianceEngine.calculate_zone_security_level_achieved(db, zone)
                    if zone_sl_a:
                        # If membership has SL-T override, use that for comparison
                        target_sl = membership.sl_target or zone.security_level_target
                        if target_sl:
                            # Use the minimum between zone SL-A and membership SL-T (worst case)
                            zone_sl_as.append(min(zone_sl_a, target_sl))
                        else:
                            zone_sl_as.append(zone_sl_a)
            
            if zone_sl_as:
                # Use minimum SL-A (worst case) - asset is only as secure as its weakest zone
                return min(zone_sl_as)
        
        # Fallback: If asset is in a zone (deprecated security_zone_id), use zone SL-A
        if asset.security_zone_id:
            zone = db.query(SecurityZone).filter(SecurityZone.id == asset.security_zone_id).first()
            if zone:
                zone_sl_a = ISA62443ComplianceEngine.calculate_zone_security_level_achieved(db, zone)
                if zone_sl_a:
                    return zone_sl_a
        
        # Calculate based on asset compliance records
        target_sl = asset.security_level_target
        if not target_sl:
            return None
        
        # Get requirements applicable to assets
        requirements = (
            db.query(SecurityRequirement)
            .filter(
                SecurityRequirement.applies_to_assets == True,
                SecurityRequirement.min_security_level <= target_sl
            )
            .all()
        )
        
        if not requirements:
            return None
        
        # Get compliance records
        compliance_records = (
            db.query(SecurityRequirementCompliance)
            .filter(
                SecurityRequirementCompliance.asset_id == asset.id,
                SecurityRequirementCompliance.tenant_id == asset.tenant_id
            )
            .all()
        )
        
        compliance_map = {
            record.requirement_id: record
            for record in compliance_records
        }
        
        # Calculate SL-A: highest SL where ALL requirements are compliant (cumulative)
        achieved_sl = None
        
        for sl in range(target_sl, 0, -1):
            # Get ALL requirements for this SL (cumulative)
            sl_requirements = [
                req for req in requirements
                if req.min_security_level <= sl and (
                    req.max_security_level is None or req.max_security_level >= sl
                )
            ]
            
            if not sl_requirements:
                continue
            
            # Check if ALL requirements for this SL are compliant
            all_compliant = True
            for req in sl_requirements:
                compliance = compliance_map.get(req.id)
                if not compliance or compliance.compliance_status != 'compliant':
                    all_compliant = False
                    break
            
            if all_compliant:
                achieved_sl = sl
                break
        
        return achieved_sl
    
    @staticmethod
    def calculate_conduit_security_level_achieved(
        db: Session,
        conduit: Conduit
    ) -> Optional[int]:
        """
        Calculate Security Level Achieved (SL-A) for a Conduit.
        
        Logic:
        1. Check encryption and authentication
        2. Check compliance with conduit requirements
        3. Calculate SL-A based on security properties
        """
        target_sl = conduit.security_level_target
        if not target_sl:
            return None
        
        # Base SL-A on security properties
        sl_a = 1
        
        # Encryption adds SL
        if conduit.is_encrypted:
            if conduit.encryption_type in ['tls', 'ipsec']:
                sl_a = max(sl_a, 2)
            else:
                sl_a = max(sl_a, 1)
        
        # Authentication adds SL
        if conduit.authentication_required:
            if conduit.authentication_method == 'certificate':
                sl_a = max(sl_a, 3)
            elif conduit.authentication_method in ['psk', 'username_password']:
                sl_a = max(sl_a, 2)
        
        # Check compliance records
        compliance_records = (
            db.query(SecurityRequirementCompliance)
            .filter(
                SecurityRequirementCompliance.conduit_id == conduit.id,
                SecurityRequirementCompliance.tenant_id == conduit.tenant_id
            )
            .all()
        )
        
        # Check compliance records for conduit requirements
        if compliance_records:
            # Get all requirements applicable to conduits
            conduit_requirements = (
                db.query(SecurityRequirement)
                .filter(
                    SecurityRequirement.applies_to_conduits == True,
                    SecurityRequirement.min_security_level <= target_sl
                )
                .all()
            )
            
            if conduit_requirements:
                compliance_map = {
                    record.requirement_id: record
                    for record in compliance_records
                }
                
                # Calculate SL-A: highest SL where ALL requirements are compliant
                for sl in range(target_sl, 0, -1):
                    sl_requirements = [
                        req for req in conduit_requirements
                        if req.min_security_level <= sl and (
                            req.max_security_level is None or req.max_security_level >= sl
                        )
                    ]
                    
                    if not sl_requirements:
                        continue
                    
                    # Check if ALL requirements for this SL are compliant
                    all_compliant = True
                    for req in sl_requirements:
                        compliance = compliance_map.get(req.id)
                        if not compliance or compliance.compliance_status != 'compliant':
                            all_compliant = False
                            break
                    
                    if all_compliant:
                        # Use the higher between property-based SL-A and compliance-based SL-A
                        sl_a = max(sl_a, sl)
                        break
        
        return min(sl_a, target_sl)
    
    @staticmethod
    def calculate_zone_compliance_status(
        db: Session,
        zone: SecurityZone
    ) -> str:
        """
        Calculate overall compliance status for a zone.
        Returns: 'compliant', 'non_compliant', 'partial', 'not_assessed'
        Uses SRAssessment when available; falls back to SecurityRequirementCompliance.
        """
        # Prefer SRAssessment (new model)
        try:
            zone_assessments = (
                db.query(SRAssessment)
                .filter(
                    SRAssessment.object_type == 'zone',
                    SRAssessment.object_id == zone.id,
                    SRAssessment.tenant_id == zone.tenant_id
                )
                .all()
            )
            if zone_assessments:
                compliant_count = sum(1 for a in zone_assessments if a.status == 'compliant')
                partial_count = sum(1 for a in zone_assessments if a.status == 'partial')
                non_compliant_count = sum(1 for a in zone_assessments if a.status == 'non_compliant')
                total_count = len(zone_assessments)
                if total_count > 0:
                    compliance_percentage = (compliant_count / total_count) * 100
                    if compliance_percentage >= 80:
                        return 'compliant'
                    if compliance_percentage >= 50 or partial_count > 0:
                        return 'partial'
                    return 'non_compliant'
        except Exception as e:
            logger.debug(f"SRAssessment not available for zone compliance status, using legacy: {e}")
        
        # Fallback: SecurityRequirementCompliance (legacy)
        compliance_records = (
            db.query(SecurityRequirementCompliance)
            .filter(
                SecurityRequirementCompliance.zone_id == zone.id,
                SecurityRequirementCompliance.tenant_id == zone.tenant_id
            )
            .all()
        )
        if not compliance_records:
            return 'not_assessed'
        compliant_count = sum(1 for r in compliance_records if r.compliance_status == 'compliant')
        partial_count = sum(1 for r in compliance_records if r.compliance_status == 'partial')
        total_count = len(compliance_records)
        if total_count == 0:
            return 'not_assessed'
        compliance_percentage = (compliant_count / total_count) * 100
        if compliance_percentage >= 80:
            return 'compliant'
        if compliance_percentage >= 50 or partial_count > 0:
            return 'partial'
        return 'non_compliant'
    
    @staticmethod
    def calculate_zone_security_level_capability(
        db: Session,
        zone: SecurityZone
    ) -> Optional[int]:
        """
        Calculate Security Level Capability (SL-C) for a Security Zone.
        
        SL-C represents the maximum capability of the system based on available
        Security Capabilities. It is calculated by checking if all required
        capabilities for each SL are available (explicit or inferred with high confidence).
        
        Logic:
        1. Get all Security Requirements for the zone's target SL
        2. Get all required Security Capabilities (via SRCapability mappings)
        3. For each SL (1 to SL-T), check if all required capabilities are available
        4. SL-C = highest SL where all required capabilities are available
        
        Returns: SL-C (1-4) or None if not calculable
        """
        if not zone.security_level_target:
            return None
        
        target_sl = zone.security_level_target
        
        # Get all requirements applicable to zones
        all_requirements = (
            db.query(SecurityRequirement)
            .filter(
                SecurityRequirement.applies_to_zones == True
            )
            .all()
        )
        
        if not all_requirements:
            return None
        
        # Get all assets in the zone (via memberships)
        zone_assets = (
            db.query(Asset)
            .join(AssetZoneMembership, Asset.id == AssetZoneMembership.asset_id)
            .filter(
                AssetZoneMembership.security_zone_id == zone.id,
                AssetZoneMembership.tenant_id == zone.tenant_id,
                AssetZoneMembership.deleted_at.is_(None),
                Asset.deleted_at.is_(None)
            )
            .all()
        )
        
        if not zone_assets:
            # No assets in zone, cannot determine capabilities
            return None
        
        # Get all AssetCapabilities for zone assets
        asset_ids = [asset.id for asset in zone_assets]
        asset_capabilities = (
            db.query(AssetCapability)
            .filter(
                AssetCapability.asset_id.in_(asset_ids),
                AssetCapability.tenant_id == zone.tenant_id
            )
            .all()
        )
        
        # Create map of available capabilities (explicit only, with support_level = 'supported')
        available_capabilities = set()
        for ac in asset_capabilities:
            if ac.support_level == 'supported':
                available_capabilities.add(ac.capability_id)
        
        # Also check inferred capabilities (from asset_type matching typical_roles)
        # For now, we only count explicit capabilities as "available" for SL-C
        # Inferred capabilities with high confidence could be considered in future
        
        # Calculate SL-C: highest SL where all required capabilities are available
        achieved_sl_c = None
        
        for sl in range(target_sl, 0, -1):
            # Get ALL requirements for this SL (cumulative)
            sl_requirements = [
                req for req in all_requirements
                if req.min_security_level <= sl and (
                    req.max_security_level is None or req.max_security_level >= sl
                )
            ]
            
            if not sl_requirements:
                continue
            
            # Get all required capabilities for these requirements
            requirement_ids = [req.id for req in sl_requirements]
            required_capabilities = (
                db.query(SRCapability)
                .filter(SRCapability.sr_id.in_(requirement_ids))
                .all()
            )
            
            if not required_capabilities:
                # No capabilities required for this SL, consider it achievable
                achieved_sl_c = sl
                break
            
            # Check if ALL required capabilities are available
            required_capability_ids = {rc.capability_id for rc in required_capabilities}
            all_available = required_capability_ids.issubset(available_capabilities)
            
            if all_available:
                achieved_sl_c = sl
                logger.debug(f"Zone {zone.id}: SL-C = {sl} (all {len(required_capability_ids)} required capabilities available)")
                break
            else:
                missing = required_capability_ids - available_capabilities
                logger.debug(f"Zone {zone.id}: SL-{sl} not achievable - {len(missing)} capabilities missing")
        
        return achieved_sl_c
    
    @staticmethod
    def update_zone_security_levels(
        db: Session,
        zone_id: str
    ) -> SecurityZone:
        """
        Recalculate and update SL-A, SL-C, and compliance status for a zone.
        Validates that SL-A ≤ SL-C ≤ SL-T.
        """
        zone = db.query(SecurityZone).filter(SecurityZone.id == zone_id).first()
        if not zone:
            raise ValueError(f"Zone {zone_id} not found")
        
        # Calculate SL-C first (capability level)
        sl_c = ISA62443ComplianceEngine.calculate_zone_security_level_capability(db, zone)
        zone.security_level_capability = sl_c
        
        # Calculate SL-A (achieved level)
        sl_a = ISA62443ComplianceEngine.calculate_zone_security_level_achieved(db, zone)
        
        # Validate: SL-A cannot exceed SL-C
        if sl_c is not None and sl_a is not None:
            if sl_a > sl_c:
                logger.warning(f"Zone {zone.id}: SL-A ({sl_a}) > SL-C ({sl_c}), capping SL-A to SL-C")
                sl_a = sl_c
            # Also validate: SL-C cannot exceed SL-T
            if sl_c > zone.security_level_target:
                logger.warning(f"Zone {zone.id}: SL-C ({sl_c}) > SL-T ({zone.security_level_target}), capping SL-C to SL-T")
                sl_c = min(sl_c, zone.security_level_target)
                # Re-cap SL-A if needed
                if sl_a > sl_c:
                    sl_a = sl_c
        
        zone.security_level_achieved = sl_a
        
        # Calculate compliance status
        compliance_status = ISA62443ComplianceEngine.calculate_zone_compliance_status(db, zone)
        zone.compliance_status = compliance_status
        
        zone.last_assessment_date = datetime.utcnow()
        
        db.commit()
        db.refresh(zone)
        
        return zone
    
    @staticmethod
    def get_compliance_gap_analysis(
        db: Session,
        zone_id: str
    ) -> Dict:
        """
        Get gap analysis for a zone (SL-T vs SL-A, missing requirements, etc.)
        """
        zone = db.query(SecurityZone).filter(SecurityZone.id == zone_id).first()
        if not zone:
            raise ValueError(f"Zone {zone_id} not found")
        
        sl_t = zone.security_level_target
        sl_a = zone.security_level_achieved or ISA62443ComplianceEngine.calculate_zone_security_level_achieved(db, zone)
        
        gap = (sl_t - sl_a) if (sl_t and sl_a) else None
        
        # Requirements applicable to zone for this SL-T (for missing list)
        all_requirements = []
        if sl_t:
            all_requirements = (
                db.query(SecurityRequirement)
                .filter(
                    SecurityRequirement.applies_to_zones == True,
                    SecurityRequirement.min_security_level <= sl_t
                )
                .all()
            )
        
        non_compliant_list = []
        assessed_requirement_ids = set()
        zone_assessments = []
        
        try:
            zone_assessments = (
                db.query(SRAssessment)
                .filter(
                    SRAssessment.object_type == 'zone',
                    SRAssessment.object_id == zone.id,
                    SRAssessment.tenant_id == zone.tenant_id
                )
                .all()
            )
            if zone_assessments:
                for a in zone_assessments:
                    assessed_requirement_ids.add(a.sr_id)
                    if a.status in ('non_compliant', 'partial'):
                        sr = db.query(SecurityRequirement).filter(SecurityRequirement.id == a.sr_id).first()
                        if sr:
                            non_compliant_list.append({
                                'requirement_id': sr.requirement_id,
                                'title': sr.title,
                                'status': a.status
                            })
        except Exception as e:
            logger.debug(f"SRAssessment not available for gap analysis, using legacy: {e}")
        
        if not zone_assessments:
            # Fallback: SecurityRequirementCompliance (legacy)
            compliance_records = (
                db.query(SecurityRequirementCompliance)
                .filter(
                    SecurityRequirementCompliance.zone_id == zone.id,
                    SecurityRequirementCompliance.tenant_id == zone.tenant_id
                )
                .all()
            )
            non_compliant_list = [
                {
                    'requirement_id': record.requirement.requirement_id,
                    'title': record.requirement.title,
                    'status': record.compliance_status
                }
                for record in compliance_records
                if record.compliance_status in ('non_compliant', 'partial')
            ]
            assessed_requirement_ids = {record.requirement_id for record in compliance_records}
        
        missing_requirements = [req for req in all_requirements if req.id not in assessed_requirement_ids]
        
        return {
            'zone_id': str(zone.id),
            'zone_name': zone.name,
            'security_level_target': sl_t,
            'security_level_achieved': sl_a,
            'gap': gap,
            'compliance_status': zone.compliance_status,
            'non_compliant_count': len(non_compliant_list),
            'non_compliant_requirements': non_compliant_list,
            'missing_requirements_count': len(missing_requirements),
            'missing_requirements': [
                {'requirement_id': req.requirement_id, 'title': req.title}
                for req in missing_requirements
            ]
        }

