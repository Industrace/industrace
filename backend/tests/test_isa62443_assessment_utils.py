"""Unit tests for IEC 62443 assessment helpers."""
import uuid
from types import SimpleNamespace

from app.services.isa62443_assessment_utils import (
    assessment_coverage_ratio,
    derive_compliance_status,
    highest_achieved_sl,
    sl_level_fully_satisfied,
    sl_level_fully_satisfied_re,
)


def _req(min_sl: int, req_id: str = "SR 1.1"):
    return SimpleNamespace(
        id=uuid.uuid4(),
        requirement_id=req_id,
        min_security_level=min_sl,
        max_security_level=4,
    )


def test_not_applicable_excluded_from_sl():
    r1 = _req(1)
    compliance = {r1.id: "not_applicable"}
    assert sl_level_fully_satisfied([r1], compliance) is True
    assert highest_achieved_sl(2, [r1], compliance) == 2


def test_insufficient_info_blocks_sl():
    r1 = _req(1)
    compliance = {r1.id: "insufficient_info"}
    assert sl_level_fully_satisfied([r1], compliance) is False
    assert highest_achieved_sl(2, [r1], compliance) is None


def test_compliant_achieves_sl():
    r1 = _req(1)
    r2 = _req(2)
    compliance = {r1.id: "compliant", r2.id: "compliant"}
    assert highest_achieved_sl(2, [r1, r2], compliance) == 2


def test_partial_blocks_higher_sl():
    r1 = _req(1)
    r2 = _req(2)
    compliance = {r1.id: "compliant", r2.id: "partial"}
    assert highest_achieved_sl(2, [r1, r2], compliance) == 1


def test_derive_compliance_from_sl_gap():
    assert derive_compliance_status(3, 3, 1.0, True) == "compliant"
    assert derive_compliance_status(3, 2, 1.0, True) == "partial"
    assert derive_compliance_status(3, None, 0.5, True) == "non_compliant"
    assert derive_compliance_status(3, None, 0.0, False) == "not_assessed"


def test_coverage_excludes_na():
    r1 = _req(1)
    r2 = _req(1, "SR 1.2")
    compliance = {r1.id: "compliant", r2.id: "not_applicable"}
    assert assessment_coverage_ratio([r1, r2], compliance) == 1.0


def test_re_level_blocks_sl_when_re2_missing():
    r1 = _req(1)
    by_re = {(r1.id, 1): "compliant"}
    assert sl_level_fully_satisfied_re(2, [r1], {}, by_re) is False
    by_re[(r1.id, 2)] = "compliant"
    assert sl_level_fully_satisfied_re(2, [r1], {}, by_re) is True


def test_highest_achieved_sl_from_re():
    r1 = _req(1)
    r2 = _req(2)
    by_re = {
        (r1.id, 1): "compliant",
        (r1.id, 2): "compliant",
        (r2.id, 1): "compliant",
        (r2.id, 2): "partial",
    }
    assert highest_achieved_sl(2, [r1, r2], {}, by_re=by_re) == 1


def test_legacy_sr_assessment_used_when_no_re_rows():
    r1 = _req(1)
    legacy = {r1.id: "compliant"}
    assert highest_achieved_sl(1, [r1], legacy) == 1
