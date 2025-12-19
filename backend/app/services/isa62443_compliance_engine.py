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
    AssetZoneMembership
)
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
        
        Logic:
        1. Get all compliance records for the zone
        2. For each Security Requirement applicable to the zone's target SL
        3. Calculate compliance percentage
        4. SL-A is the highest SL where all requirements are met
        
        Returns: SL-A (1-4) or None if not calculable
        """
        if not zone.security_level_target:
            return None
        
        target_sl = zone.security_level_target
        
        # Get all requirements applicable to zones for the target SL
        requirements = (
            db.query(SecurityRequirement)
            .filter(
                SecurityRequirement.applies_to_zones == True,
                SecurityRequirement.min_security_level <= target_sl,
                or_(
                    SecurityRequirement.max_security_level.is_(None),
                    SecurityRequirement.max_security_level >= target_sl
                )
            )
            .all()
        )
        
        if not requirements:
            return None
        
        # Get compliance records for this zone
        compliance_records = (
            db.query(SecurityRequirementCompliance)
            .filter(
                SecurityRequirementCompliance.zone_id == zone.id,
                SecurityRequirementCompliance.tenant_id == zone.tenant_id
            )
            .all()
        )
        
        # Create compliance map
        compliance_map = {
            record.requirement_id: record
            for record in compliance_records
        }
        
        # Calculate compliance for each Security Level (1 to target_sl)
        sl_compliance = {}
        
        for sl in range(1, target_sl + 1):
            # Get requirements for this SL
            sl_requirements = [
                req for req in requirements
                if req.min_security_level <= sl and (
                    req.max_security_level is None or req.max_security_level >= sl
                )
            ]
            
            if not sl_requirements:
                continue
            
            # Check compliance for each requirement
            compliant_count = 0
            total_count = len(sl_requirements)
            
            for req in sl_requirements:
                compliance = compliance_map.get(req.id)
                if compliance:
                    if compliance.compliance_status == 'compliant':
                        compliant_count += 1
                    elif compliance.compliance_status == 'partial':
                        # Count partial as 0.5
                        compliant_count += 0.5
                else:
                    # Not assessed = not compliant
                    pass
            
            compliance_percentage = (compliant_count / total_count) * 100 if total_count > 0 else 0
            sl_compliance[sl] = compliance_percentage
        
        # SL-A is the highest SL where compliance >= 80%
        achieved_sl = None
        for sl in range(target_sl, 0, -1):
            if sl in sl_compliance and sl_compliance[sl] >= 80.0:
                achieved_sl = sl
                break
        
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
        
        # Calculate compliance
        compliant_count = 0
        total_count = len(requirements)
        
        for req in requirements:
            compliance = compliance_map.get(req.id)
            if compliance and compliance.compliance_status == 'compliant':
                compliant_count += 1
        
        compliance_percentage = (compliant_count / total_count) * 100 if total_count > 0 else 0
        
        # SL-A based on compliance percentage
        if compliance_percentage >= 80:
            return target_sl
        elif compliance_percentage >= 60:
            return max(1, target_sl - 1)
        elif compliance_percentage >= 40:
            return max(1, target_sl - 2)
        else:
            return 1
    
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
        
        if compliance_records:
            compliant_count = sum(
                1 for record in compliance_records
                if record.compliance_status == 'compliant'
            )
            total_count = len(compliance_records)
            
            if total_count > 0:
                compliance_percentage = (compliant_count / total_count) * 100
                if compliance_percentage >= 80:
                    sl_a = target_sl
                elif compliance_percentage >= 60:
                    sl_a = max(1, target_sl - 1)
        
        return min(sl_a, target_sl)
    
    @staticmethod
    def calculate_zone_compliance_status(
        db: Session,
        zone: SecurityZone
    ) -> str:
        """
        Calculate overall compliance status for a zone.
        Returns: 'compliant', 'non_compliant', 'partial', 'not_assessed'
        """
        # Get all compliance records for the zone
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
        
        compliant_count = sum(
            1 for record in compliance_records
            if record.compliance_status == 'compliant'
        )
        partial_count = sum(
            1 for record in compliance_records
            if record.compliance_status == 'partial'
        )
        non_compliant_count = sum(
            1 for record in compliance_records
            if record.compliance_status == 'non_compliant'
        )
        total_count = len(compliance_records)
        
        if total_count == 0:
            return 'not_assessed'
        
        compliance_percentage = (compliant_count / total_count) * 100
        
        if compliance_percentage >= 80:
            return 'compliant'
        elif compliance_percentage >= 50 or partial_count > 0:
            return 'partial'
        else:
            return 'non_compliant'
    
    @staticmethod
    def update_zone_security_levels(
        db: Session,
        zone_id: str
    ) -> SecurityZone:
        """
        Recalculate and update SL-A and compliance status for a zone.
        """
        zone = db.query(SecurityZone).filter(SecurityZone.id == zone_id).first()
        if not zone:
            raise ValueError(f"Zone {zone_id} not found")
        
        # Calculate SL-A
        sl_a = ISA62443ComplianceEngine.calculate_zone_security_level_achieved(db, zone)
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
        
        # Get non-compliant requirements
        compliance_records = (
            db.query(SecurityRequirementCompliance)
            .filter(
                SecurityRequirementCompliance.zone_id == zone.id,
                SecurityRequirementCompliance.tenant_id == zone.tenant_id
            )
            .all()
        )
        
        non_compliant = [
            record for record in compliance_records
            if record.compliance_status in ['non_compliant', 'partial']
        ]
        
        # Get missing requirements (not assessed)
        if sl_t:
            all_requirements = (
                db.query(SecurityRequirement)
                .filter(
                    SecurityRequirement.applies_to_zones == True,
                    SecurityRequirement.min_security_level <= sl_t
                )
                .all()
            )
            
            assessed_requirement_ids = {record.requirement_id for record in compliance_records}
            missing_requirements = [
                req for req in all_requirements
                if req.id not in assessed_requirement_ids
            ]
        else:
            missing_requirements = []
        
        return {
            'zone_id': str(zone.id),
            'zone_name': zone.name,
            'security_level_target': sl_t,
            'security_level_achieved': sl_a,
            'gap': gap,
            'compliance_status': zone.compliance_status,
            'non_compliant_count': len(non_compliant),
            'non_compliant_requirements': [
                {
                    'requirement_id': record.requirement.requirement_id,
                    'title': record.requirement.title,
                    'status': record.compliance_status
                }
                for record in non_compliant
            ],
            'missing_requirements_count': len(missing_requirements),
            'missing_requirements': [
                {
                    'requirement_id': req.requirement_id,
                    'title': req.title
                }
                for req in missing_requirements
            ]
        }

