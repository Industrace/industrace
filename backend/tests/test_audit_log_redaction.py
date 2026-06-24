from app.services.audit_log import redact_sensitive_data, REDACTED_VALUE


def test_redact_sensitive_data_masks_api_key():
    payload = {
        "name": "probe-1",
        "api_key": "ind_live_super_secret_key",
        "interface_name": "eth0",
    }
    redacted = redact_sensitive_data(payload)
    assert redacted["name"] == "probe-1"
    assert redacted["api_key"] == REDACTED_VALUE
    assert redacted["interface_name"] == "eth0"


def test_redact_sensitive_data_preserves_non_secret_flags():
    payload = {"password_change_required": True, "password_hash": "hash-value"}
    redacted = redact_sensitive_data(payload)
    assert redacted["password_change_required"] is True
    assert redacted["password_hash"] == REDACTED_VALUE


def test_redact_sensitive_data_nested_dict():
    payload = {"probe": {"api_key": "secret", "status": "active"}}
    redacted = redact_sensitive_data(payload)
    assert redacted["probe"]["api_key"] == REDACTED_VALUE
    assert redacted["probe"]["status"] == "active"
