# backend/app/services/isa62443_assessment_utils.py
"""
Shared IEC 62443 assessment helpers (SR status, applicability, SL-A rules).
"""
from typing import Any, Dict, List, Optional, Tuple, Union

from app.models.security_requirement import SecurityRequirement

ReLevelKey = Tuple[Any, int]

AssessmentValue = Union[str, Any, None]

ASSESSMENT_STATUSES = frozenset({
    "compliant",
    "non_compliant",
    "partial",
    "not_applicable",
    "insufficient_info",
})


def extract_assessment_status(value: AssessmentValue) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return getattr(value, "compliance_status", None) or getattr(value, "status", None)


def requirement_applies_at_sl(req: SecurityRequirement, sl: int) -> bool:
    if req.min_security_level is None:
        return False
    if req.min_security_level > sl:
        return False
    if req.max_security_level is not None and req.max_security_level < sl:
        return False
    return True


def filter_requirements_for_sl(
    requirements: List[SecurityRequirement],
    sl: int,
) -> List[SecurityRequirement]:
    return [req for req in requirements if requirement_applies_at_sl(req, sl)]


def applicable_requirements_for_target(
    requirements: List[SecurityRequirement],
    target_sl: int,
) -> List[SecurityRequirement]:
    """All SR in scope when assessing against SL-T (cumulative through SL-T)."""
    return filter_requirements_for_sl(requirements, target_sl)


def excludes_from_sl_denominator(status: Optional[str]) -> bool:
    return status == "not_applicable"


def satisfies_sl_level(status: Optional[str]) -> bool:
    return status == "compliant"


def blocks_sl_achievement(status: Optional[str]) -> bool:
    if status is None:
        return True
    if excludes_from_sl_denominator(status):
        return False
    return not satisfies_sl_level(status)


def parse_assessment_records(
    assessments: List[Any],
) -> Tuple[Dict[Any, str], Dict[ReLevelKey, str]]:
    """Split SRAssessment rows into legacy (SR-level) and per-RE maps."""
    legacy: Dict[Any, str] = {}
    by_re: Dict[ReLevelKey, str] = {}
    for row in assessments:
        sr_id = getattr(row, "sr_id", None)
        if sr_id is None:
            continue
        level = getattr(row, "enhancement_level", None)
        status = extract_assessment_status(row)
        if level is None:
            legacy[sr_id] = status
        else:
            by_re[(sr_id, level)] = status
    return legacy, by_re


def sr_has_re_assessments(sr_id: Any, by_re: Dict[ReLevelKey, str]) -> bool:
    return any(key[0] == sr_id for key in by_re)


def re_status_for_level(
    sr_id: Any,
    re_level: int,
    legacy: Dict[Any, str],
    by_re: Dict[ReLevelKey, str],
) -> Optional[str]:
    if (sr_id, re_level) in by_re:
        return by_re[(sr_id, re_level)]
    if sr_id in legacy and not sr_has_re_assessments(sr_id, by_re):
        return legacy[sr_id]
    return None


def aggregate_sr_status_from_re(
    req: SecurityRequirement,
    target_sl: int,
    legacy: Dict[Any, str],
    by_re: Dict[ReLevelKey, str],
) -> Optional[str]:
    """Roll up per-RE statuses to one SR status for FR stats / list views."""
    if sr_id := req.id:
        if sr_id in legacy and not sr_has_re_assessments(sr_id, by_re):
            return legacy[sr_id]

    statuses: List[Optional[str]] = []
    for level in range(1, target_sl + 1):
        if not requirement_applies_at_sl(req, level):
            continue
        statuses.append(re_status_for_level(req.id, level, legacy, by_re))

    if not statuses:
        return legacy.get(req.id)

    in_scope = [s for s in statuses if not excludes_from_sl_denominator(s)]
    if not in_scope:
        return "not_applicable"
    if any(s is None for s in in_scope):
        for blocked in ("non_compliant", "insufficient_info", "partial"):
            if any(s == blocked for s in in_scope):
                return blocked
        return None
    if any(blocks_sl_achievement(s) for s in in_scope):
        for blocked in ("non_compliant", "insufficient_info", "partial"):
            if any(s == blocked for s in in_scope):
                return blocked
        return "non_compliant"
    if all(satisfies_sl_level(s) for s in in_scope):
        return "compliant"
    return None


def build_sr_compliance_map(
    requirements: List[SecurityRequirement],
    target_sl: int,
    legacy: Dict[Any, str],
    by_re: Dict[ReLevelKey, str],
) -> dict:
    """Map sr.id -> status for FR stats and coverage (RE-aware with legacy fallback)."""
    if not by_re:
        return dict(legacy)
    result = {}
    for req in requirements:
        result[req.id] = aggregate_sr_status_from_re(req, target_sl, legacy, by_re)
    for sr_id, status in legacy.items():
        if sr_id not in result:
            result[sr_id] = status
    return result


