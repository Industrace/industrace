# backend/app/services/isa62443_compliance_engine.py
import uuid
from typing import Dict, List, Optional, Union
from datetime import datetime
from sqlalchemy.orm import Session

UuidLike = Union[str, uuid.UUID]

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
from app.services.isa62443_assessment_utils import (
    applicable_requirements_for_target,
    assessment_coverage_ratio,
    build_sr_compliance_map,
    derive_compliance_status,
    extract_assessment_status,
    filter_requirements_for_sl,
    highest_achieved_sl,
    parse_assessment_records,
)
import logging

logger = logging.getLogger(__name__)


def _coerce_uuid(value: UuidLike) -> uuid.UUID:
    if isinstance(value, uuid.UUID):
        return value
    return uuid.UUID(str(value))


class ISA62443ComplianceEngine:
    """Engine for calculating ISA/IEC 62443 compliance and Security Levels"""

    @staticmethod
    def _zone_assessments(db: Session, zone: SecurityZone) -> List[SRAssessment]:
        return (
            db.query(SRAssessment)
            .filter(
                SRAssessment.object_type == "zone",
                SRAssessment.object_id == zone.id,
                SRAssessment.tenant_id == zone.tenant_id,
            )
            .all()
        )

    @staticmethod
    def _compliance_map_from_assessments(
        assessments: List[SRAssessment],
        requirements: List[SecurityRequirement],
        target_sl: Optional[int],
    ) -> dict:
        legacy, by_re = parse_assessment_records(assessments)
        if by_re and target_sl:
            return build_sr_compliance_map(requirements, target_sl, legacy, by_re)
        return legacy

    @staticmethod
    def _zone_compliance_map(db: Session, zone: SecurityZone) -> dict:
        try:
            zone_assessments = ISA62443ComplianceEngine._zone_assessments(db, zone)
            if zone_assessments:
                requirements = ISA62443ComplianceEngine._zone_requirements(db)
                return ISA62443ComplianceEngine._compliance_map_from_assessments(
                    zone_assessments,
                    requirements,
                    zone.security_level_target,
                )
        except Exception as e:
            logger.debug(f"SRAssessment not available for zone, using legacy: {e}")

        compliance_records = (
            db.query(SecurityRequirementCompliance)
            .filter(
                SecurityRequirementCompliance.zone_id == zone.id,
                SecurityRequirementCompliance.tenant_id == zone.tenant_id,
            )
            .all()
        )
        return {record.requirement_id: record for record in compliance_records}

    @staticmethod
    def _zone_requirements(db: Session) -> List[SecurityRequirement]:
        return (
            db.query(SecurityRequirement)
            .filter(SecurityRequirement.applies_to_zones == True)
            .all()
        )

    @staticmethod
    def calculate_zone_security_level_achieved(
        db: Session,
        zone: SecurityZone,
    ) -> Optional[int]:
        """
        SL-A: highest SL (1..SL-T) where all in-scope SRs are compliant.
        not_applicable SRs are excluded; unassessed / partial / insufficient_info block.
        """
        if not zone.security_level_target:
            return None

        all_requirements = ISA62443ComplianceEngine._zone_requirements(db)
        if not all_requirements:
            return None

        zone_assessments = ISA62443ComplianceEngine._zone_assessments(db, zone)
        legacy, by_re = parse_assessment_records(zone_assessments)
        if by_re:
            return highest_achieved_sl(
                zone.security_level_target,
                all_requirements,
                {},
                legacy=legacy,
                by_re=by_re,
            )
        compliance_map = legacy or ISA62443ComplianceEngine._zone_compliance_map(db, zone)
        return highest_achieved_sl(
            zone.security_level_target,
            all_requirements,
            compliance_map,
        )

    @staticmethod
    def calculate_asset_security_level_achieved(
        db: Session,
        asset: Asset,
    ) -> Optional[int]:
        if asset.security_level_achieved is not None:
            return asset.security_level_achieved

        memberships = (
            db.query(AssetZoneMembership)
            .filter(
                AssetZoneMembership.asset_id == asset.id,
                AssetZoneMembership.tenant_id == asset.tenant_id,
                AssetZoneMembership.deleted_at.is_(None),
            )
            .all()
        )

        if memberships:
            zone_sl_as = []
            for membership in memberships:
                zone = (
                    db.query(SecurityZone)
                    .filter(SecurityZone.id == membership.security_zone_id)
                    .first()
                )
                if zone:
                    zone_sl_a = ISA62443ComplianceEngine.calculate_zone_security_level_achieved(
                        db, zone
                    )
                    if zone_sl_a:
                        target_sl = membership.sl_target or zone.security_level_target
                        if target_sl:
                            zone_sl_as.append(min(zone_sl_a, target_sl))
                        else:
                            zone_sl_as.append(zone_sl_a)
            if zone_sl_as:
                return min(zone_sl_as)

        if asset.security_zone_id:
            zone = (
                db.query(SecurityZone)
                .filter(SecurityZone.id == asset.security_zone_id)
                .first()
            )
            if zone:
                zone_sl_a = ISA62443ComplianceEngine.calculate_zone_security_level_achieved(
                    db, zone
                )
                if zone_sl_a:
                    return zone_sl_a

        target_sl = asset.security_level_target
        if not target_sl:
            return None

        requirements = (
            db.query(SecurityRequirement)
            .filter(
                SecurityRequirement.applies_to_assets == True,
            )
            .all()
        )
        if not requirements:
            return None

        compliance_map = ISA62443ComplianceEngine._asset_compliance_map(db, asset)
        if not compliance_map:
            compliance_records = (
                db.query(SecurityRequirementCompliance)
                .filter(
                    SecurityRequirementCompliance.asset_id == asset.id,
                    SecurityRequirementCompliance.tenant_id == asset.tenant_id,
                )
                .all()
            )
            compliance_map = {
                record.requirement_id: record for record in compliance_records
            }
        if not compliance_map:
            return None
        assessments = ISA62443ComplianceEngine._asset_assessments(db, asset)
        _, by_re = parse_assessment_records(assessments)
        if by_re:
            legacy, _ = parse_assessment_records(assessments)
            return highest_achieved_sl(
                target_sl, requirements, {}, legacy=legacy, by_re=by_re
            )
        return highest_achieved_sl(target_sl, requirements, compliance_map)

    @staticmethod
    def _asset_assessments(db: Session, asset: Asset) -> List[SRAssessment]:
        return (
            db.query(SRAssessment)
            .filter(
                SRAssessment.object_type == "asset",
                SRAssessment.object_id == asset.id,
                SRAssessment.tenant_id == asset.tenant_id,
            )
            .all()
        )

    @staticmethod
    def _asset_compliance_map(db: Session, asset: Asset) -> dict:
        try:
            assessments = ISA62443ComplianceEngine._asset_assessments(db, asset)
            if assessments:
                requirements = (
                    db.query(SecurityRequirement)
                    .filter(SecurityRequirement.applies_to_assets == True)
                    .all()
                )
                return ISA62443ComplianceEngine._compliance_map_from_assessments(
                    assessments,
                    requirements,
                    asset.security_level_target,
                )
        except Exception as e:
            logger.debug(f"SRAssessment not available for asset: {e}")
        return {}

    @staticmethod
    def update_asset_iec62443_levels(db: Session, asset_id: UuidLike) -> Asset:
        asset = db.query(Asset).filter(Asset.id == _coerce_uuid(asset_id)).first()
        if not asset:
            raise ValueError(f"Asset {asset_id} not found")

        sl_a = ISA62443ComplianceEngine.calculate_asset_security_level_achieved(db, asset)
        asset.security_level_achieved = sl_a

        target_sl = asset.security_level_target
        requirements = (
            db.query(SecurityRequirement)
            .filter(SecurityRequirement.applies_to_assets == True)
            .all()
        )
        compliance_map = ISA62443ComplianceEngine._asset_compliance_map(db, asset)
        if not compliance_map and requirements:
            records = (
                db.query(SecurityRequirementCompliance)
                .filter(
                    SecurityRequirementCompliance.asset_id == asset.id,
                    SecurityRequirementCompliance.tenant_id == asset.tenant_id,
                )
                .all()
            )
            compliance_map = {r.requirement_id: r for r in records}

        applicable = (
            applicable_requirements_for_target(requirements, target_sl)
            if target_sl
            else []
        )
        coverage = assessment_coverage_ratio(applicable, compliance_map) if applicable else 0.0
        asset.isa62443_compliance_status = derive_compliance_status(
            target_sl,
            sl_a,
            coverage,
            len(compliance_map) > 0,
        )
        asset.isa62443_last_assessment = datetime.utcnow()
        db.commit()
        db.refresh(asset)
        return asset

    @staticmethod
    def _estimate_conduit_sl_from_properties(conduit: Conduit) -> Optional[int]:
        """Preliminary estimate only — not normative SL-A."""
        sl_a = 1
        if conduit.is_encrypted:
            if conduit.encryption_type in ["tls", "ipsec"]:
                sl_a = max(sl_a, 2)
        if conduit.authentication_required:
            if conduit.authentication_method == "certificate":
                sl_a = max(sl_a, 3)
            elif conduit.authentication_method in ["psk", "username_password"]:
                sl_a = max(sl_a, 2)
        return sl_a

    @staticmethod
    def _conduit_assessments(db: Session, conduit: Conduit) -> List[SRAssessment]:
        return (
            db.query(SRAssessment)
            .filter(
                SRAssessment.object_type == "conduit",
                SRAssessment.object_id == conduit.id,
                SRAssessment.tenant_id == conduit.tenant_id,
            )
            .all()
        )

    @staticmethod
    def _conduit_compliance_map(db: Session, conduit: Conduit) -> dict:
        try:
            assessments = ISA62443ComplianceEngine._conduit_assessments(db, conduit)
            if assessments:
                requirements = (
                    db.query(SecurityRequirement)
                    .filter(SecurityRequirement.applies_to_conduits == True)
                    .all()
                )
                return ISA62443ComplianceEngine._compliance_map_from_assessments(
                    assessments,
                    requirements,
                    conduit.security_level_target,
                )
        except Exception as e:
            logger.debug(f"SRAssessment not available for conduit: {e}")

        compliance_records = (
            db.query(SecurityRequirementCompliance)
            .filter(
                SecurityRequirementCompliance.conduit_id == conduit.id,
                SecurityRequirementCompliance.tenant_id == conduit.tenant_id,
            )
            .all()
        )
        if compliance_records:
            return {record.requirement_id: record for record in compliance_records}
        return {}

    @staticmethod
    def get_conduit_sl_metadata(db: Session, conduit: Conduit) -> dict:
        """Returns SL-A and source: assessment | preliminary | none."""
        target_sl = conduit.security_level_target
        if not target_sl:
            return {"security_level_achieved": None, "sl_achieved_source": "none"}

        conduit_requirements = (
            db.query(SecurityRequirement)
            .filter(SecurityRequirement.applies_to_conduits == True)
            .all()
        )
        assessments = ISA62443ComplianceEngine._conduit_assessments(db, conduit)
        legacy, by_re = parse_assessment_records(assessments)
        compliance_map = ISA62443ComplianceEngine._conduit_compliance_map(db, conduit)
        if compliance_map and conduit_requirements:
            if by_re:
                achieved = highest_achieved_sl(
                    target_sl,
                    conduit_requirements,
                    {},
                    legacy=legacy,
                    by_re=by_re,
                )
            else:
                achieved = highest_achieved_sl(
                    target_sl, conduit_requirements, compliance_map
                )
            return {
                "security_level_achieved": achieved,
                "sl_achieved_source": "assessment",
            }

        if compliance_map:
            return {"security_level_achieved": None, "sl_achieved_source": "assessment"}

        preliminary = ISA62443ComplianceEngine._estimate_conduit_sl_from_properties(conduit)
        sl_a = min(preliminary, target_sl) if preliminary else None
        return {
            "security_level_achieved": sl_a,
            "sl_achieved_source": "preliminary" if sl_a is not None else "none",
        }

    @staticmethod
    def calculate_conduit_security_level_achieved(
        db: Session,
        conduit: Conduit,
    ) -> Optional[int]:
        return ISA62443ComplianceEngine.get_conduit_sl_metadata(db, conduit)[
            "security_level_achieved"
        ]

    @staticmethod
    def update_conduit_iec62443_levels(db: Session, conduit_id: UuidLike) -> Conduit:
        conduit = db.query(Conduit).filter(Conduit.id == _coerce_uuid(conduit_id)).first()
        if not conduit:
            raise ValueError(f"Conduit {conduit_id} not found")

        meta = ISA62443ComplianceEngine.get_conduit_sl_metadata(db, conduit)
        conduit.security_level_achieved = meta["security_level_achieved"]

        target_sl = conduit.security_level_target
        requirements = (
            db.query(SecurityRequirement)
            .filter(SecurityRequirement.applies_to_conduits == True)
            .all()
        )
        compliance_map = ISA62443ComplianceEngine._conduit_compliance_map(db, conduit)
        applicable = (
            applicable_requirements_for_target(requirements, target_sl)
            if target_sl
            else []
        )
        coverage = assessment_coverage_ratio(applicable, compliance_map) if applicable else 0.0
        conduit.compliance_status = derive_compliance_status(
            target_sl,
            conduit.security_level_achieved,
            coverage,
            len(compliance_map) > 0,
        )
        conduit.last_assessment_date = datetime.utcnow()
        db.commit()
        db.refresh(conduit)
        return conduit

    @staticmethod
    def calculate_zone_compliance_status(
        db: Session,
        zone: SecurityZone,
    ) -> str:
        if not zone.security_level_target:
            return "not_assessed"

        all_requirements = ISA62443ComplianceEngine._zone_requirements(db)
        applicable = applicable_requirements_for_target(
            all_requirements, zone.security_level_target
        )
        compliance_map = ISA62443ComplianceEngine._zone_compliance_map(db, zone)
        has_any = len(compliance_map) > 0
        coverage = assessment_coverage_ratio(applicable, compliance_map)
        sl_a = ISA62443ComplianceEngine.calculate_zone_security_level_achieved(db, zone)

        return derive_compliance_status(
            zone.security_level_target,
            sl_a,
            coverage,
            has_any,
        )

    @staticmethod
    def calculate_zone_security_level_capability(
        db: Session,
        zone: SecurityZone,
    ) -> Optional[int]:
        if not zone.security_level_target:
            return None

        target_sl = zone.security_level_target
        all_requirements = ISA62443ComplianceEngine._zone_requirements(db)
        if not all_requirements:
            return None

        zone_assets = (
            db.query(Asset)
            .join(AssetZoneMembership, Asset.id == AssetZoneMembership.asset_id)
            .filter(
                AssetZoneMembership.security_zone_id == zone.id,
                AssetZoneMembership.tenant_id == zone.tenant_id,
                AssetZoneMembership.deleted_at.is_(None),
                Asset.deleted_at.is_(None),
            )
            .all()
        )

        if not zone_assets:
            legacy_assets = (
                db.query(Asset)
                .filter(
                    Asset.security_zone_id == zone.id,
                    Asset.deleted_at.is_(None),
                )
                .all()
            )
            if not legacy_assets:
                return None
            zone_assets = legacy_assets

        asset_ids = [asset.id for asset in zone_assets]
        asset_capabilities = (
            db.query(AssetCapability)
            .filter(
                AssetCapability.asset_id.in_(asset_ids),
                AssetCapability.tenant_id == zone.tenant_id,
            )
            .all()
        )

        available_capabilities = set()
        for ac in asset_capabilities:
            if ac.support_level == "supported":
                available_capabilities.add(ac.capability_id)

        achieved_sl_c = None
        for sl in range(target_sl, 0, -1):
            sl_requirements = filter_requirements_for_sl(all_requirements, sl)
            if not sl_requirements:
                continue

            requirement_ids = [req.id for req in sl_requirements]
            required_capabilities = (
                db.query(SRCapability)
                .filter(SRCapability.sr_id.in_(requirement_ids))
                .all()
            )

            if not required_capabilities:
                achieved_sl_c = sl
                break

            required_capability_ids = {rc.capability_id for rc in required_capabilities}
            if required_capability_ids.issubset(available_capabilities):
                achieved_sl_c = sl
                logger.debug(
                    f"Zone {zone.id}: SL-C = {sl} (all required capabilities available)"
                )
                break

        return achieved_sl_c

    @staticmethod
    def update_zone_security_levels(
        db: Session,
        zone_id: UuidLike,
    ) -> SecurityZone:
        zone = db.query(SecurityZone).filter(SecurityZone.id == _coerce_uuid(zone_id)).first()
        if not zone:
            raise ValueError(f"Zone {zone_id} not found")

        sl_c = ISA62443ComplianceEngine.calculate_zone_security_level_capability(db, zone)
        zone.security_level_capability = sl_c

        sl_a = ISA62443ComplianceEngine.calculate_zone_security_level_achieved(db, zone)

        if sl_c is not None and sl_a is not None:
            if sl_a > sl_c:
                logger.warning(
                    f"Zone {zone.id}: SL-A ({sl_a}) > SL-C ({sl_c}), capping SL-A to SL-C"
                )
                sl_a = sl_c
            if sl_c > zone.security_level_target:
                logger.warning(
                    f"Zone {zone.id}: SL-C ({sl_c}) > SL-T ({zone.security_level_target}), "
                    "capping SL-C to SL-T"
                )
                sl_c = min(sl_c, zone.security_level_target)
                if sl_a > sl_c:
                    sl_a = sl_c

        zone.security_level_achieved = sl_a
        zone.compliance_status = ISA62443ComplianceEngine.calculate_zone_compliance_status(
            db, zone
        )
        zone.last_assessment_date = datetime.utcnow()

        db.commit()
        db.refresh(zone)
        return zone

    @staticmethod
    def get_compliance_gap_analysis(
        db: Session,
        zone_id: UuidLike,
    ) -> Dict:
        zone = db.query(SecurityZone).filter(SecurityZone.id == _coerce_uuid(zone_id)).first()
        if not zone:
            raise ValueError(f"Zone {zone_id} not found")

        sl_t = zone.security_level_target
        sl_a = zone.security_level_achieved or (
            ISA62443ComplianceEngine.calculate_zone_security_level_achieved(db, zone)
        )
        gap = (sl_t - sl_a) if (sl_t and sl_a is not None) else None

        all_requirements = []
        if sl_t:
            all_requirements = applicable_requirements_for_target(
                ISA62443ComplianceEngine._zone_requirements(db), sl_t
            )

        non_compliant_list = []
        assessed_requirement_ids = set()
        compliance_map = ISA62443ComplianceEngine._zone_compliance_map(db, zone)

        for req in all_requirements:
            val = compliance_map.get(req.id)
            status = extract_assessment_status(val)
            if status is not None:
                assessed_requirement_ids.add(req.id)
            if status in ("non_compliant", "partial", "insufficient_info"):
                non_compliant_list.append(
                    {
                        "requirement_id": req.requirement_id,
                        "title": req.title,
                        "status": status,
                    }
                )

        missing_requirements = [
            req for req in all_requirements if req.id not in assessed_requirement_ids
        ]

        return {
            "zone_id": str(zone.id),
            "zone_name": zone.name,
            "security_level_target": sl_t,
            "security_level_achieved": sl_a,
            "gap": gap,
            "compliance_status": zone.compliance_status,
            "non_compliant_count": len(non_compliant_list),
            "non_compliant_requirements": non_compliant_list,
            "missing_requirements_count": len(missing_requirements),
            "missing_requirements": [
                {"requirement_id": req.requirement_id, "title": req.title}
                for req in missing_requirements
            ],
        }
