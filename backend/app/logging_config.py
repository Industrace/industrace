import logging
import logging.config
import os
from datetime import datetime
from app.config import settings
import sys
from typing import Dict, Any

def setup_logging():
    """Setup centralized logging configuration"""
    
    # Suppress specific warnings
    logging.getLogger("passlib.handlers.bcrypt").setLevel(logging.ERROR)
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific log levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("alembic").setLevel(logging.WARNING)
    
    # Suppress noisy libraries
    logging.getLogger("passlib").setLevel(logging.ERROR)
    logging.getLogger("bcrypt").setLevel(logging.ERROR)
    
    # Create logs directory if it doesn't exist
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Determine log level based on environment
    log_level = "INFO" if settings.ENVIRONMENT == "production" else "DEBUG"
    
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "format": '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}',
                "datefmt": "%Y-%m-%d %H:%M:%S",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "default",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": log_level,
                "formatter": "detailed",
                "filename": f"{log_dir}/industrace.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": f"{log_dir}/error.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
            "security_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": f"{log_dir}/security.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 10,
            }
        },
        "loggers": {
            "": {  # Root logger
                "handlers": ["console", "file"],
                "level": log_level,
                "propagate": False,
            },
            "app": {  # Application logger
                "handlers": ["console", "file"],
                "level": log_level,
                "propagate": False,
            },
            "app.services.auth": {  # Authentication logger
                "handlers": ["console", "security_file"],
                "level": "INFO",
                "propagate": False,
            },
            "app.services.audit_log": {  # Audit logger
                "handlers": ["console", "security_file"],
                "level": "INFO",
                "propagate": False,
            },
            "security": {  # Security events logger
                "handlers": ["console", "security_file"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn": {  # Uvicorn logger
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False,
            },
            "sqlalchemy": {  # SQLAlchemy logger
                "handlers": ["console", "file"],
                "level": "WARNING",
                "propagate": False,
            },
        },
    }
    
    logging.config.dictConfig(logging_config)
    
    # Log startup information
    logger = logging.getLogger("app")
    logger.info(f"Industrace starting up - Environment: {settings.ENVIRONMENT}")
    logger.info(f"Log level: {log_level}")
    logger.info(f"Database URL: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'local'}")
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name"""
    return logging.getLogger(f"app.{name}")

def log_security_event(event_type: str, details: dict, user_id: str = None, tenant_id: str = None):
    """Log security-related events"""
    logger = logging.getLogger("app.services.auth")
    
    log_data = {
        "event_type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "details": details,
        "user_id": user_id,
        "tenant_id": tenant_id,
    }
    
    logger.info(f"Security event: {log_data}")

def log_audit_event(action: str, entity_type: str, entity_id: str, user_id: str, tenant_id: str, details: dict = None):
    """Log audit events"""
    logger = logging.getLogger("app.services.audit_log")
    
    log_data = {
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "user_id": user_id,
        "tenant_id": tenant_id,
        "timestamp": datetime.utcnow().isoformat(),
        "details": details or {},
    }
    
    logger.info(f"Audit event: {log_data}") 