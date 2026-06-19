"""
API per la configurazione del server syslog esterno (inoltro audit log).
"""
import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import TenantSyslogConfig, User
from app.schemas.tenant_syslog_config import (
    TenantSyslogConfigRead,
    TenantSyslogConfigCreate,
    TenantSyslogConfigUpdate,
)
from app.services.auth import get_current_user
from app.services.rbac import require_permission
from app.errors.exceptions import ErrorCodeException
from app.errors.error_codes import ErrorCode
from app.services.syslog_forwarder import _format_bsd_message, _send_udp, _send_tcp

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/syslog-config",
    tags=["syslog-config"],
)


@router.get("", response_model=TenantSyslogConfigRead)
def get_syslog_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    perm=Depends(require_permission("external_log", 1)),
):
    config = (
        db.query(TenantSyslogConfig)
        .filter(TenantSyslogConfig.tenant_id == current_user.tenant_id)
        .first()
    )
    if not config:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.SYSLOG_CONFIG_NOT_FOUND
        )
    return config


@router.get("/exists")
def syslog_config_exists(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    perm=Depends(require_permission("external_log", 1)),
):
    """Usato dal frontend per sapere se esiste una config (per mostrare lo stato nel tile)."""
    config = (
        db.query(TenantSyslogConfig)
        .filter(TenantSyslogConfig.tenant_id == current_user.tenant_id)
        .first()
    )
    return {"exists": config is not None, "enabled": config.enabled if config else False}


@router.post("", response_model=TenantSyslogConfigRead)
@router.put("", response_model=TenantSyslogConfigRead)
def set_syslog_config(
    config_in: TenantSyslogConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    perm=Depends(require_permission("external_log", 2)),
):
    protocol = (config_in.protocol or "udp").lower()
    if protocol not in ("udp", "tcp"):
        protocol = "udp"
    facility = config_in.facility if config_in.facility is not None else 16
    facility = max(0, min(23, facility))

    config = (
        db.query(TenantSyslogConfig)
        .filter(TenantSyslogConfig.tenant_id == current_user.tenant_id)
        .first()
    )

    data = {
        "host": config_in.host,
        "port": config_in.port or 514,
        "protocol": protocol,
        "facility": facility,
        "enabled": config_in.enabled if config_in.enabled is not None else False,
    }

    if config:
        for key, value in data.items():
            setattr(config, key, value)
    else:
        config = TenantSyslogConfig(tenant_id=current_user.tenant_id, **data)
        db.add(config)

    try:
        db.commit()
        db.refresh(config)
        return config
    except Exception as e:
        db.rollback()
        logger.error("Error saving syslog config: %s", e, exc_info=True)
        raise ErrorCodeException(
            status_code=400,
            error_code=ErrorCode.SYSLOG_CONFIG_SAVE_ERROR,
            detail=f"Error saving syslog configuration: {str(e)}",
        )


@router.patch("", response_model=TenantSyslogConfigRead)
def update_syslog_config(
    config_in: TenantSyslogConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    perm=Depends(require_permission("external_log", 2)),
):
    config = (
        db.query(TenantSyslogConfig)
        .filter(TenantSyslogConfig.tenant_id == current_user.tenant_id)
        .first()
    )
    if not config:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.SYSLOG_CONFIG_NOT_FOUND
        )

    updates = config_in.model_dump(exclude_unset=True)
    if "protocol" in updates and updates["protocol"] not in ("udp", "tcp"):
        updates["protocol"] = "udp"
    if "facility" in updates:
        updates["facility"] = max(0, min(23, updates["facility"]))

    for key, value in updates.items():
        setattr(config, key, value)

    db.commit()
    db.refresh(config)
    return config


@router.post("/test")
def test_syslog_config(
    config_data: TenantSyslogConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    perm=Depends(require_permission("external_log", 2)),
):
    """
    Invia un messaggio di test al server syslog configurato.
    Usa i parametri passati nel body oppure quelli salvati in DB.
    """
    host = config_data.host
    port = config_data.port or 514
    protocol = (config_data.protocol or "udp").lower()
    if protocol not in ("udp", "tcp"):
        protocol = "udp"
    facility = config_data.facility if config_data.facility is not None else 16
    facility = max(0, min(23, facility))

    if not host or not host.strip():
        # Prova a usare la config salvata
        config = (
            db.query(TenantSyslogConfig)
            .filter(TenantSyslogConfig.tenant_id == current_user.tenant_id)
            .first()
        )
        if not config or not config.host:
            raise ErrorCodeException(
                status_code=400,
                error_code=ErrorCode.SYSLOG_CONFIG_NOT_FOUND,
                detail="Indicare host (e porta) del server syslog o salvare prima la configurazione.",
            )
        host = config.host
        port = config.port or 514
        protocol = (config.protocol or "udp").lower()
        facility = config.facility if config.facility is not None else 16

    message = '{"test": true, "message": "Industrace syslog test", "source": "industrace-audit"}'
    data = _format_bsd_message(facility, "industrace-audit", message)

    try:
        if protocol == "tcp":
            _send_tcp(host, port, data)
        else:
            _send_udp(host, port, data)
        return {"detail": "Test message sent successfully", "host": host, "port": port}
    except Exception as e:
        logger.warning("Syslog test failed: %s", e)
        raise ErrorCodeException(
            status_code=400,
            error_code=ErrorCode.SYSLOG_SEND_ERROR,
            detail=f"Impossibile inviare il messaggio di test al server syslog: {str(e)}",
        )
