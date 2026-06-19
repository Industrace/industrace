from app.services.log_sanitizer import redact_sensitive_text


def test_redact_api_key_header():
    text = "Failed request X-API-Key: secret-token-12345"
    assert redact_sensitive_text(text) == "Failed request X-API-Key: ***"


def test_redact_api_key_query_param():
    text = "url failed api_key=supersecret&other=1"
    assert "supersecret" not in redact_sensitive_text(text)
    assert "api_key=***" in redact_sensitive_text(text)


def test_redact_api_key_assignment():
    text = 'config api_key: "my-long-key-value"'
    redacted = redact_sensitive_text(text)
    assert "my-long-key-value" not in redacted
