import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Centralized application configurations"""

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql+psycopg://user:password@localhost/cmdb"
    )

    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )
    JWT_ISSUER: str = os.getenv("JWT_ISSUER", "industrace-api")
    JWT_AUDIENCE: str = os.getenv("JWT_AUDIENCE", "industrace-client")

    # Upload
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB

    # Pagination
    DEFAULT_PAGE_SIZE: int = int(os.getenv("DEFAULT_PAGE_SIZE", "100"))
    MAX_PAGE_SIZE: int = int(os.getenv("MAX_PAGE_SIZE", "1000"))

    # Audit Log
    AUDIT_LOG_ENABLED: bool = os.getenv("AUDIT_LOG_ENABLED", "true").lower() == "true"
    AUDIT_LOG_RETENTION_DAYS: int = int(os.getenv("AUDIT_LOG_RETENTION_DAYS", "365"))

    # CORS
    CORS_ORIGINS: str = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:8080,http://localhost:5173",
    )

    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

    # Cookie Settings
    SECURE_COOKIES: bool = os.getenv("SECURE_COOKIES", "false").lower() == "true"
    SAME_SITE_COOKIES: str = os.getenv("SAME_SITE_COOKIES", "lax")

    # OpenAPI Security
    API_KEY_HEADER: str = os.getenv("API_KEY_HEADER", "X-API-Key")
    API_KEY_LENGTH: int = int(os.getenv("API_KEY_LENGTH", "32"))
    API_KEY_PREFIX: str = os.getenv("API_KEY_PREFIX", "ind_")

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_DEFAULT: str = os.getenv("RATE_LIMIT_DEFAULT", "100/hour")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_ENABLED: bool = os.getenv("REDIS_ENABLED", "true").lower() == "true"
    
    # Account Lockout
    MAX_LOGIN_ATTEMPTS: int = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
    LOCKOUT_DURATION_MINUTES: int = int(os.getenv("LOCKOUT_DURATION_MINUTES", "15"))

    # MFA / TOTP
    MFA_PENDING_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("MFA_PENDING_TOKEN_EXPIRE_MINUTES", "5")
    )
    MFA_MAX_ATTEMPTS: int = int(os.getenv("MFA_MAX_ATTEMPTS", "5"))
    MFA_LOCKOUT_MINUTES: int = int(os.getenv("MFA_LOCKOUT_MINUTES", "15"))
    MFA_BACKUP_CODES_COUNT: int = int(os.getenv("MFA_BACKUP_CODES_COUNT", "10"))
    MFA_ISSUER_NAME: str = os.getenv("MFA_ISSUER_NAME", "Industrace")
    
    # SSO/Enterprise Auth
    SSO_REDIRECT_URI: str = os.getenv("SSO_REDIRECT_URI") or "http://localhost:5173/auth/sso/callback"
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "")  # For encrypting client secrets (generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    RATE_LIMIT_STRICT: str = os.getenv("RATE_LIMIT_STRICT", "10/minute")
    # Network probe endpoints (per API key)
    PROBE_RATE_LIMIT_HEARTBEAT: str = os.getenv("PROBE_RATE_LIMIT_HEARTBEAT", "120/minute")
    PROBE_RATE_LIMIT_DATA: str = os.getenv("PROBE_RATE_LIMIT_DATA", "30/hour")
    PROBE_RATE_LIMIT_CONFIG: str = os.getenv("PROBE_RATE_LIMIT_CONFIG", "60/hour")
    PROBE_HEARTBEAT_STALE_SECONDS: int = int(os.getenv("PROBE_HEARTBEAT_STALE_SECONDS", "300"))
    PROBE_RETENTION_DAYS: int = int(os.getenv("PROBE_RETENTION_DAYS", "90"))

    # API Versioning
    API_VERSION: str = os.getenv("API_VERSION", "v1")
    API_TITLE: str = os.getenv("API_TITLE", "Industrace API")
    API_DESCRIPTION: str = os.getenv(
        "API_DESCRIPTION",
        "Configuration Management Database for Industrial Control Systems",
    )

    # External API Settings
    EXTERNAL_API_ENABLED: bool = (
        os.getenv("EXTERNAL_API_ENABLED", "true").lower() == "true"
    )
    EXTERNAL_API_DOCS_ENABLED: bool = (
        os.getenv("EXTERNAL_API_DOCS_ENABLED", "").lower() == "true"
        if os.getenv("EXTERNAL_API_DOCS_ENABLED") is not None
        else os.getenv("ENVIRONMENT", "development") != "production"
    )

    # Setup wizard protection (required in production)
    SETUP_TOKEN: str = os.getenv("SETUP_TOKEN", "")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate_security_settings()

    def _validate_security_settings(self):
        """Validate critical security settings"""
        if self.ENVIRONMENT == "production":
            if self.SECRET_KEY in ["your-secret-key-change-in-production", "your-secret-key"]:
                raise ValueError(
                    "SECRET_KEY must be changed in production environment"
                )
            if self.DEBUG:
                raise ValueError("DEBUG must be False in production environment")
            if not self.SECURE_COOKIES:
                raise ValueError("SECURE_COOKIES must be True in production environment")
            if self.SAME_SITE_COOKIES != "strict":
                raise ValueError("SAME_SITE_COOKIES must be 'strict' in production environment")
            if not self.ENCRYPTION_KEY:
                raise ValueError(
                    "ENCRYPTION_KEY must be set in production (required for SSO client secret encryption)"
                )
            if not self.SETUP_TOKEN:
                raise ValueError(
                    "SETUP_TOKEN must be set in production (protects first-time setup endpoints)"
                )

    model_config = SettingsConfigDict(env_file=".env")


# Global settings instance
settings = Settings()
