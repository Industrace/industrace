from app.services.tenant_features import (
    FEATURE_IEC62443,
    get_tenant_features,
    is_iec62443_enabled,
    set_iec62443_enabled,
    set_feature,
)


class _FakeTenant:
    def __init__(self, settings=None):
        self.settings = settings


def test_default_features_enabled_when_missing():
    assert get_tenant_features(None) == {FEATURE_IEC62443: True}
    assert get_tenant_features({}) == {FEATURE_IEC62443: True}
    assert is_iec62443_enabled(_FakeTenant()) is True


def test_disable_iec62443_in_settings():
    settings = set_iec62443_enabled({"theme": "industrial"}, False)
    assert settings["features"][FEATURE_IEC62443] is False
    assert get_tenant_features(settings)[FEATURE_IEC62443] is False
    assert is_iec62443_enabled(_FakeTenant(settings)) is False


def test_enable_iec62443_explicitly():
    settings = set_feature({"features": {FEATURE_IEC62443: False}}, FEATURE_IEC62443, True)
    assert is_iec62443_enabled(_FakeTenant(settings)) is True
