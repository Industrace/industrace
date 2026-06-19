import pytest
from cryptography.fernet import Fernet

import app.services.sso_encryption as sso_encryption
from app.config import settings
from app.services.sso_encryption import encrypt_secret, decrypt_secret


@pytest.fixture
def encryption_key(monkeypatch):
    key = Fernet.generate_key().decode()
    monkeypatch.setenv("ENCRYPTION_KEY", key)
    monkeypatch.setattr(settings, "ENCRYPTION_KEY", key)
    monkeypatch.setattr(sso_encryption, "_fernet", None)
    return key


def test_encrypt_decrypt_roundtrip(encryption_key):
    plain = "client-secret-value"
    encrypted = encrypt_secret(plain)
    assert encrypted != plain
    assert decrypt_secret(encrypted) == plain


def test_decrypt_invalid_raises(encryption_key):
    with pytest.raises(Exception):
        decrypt_secret("not-valid-ciphertext")
