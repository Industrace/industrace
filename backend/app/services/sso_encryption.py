# backend/app/services/sso_encryption.py
"""
Service per encrypt/decrypt client secrets per SSO configuration.
Usa Fernet (symmetric encryption) per proteggere i client secrets nel database.
"""
from cryptography.fernet import Fernet
from app.config import settings
import base64
import logging

logger = logging.getLogger(__name__)

# Generate key if not exists (for development only)
if not settings.ENCRYPTION_KEY:
    logger.warning("ENCRYPTION_KEY not set - generating temporary key (NOT for production!)")
    _temp_key = Fernet.generate_key()
    _fernet = Fernet(_temp_key)
else:
    try:
        _fernet = Fernet(settings.ENCRYPTION_KEY.encode())
    except Exception as e:
        logger.error(f"Invalid ENCRYPTION_KEY: {e}")
        raise ValueError("Invalid ENCRYPTION_KEY. Generate with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"")


def encrypt_secret(secret: str) -> str:
    """Encrypt a client secret"""
    if not secret:
        return ""
    try:
        encrypted = _fernet.encrypt(secret.encode())
        return encrypted.decode()
    except Exception as e:
        logger.error(f"Error encrypting secret: {e}")
        raise


def decrypt_secret(encrypted: str) -> str:
    """Decrypt a client secret"""
    if not encrypted:
        return ""
    try:
        decrypted = _fernet.decrypt(encrypted.encode())
        return decrypted.decode()
    except Exception as e:
        logger.error(f"Error decrypting secret: {e}")
        raise

