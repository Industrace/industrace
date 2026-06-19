"""Integration tests: RE assessments → zone SL-A recalculation (SQLite)."""
import uuid

from app.models import SecurityZone
from app.routers.compliance import _save_sr_assessment
from app.services.isa62443_audit_export import audit_export_to_csv, build_zone_audit_export
from app.services.isa62443_compliance_engine import ISA62443ComplianceEngine


def _recalc_zone_sla_only(db_session, zone: SecurityZone) -> SecurityZone:
    """SL-A + compliance_status without SL-C (no assets tables in SQLite fixture)."""
    zone.security_level_achieved = (
        ISA62443ComplianceEngine.calculate_zone_security_level_achieved(db_session, zone)
    )
    zone.compliance_status = ISA62443ComplianceEngine.calculate_zone_compliance_status(
        db_session, zone
    )
    db_session.commit()
    db_session.refresh(zone)
    return zone


def test_re_assessments_raise_zone_sl_a(db_session, tenant, zone, sr_min_sl_1):
    user_id = uuid.uuid4()
    _save_sr_assessment(
        db_session,
        tenant.id,
        user_id,
        sr_min_sl_1.id,
        "zone",
        zone.id,
        {
            "re_assessments": [
                {"enhancement_level": 1, "status": "compliant"},
                {"enhancement_level": 2, "status": "compliant"},
            ],
        },
    )

    updated = _recalc_zone_sla_only(db_session, zone)
    assert updated.security_level_achieved == 2
    assert updated.compliance_status == "compliant"


def test_partial_re_blocks_sl_2(db_session, tenant, zone, sr_min_sl_1):
    user_id = uuid.uuid4()
    _save_sr_assessment(
        db_session,
        tenant.id,
        user_id,
        sr_min_sl_1.id,
        "zone",
        zone.id,
        {
            "re_assessments": [
                {"enhancement_level": 1, "status": "compliant"},
                {"enhancement_level": 2, "status": "partial", "justification": "Gap"},
            ],
        },
    )
    updated = _recalc_zone_sla_only(db_session, zone)
    assert updated.security_level_achieved == 1


def test_audit_export_includes_re_rows(db_session, tenant, zone, sr_min_sl_1):
    user_id = uuid.uuid4()
    _save_sr_assessment(
        db_session,
        tenant.id,
        user_id,
        sr_min_sl_1.id,
        "zone",
        zone.id,
        {
            "re_assessments": [
                {"enhancement_level": 1, "status": "compliant"},
                {"enhancement_level": 2, "status": "non_compliant", "justification": "NC"},
            ],
        },
    )
    db_session.refresh(zone)
    zone.security_level_achieved = (
        ISA62443ComplianceEngine.calculate_zone_security_level_achieved(db_session, zone)
    )

    payload = build_zone_audit_export(db_session, zone)
    assert payload["zone"]["id"] == str(zone.id)
    assert payload["summary"]["total_rows"] >= 4
    in_scope = [
        r
        for r in payload["rows"]
        if r["requirement_id"] == "SR 9.9" and r["in_scope_for_sl_t"]
    ]
    assert len(in_scope) == 2
    assert {r["enhancement_level"] for r in in_scope} == {1, 2}
    statuses = {r["enhancement_level"]: r["assessment_status"] for r in in_scope}
    assert statuses[1] == "compliant"
    assert statuses[2] == "non_compliant"

    csv_text = audit_export_to_csv(payload)
    assert "SR 9.9" in csv_text
    assert "enhancement_level" in csv_text.splitlines()[0]
