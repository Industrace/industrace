import os
from pydantic_settings import BaseSettings
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
    
    # SSO/Enterprise Auth
    SSO_REDIRECT_URI: str = os.getenv("SSO_REDIRECT_URI", "http://localhost:5173/auth/sso/callback")
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "")  # For encrypting client secrets (generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    RATE_LIMIT_STRICT: str = os.getenv("RATE_LIMIT_STRICT", "10/minute")

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
        os.getenv("EXTERNAL_API_DOCS_ENABLED", "true").lower() == "true"
    )

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

    class Config:
        env_file = ".env"


# Global settings instance
settings = Settings()
