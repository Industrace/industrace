# backend/app/services/sso_encryption.py
"""
Service per encrypt/decrypt client secrets per SSO configuration.
Usa Fernet (symmetric encryption) per proteggere i client secrets nel database.
"""
from cryptography.fernet import Fernet
from app.config import settings
import base64
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Initialize Fernet - lazy initialization to avoid blocking app startup
_fernet = None

# Path to store temporary encryption key (only used if ENCRYPTION_KEY env var is not set)
# Use logs directory which is typically mounted as a volume for persistence
_TEMP_KEY_FILE = Path("/app/logs/.encryption_key_temp")

def _get_fernet():
    """Get or initialize Fernet instance"""
    global _fernet
    if _fernet is not None:
        return _fernet
    
    if not settings.ENCRYPTION_KEY:
        # In production, require ENCRYPTION_KEY to be set
        if settings.ENVIRONMENT == "production":
            logger.error("ENCRYPTION_KEY must be set in production environment!")
            raise ValueError(
                "ENCRYPTION_KEY environment variable is required in production. "
                "Generate with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )
        
        # In development, use a persistent temporary key file
        logger.warning("ENCRYPTION_KEY not set - using persistent temporary key file (development only)")
        
        # Try to load existing temporary key
        if _TEMP_KEY_FILE.exists():
            try:
                with open(_TEMP_KEY_FILE, 'rb') as f:
                    _temp_key = f.read()
                logger.info("Loaded existing temporary encryption key from file")
            except Exception as e:
                logger.warning(f"Failed to load temporary key file: {e}. Generating new key.")
                _temp_key = Fernet.generate_key()
                try:
                    with open(_TEMP_KEY_FILE, 'wb') as f:
                        f.write(_temp_key)
                    # Set restrictive permissions (owner read/write only)
                    os.chmod(_TEMP_KEY_FILE, 0o600)
                    logger.info("Generated and saved new temporary encryption key")
                except Exception as e:
                    logger.error(f"Failed to save temporary key file: {e}")
                    raise ValueError("Failed to create temporary encryption key file. Please set ENCRYPTION_KEY environment variable.")
        else:
            # Generate new temporary key and save it
            _temp_key = Fernet.generate_key()
            try:
                with open(_TEMP_KEY_FILE, 'wb') as f:
                    f.write(_temp_key)
                # Set restrictive permissions (owner read/write only)
                os.chmod(_TEMP_KEY_FILE, 0o600)
                logger.info("Generated and saved new temporary encryption key")
            except Exception as e:
                logger.error(f"Failed to save temporary key file: {e}")
                raise ValueError("Failed to create temporary encryption key file. Please set ENCRYPTION_KEY environment variable.")
        
        _fernet = Fernet(_temp_key)
    else:
        try:
            _fernet = Fernet(settings.ENCRYPTION_KEY.encode())
            logger.info("Initialized Fernet with ENCRYPTION_KEY from environment")
        except Exception as e:
            logger.error(f"Invalid ENCRYPTION_KEY: {e}")
            raise ValueError("Invalid ENCRYPTION_KEY. Generate with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"")
    
    return _fernet


def encrypt_secret(secret: str) -> str:
    """Encrypt a client secret"""
    if not secret:
        return ""
    try:
        fernet = _get_fernet()
        encrypted = fernet.encrypt(secret.encode())
        return encrypted.decode()
    except Exception as e:
        logger.error(f"Error encrypting secret: {e}")
        raise


def decrypt_secret(encrypted: str) -> str:
    """Decrypt a client secret"""
    if not encrypted:
        return ""
    try:
        fernet = _get_fernet()
        decrypted = fernet.decrypt(encrypted.encode())
        return decrypted.decode()
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error decrypting secret: {error_msg}")
        
        # Provide more helpful error message
        if "InvalidToken" in error_msg or "Invalid signature" in error_msg:
            logger.error(
                "This usually means the ENCRYPTION_KEY has changed. "
                "The client secret was encrypted with a different key. "
                "If you're using a temporary key in development, make sure the key file persists. "
                "In production, ensure ENCRYPTION_KEY is set and remains constant."
            )
        raise

