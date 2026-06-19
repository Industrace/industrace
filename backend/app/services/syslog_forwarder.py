"""
Inoltro eventi audit log verso un server syslog esterno.
Formato messaggio: BSD syslog (compatibile con la maggior parte dei collector).
"""
import json
import logging
import socket
from datetime import datetime, timezone
from typing import Optional, Any
from sqlalchemy.orm import Session

from app.models.tenant_syslog_config import TenantSyslogConfig
from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)

# Severity per syslog: 6 = informational (audit)
SEVERITY_INFO = 6


def _syslog_priority(facility: int, severity: int) -> int:
    """Calcola il valore PRI (RFC 5424/BSD): facility * 8 + severity."""
    return facility * 8 + severity


def _format_bsd_message(facility: int, tag: str, message: str) -> bytes:
    """
    Formato BSD syslog: <PRI>timestamp hostname tag: message
    Es: <134>Feb 12 10:00:00 industrace audit: {"action":"create",...}
    """
    pri = _syslog_priority(facility, SEVERITY_INFO)
    # Timestamp in formato BSD: Mmm dd HH:MM:SS
    ts = datetime.now(timezone.utc).strftime("%b %d %H:%M:%S")
    hostname = "industrace"
    # Il messaggio viene troncato/sanitizzato per evitare newline nel frame
    msg_line = message.replace("\n", " ").strip()
    if len(msg_line) > 8192:
        msg_line = msg_line[:8192] + "..."
    frame = f"<{pri}>{ts} {hostname} {tag}: {msg_line}"
    return frame.encode("utf-8", errors="replace")


def _audit_entry_to_message(entry: AuditLog) -> str:
    """Serializza una voce di audit in una stringa JSON per syslog."""
    payload = {
        "id": str(entry.id),
        "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
        "tenant_id": str(entry.tenant_id),
        "user_id": str(entry.user_id),
        "action": entry.action,
        "entity": entry.entity,
        "entity_id": str(entry.entity_id) if entry.entity_id else None,
        "description": entry.description,
        "ip_address": entry.ip_address,
    }
    if entry.old_data:
        try:
            payload["old_data"] = entry.old_data if isinstance(entry.old_data, dict) else json.loads(entry.old_data)
        except Exception:
            payload["old_data_raw"] = str(entry.old_data)[:500]
    if entry.new_data:
        try:
            payload["new_data"] = entry.new_data if isinstance(entry.new_data, dict) else json.loads(entry.new_data)
        except Exception:
            payload["new_data_raw"] = str(entry.new_data)[:500]
    return json.dumps(payload, ensure_ascii=False)


def _get_config(db: Session, tenant_id: Any) -> Optional[TenantSyslogConfig]:
    """Recupera la configurazione syslog per il tenant."""
    return (
        db.query(TenantSyslogConfig)
        .filter(
            TenantSyslogConfig.tenant_id == tenant_id,
            TenantSyslogConfig.enabled == True,
            TenantSyslogConfig.host.isnot(None),
            TenantSyslogConfig.host != "",
        )
        .first()
    )


def _send_udp(host: str, port: int, data: bytes) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.settimeout(2)
        sock.sendto(data, (host, port))
    finally:
        sock.close()


def _send_tcp(host: str, port: int, data: bytes) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.settimeout(5)
        sock.connect((host, port))
        # Alcuni server si aspettano un messaggio terminato da \n
        if not data.endswith(b"\n"):
            data = data + b"\n"
        sock.sendall(data)
    finally:
        sock.close()


def forward_audit_entry_to_syslog(db: Session, audit_entry: AuditLog) -> None:
    """
    Inoltra una voce di audit al server syslog configurato per il tenant.
    Non solleva eccezioni: eventuali errori vengono solo loggati.
    """
    try:
        config = _get_config(db, audit_entry.tenant_id)
        if not config:
            return
        message = _audit_entry_to_message(audit_entry)
        data = _format_bsd_message(config.facility, "industrace-audit", message)
        if config.protocol == "tcp":
            _send_tcp(config.host, config.port, data)
        else:
            _send_udp(config.host, config.port, data)
    except Exception as e:
        logger.warning("Syslog forward failed for audit entry %s: %s", getattr(audit_entry, "id", None), e)
