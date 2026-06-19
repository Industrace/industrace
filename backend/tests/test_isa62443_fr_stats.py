"""Tests for FR summary stats (IEC 62443)."""
import uuid
from types import SimpleNamespace

from app.services.isa62443_assessment_utils import compute_fr_summary_stats


def _sr(req_id: str, min_sl: int = 1):
    return SimpleNamespace(
        id=uuid.uuid4(),
        requirement_id=req_id,
        min_security_level=min_sl,
        max_security_level=4,
    )


def test_fr_stats_excludes_na_from_denominator():
    r1, r2 = _sr("SR 1.1"), _sr("SR 1.2")
    compliance = {r1.id: "compliant", r2.id: "not_applicable"}
    stats = compute_fr_summary_stats([r1, r2], compliance, target_sl=2)
    assert stats["in_scope_count"] == 1
    assert stats["compliance_percentage"] == 100.0
    assert stats["not_applicable_count"] == 1


def test_fr_stats_not_assessed_in_scope():
    r1, r2 = _sr("SR 1.1"), _sr("SR 1.2")
    compliance = {r1.id: "compliant"}
    stats = compute_fr_summary_stats([r1, r2], compliance, target_sl=2)
    assert stats["in_scope_count"] == 2
    assert stats["not_assessed_count"] == 1
    assert stats["compliance_percentage"] == 50.0
