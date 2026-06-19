# backend/app/services/isa62443_audit_export.py
"""
IEC 62443 zone audit matrix: zone × SR × RE × assessment status.
"""
import csv
import io
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import SecurityRequirement, SecurityZone, SRAssessment
from app.models.requirement_enhancement import RequirementEnhancement
from app.services.isa62443_assessment_utils import (
    parse_assessment_records,
    re_status_for_level,
    requirement_applies_at_sl,
)


def _status_bucket(status: Optional[str]) -> str:
    if status is None:
        return "not_assessed"
    if status == "not_applicable":
        return "not_applicable"
    if status in ("non_compliant", "partial", "insufficient_info"):
        return "non_compliant"
    if status == "compliant":
        return "compliant"
    return "not_assessed"


def build_zone_audit_export(
    db: Session,
    zone: SecurityZone,
) -> Dict[str, Any]:
    """Build audit matrix rows for one security zone."""
    sl_t = zone.security_level_target
    requirements = (
        db.query(SecurityRequirement)
        .filter(SecurityRequirement.applies_to_zones == True)
        .order_by(SecurityRequirement.requirement_id)
        .all()
    )
    sr_ids = [r.id for r in requirements]

    enhancements_by_sr: Dict[Any, List[RequirementEnhancement]] = {}
    if sr_ids:
        enhancements = (
            db.query(RequirementEnhancement)
            .filter(RequirementEnhancement.security_requirement_id.in_(sr_ids))
            .order_by(RequirementEnhancement.enhancement_level)
            .all()
        )
        for re in enhancements:
            enhancements_by_sr.setdefault(re.security_requirement_id, []).append(re)

    assessments = (
        db.query(SRAssessment)
        .filter(
            SRAssessment.object_type == "zone",
            SRAssessment.object_id == zone.id,
            SRAssessment.tenant_id == zone.tenant_id,
        )
        .all()
    )
    legacy, by_re = parse_assessment_records(assessments)

    rows: List[Dict[str, Any]] = []
    buckets = {
        "compliant": 0,
        "non_compliant": 0,
        "not_applicable": 0,
        "not_assessed": 0,
    }

    for req in requirements:
        re_list = enhancements_by_sr.get(req.id, [])
        if not re_list:
            for level in range(1, 5):
                re_list.append(
                    type(
                        "RE",
                        (),
                        {
                            "enhancement_level": level,
                            "title": f"{req.requirement_id} — RE {level}",
                            "description": None,
                        },
                    )()
                )

        for re in re_list:
            level = re.enhancement_level
            in_scope = bool(
                sl_t
                and level <= sl_t
                and requirement_applies_at_sl(req, level)
            )
            status = (
                re_status_for_level(req.id, level, legacy, by_re) if in_scope else None
            )
            bucket = _status_bucket(status) if in_scope else "out_of_scope"
            if in_scope and bucket in buckets:
                buckets[bucket] += 1

            rows.append(
                {
                    "zone_id": str(zone.id),
                    "zone_name": zone.name,
                    "security_level_target": sl_t,
                    "security_level_achieved": zone.security_level_achieved,
                    "sr_id": str(req.id),
                    "requirement_id": req.requirement_id,
                    "sr_title": req.title,
                    "enhancement_level": level,
                    "re_title": getattr(re, "title", None),
                    "re_description": getattr(re, "description", None),
                    "in_scope_for_sl_t": in_scope,
                    "assessment_status": status,
                    "status_bucket": bucket,
                }
            )

    return {
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "standard_version": "62443-3-3:2013",
        "zone": {
            "id": str(zone.id),
            "name": zone.name,
            "security_level_target": sl_t,
            "security_level_achieved": zone.security_level_achieved,
            "security_level_capability": zone.security_level_capability,
            "compliance_status": zone.compliance_status,
        },
        "summary": {
            "total_rows": len(rows),
            "in_scope_rows": sum(1 for r in rows if r["in_scope_for_sl_t"]),
            **buckets,
        },
        "rows": rows,
    }


def audit_export_to_csv(payload: Dict[str, Any]) -> str:
    """Serialize audit export payload to CSV text."""
    rows = payload.get("rows") or []
    if not rows:
        return ""

    fieldnames = [
        "zone_id",
        "zone_name",
        "security_level_target",
        "security_level_achieved",
        "requirement_id",
        "sr_title",
        "enhancement_level",
        "re_title",
        "in_scope_for_sl_t",
        "assessment_status",
        "status_bucket",
        "re_description",
    ]
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buffer.getvalue()
