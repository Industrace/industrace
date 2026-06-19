"""Catalog completeness for IEC 62443-3-3 security requirements seed."""
from app.init_data.init_security_requirements import SECURITY_REQUIREMENTS_DATA
from app.init_data.iec62443_re_texts import RE_TEXTS


def _sr_ids():
    return [
        r["requirement_id"]
        for r in SECURITY_REQUIREMENTS_DATA
        if r.get("requirement_category") == "SR"
    ]


def test_security_requirements_seed_has_52_srs():
    ids = _sr_ids()
    assert len(ids) == 52
    assert len(set(ids)) == 52


def test_sr_2_13_present_in_seed():
    assert "SR 2.13" in _sr_ids()


def test_re_texts_cover_all_52_srs():
    """Every SR in the seed has RE levels 1–4 with normative-style texts."""
    sr_ids = set(_sr_ids())
    assert set(RE_TEXTS.keys()) == sr_ids
    for sr_id in sr_ids:
        assert set(RE_TEXTS[sr_id].keys()) == {1, 2, 3, 4}
        for level in range(1, 5):
            assert RE_TEXTS[sr_id][level].strip()