def sl_level_fully_satisfied_re(
    sl: int,
    requirements: List[SecurityRequirement],
    legacy: Dict[Any, str],
    by_re: Dict[ReLevelKey, str],
) -> bool:
    for req in filter_requirements_for_sl(requirements, sl):
        for re_level in range(1, sl + 1):
            status = re_status_for_level(req.id, re_level, legacy, by_re)
            if excludes_from_sl_denominator(status):
                continue
            if blocks_sl_achievement(status):
                return False
    return True


def sl_level_fully_satisfied_legacy(
    requirements: List[SecurityRequirement],
    compliance_map: dict,
) -> bool:
    in_scope = []
    for req in requirements:
        status = extract_assessment_status(compliance_map.get(req.id))
        if excludes_from_sl_denominator(status):
            continue
        in_scope.append(status)
    if not in_scope:
        return True
    return all(satisfies_sl_level(status) for status in in_scope)


def sl_level_fully_satisfied(
    requirements: List[SecurityRequirement],
    compliance_map: dict,
    *,
    legacy: Optional[Dict[Any, str]] = None,
    by_re: Optional[Dict[ReLevelKey, str]] = None,
    sl: Optional[int] = None,
) -> bool:
    """
    True when every non-N/A applicable SR/RE at this SL is compliant.
    Pass by_re + sl for RE-normative checks; otherwise uses compliance_map (SR-level).
    """
    if by_re is not None and sl is not None:
        return sl_level_fully_satisfied_re(sl, requirements, legacy or {}, by_re)
    return sl_level_fully_satisfied_legacy(requirements, compliance_map)


def highest_achieved_sl(
    target_sl: int,
    requirements: List[SecurityRequirement],
    compliance_map: dict,
    *,
    legacy: Optional[Dict[Any, str]] = None,
    by_re: Optional[Dict[ReLevelKey, str]] = None,
) -> Optional[int]:
    use_re = bool(by_re)
    for sl in range(target_sl, 0, -1):
        sl_reqs = filter_requirements_for_sl(requirements, sl)
        if not sl_reqs:
            continue
        if use_re:
            if sl_level_fully_satisfied(
                sl_reqs, compliance_map, legacy=legacy, by_re=by_re, sl=sl
            ):
                return sl
        elif sl_level_fully_satisfied(sl_reqs, compliance_map):
            return sl
    return None


def assessment_coverage_ratio(
    applicable: List[SecurityRequirement],
    compliance_map: dict,
) -> float:
    """Fraction of applicable SRs with any assessment (excluding N/A from denominator)."""
    in_scope = []
    for req in applicable:
        status = extract_assessment_status(compliance_map.get(req.id))
        if excludes_from_sl_denominator(status):
            continue
        in_scope.append(req)
    if not in_scope:
        return 1.0
    assessed = sum(
        1
        for req in in_scope
        if extract_assessment_status(compliance_map.get(req.id)) is not None
    )
    return assessed / len(in_scope)


def compute_fr_summary_stats(
    sr_requirements: List[SecurityRequirement],
    compliance_map: dict,
    target_sl: Optional[int] = None,
) -> dict:
    """
    FR-level stats aligned with SL-A rules: denominator = SR applicable at SL-T (excl. N/A).
    """
    counts = {
        "compliant": 0,
        "partial": 0,
        "non_compliant": 0,
        "not_applicable": 0,
        "insufficient_info": 0,
        "not_assessed": 0,
    }
    in_scope: List[SecurityRequirement] = []
    for sr in sr_requirements:
        if target_sl is not None and not requirement_applies_at_sl(sr, target_sl):
            continue
        status = extract_assessment_status(compliance_map.get(sr.id))
        if excludes_from_sl_denominator(status):
            counts["not_applicable"] += 1
            continue
        in_scope.append(sr)
        if status is None:
            counts["not_assessed"] += 1
        elif status in counts:
            counts[status] += 1

    weighted = counts["compliant"] + counts["partial"] * 0.5
    denom = len(in_scope) or 1
    return {
        "compliant_count": counts["compliant"],
        "partial_count": counts["partial"],
        "non_compliant_count": counts["non_compliant"],
        "not_applicable_count": counts["not_applicable"],
        "insufficient_info_count": counts["insufficient_info"],
        "not_assessed_count": counts["not_assessed"],
        "total_sr": len(sr_requirements),
        "in_scope_count": len(in_scope),
        "compliance_percentage": round((weighted / denom) * 100, 1),
    }


def derive_compliance_status(
    target_sl: Optional[int],
    achieved_sl: Optional[int],
    coverage: float,
    has_any_assessment: bool,
) -> str:
    """
    Align zone compliance_status with SL-A vs SL-T (not arbitrary % thresholds).
    """
    if not target_sl:
        return "not_assessed"
    if not has_any_assessment or coverage < 0.01:
        return "not_assessed"
    if achieved_sl is None:
        return "non_compliant"
    if achieved_sl >= target_sl:
        return "compliant"
    if achieved_sl > 0:
        return "partial"
    return "non_compliant"
