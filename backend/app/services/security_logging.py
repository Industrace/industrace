"""
Security event logging utilities.
Logs security-related events to a dedicated security log file.
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import Request

# Create dedicated security logger
security_logger = logging.getLogger("security")


def log_security_event(
    event_type: str,
    message: str,
    request: Optional[Request] = None,
    user_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    additional_data: Optional[Dict[str, Any]] = None,
    severity: str = "INFO"
):
    """
    Log a security event with structured information.
    
    Args:
        event_type: Type of security event (e.g., "LOGIN_FAILED", "UNAUTHORIZED_ACCESS")
        message: Human-readable message
        request: FastAPI Request object (optional, used to extract IP and headers)
        user_id: User ID if available
        tenant_id: Tenant ID if available
        ip_address: IP address (extracted from request if not provided)
        additional_data: Additional context data
        severity: Log severity level (INFO, WARNING, ERROR)
    """
    # Extract IP address from request if not provided
    if request and not ip_address:
        ip_address = request.client.host if request.client else None
        # Try to get real IP from X-Forwarded-For header
        if request.headers.get("X-Forwarded-For"):
            ip_address = request.headers.get("X-Forwarded-For").split(",")[0].strip()
    
    # Build structured log data
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "message": message,
        "severity": severity,
    }
    
    if user_id:
        log_data["user_id"] = str(user_id)
    if tenant_id:
        log_data["tenant_id"] = str(tenant_id)
    if ip_address:
        log_data["ip_address"] = ip_address
    if request:
        log_data["user_agent"] = request.headers.get("User-Agent")
        log_data["path"] = str(request.url.path)
        log_data["method"] = request.method
    
    if additional_data:
        log_data.update(additional_data)
    
    # Log with appropriate severity
    if severity == "ERROR":
        security_logger.error(f"SECURITY_EVENT: {log_data}")
    elif severity == "WARNING":
        security_logger.warning(f"SECURITY_EVENT: {log_data}")
    else:
        security_logger.info(f"SECURITY_EVENT: {log_data}")


def log_failed_login(email: str, request: Request, reason: str = "INVALID_CREDENTIALS"):
    """Log a failed login attempt"""
    log_security_event(
        event_type="LOGIN_FAILED",
        message=f"Failed login attempt for email: {email}",
        request=request,
        additional_data={
            "email": email,
            "reason": reason
        },
        severity="WARNING"
    )


def log_successful_login(user_id: str, tenant_id: str, email: str, request: Request):
    """Log a successful login"""
    log_security_event(
        event_type="LOGIN_SUCCESS",
        message=f"Successful login for user: {email}",
        request=request,
        user_id=user_id,
        tenant_id=tenant_id,
        additional_data={"email": email},
        severity="INFO"
    )


def log_unauthorized_access(
    request: Request,
    user_id: Optional[str] = None,
    resource: Optional[str] = None,
    reason: str = "UNAUTHORIZED"
):
    """Log an unauthorized access attempt"""
    log_security_event(
        event_type="UNAUTHORIZED_ACCESS",
        message=f"Unauthorized access attempt to {resource or request.url.path}",
        request=request,
        user_id=user_id,
        additional_data={
            "resource": resource or str(request.url.path),
            "reason": reason
        },
        severity="WARNING"
    )


def log_permission_change(
    user_id: str,
    tenant_id: str,
    changed_user_id: Optional[str],
    changed_role_id: Optional[str],
    action: str,
    request: Request
):
    """Log a permission or role change"""
    log_security_event(
        event_type="PERMISSION_CHANGE",
        message=f"Permission change: {action}",
        request=request,
        user_id=user_id,
        tenant_id=tenant_id,
        additional_data={
            "action": action,
            "changed_user_id": str(changed_user_id) if changed_user_id else None,
            "changed_role_id": str(changed_role_id) if changed_role_id else None,
        },
        severity="INFO"
    )


def log_api_key_usage(
    api_key_id: str,
    tenant_id: str,
    endpoint: str,
    request: Request
):
    """Log API key usage"""
    log_security_event(
        event_type="API_KEY_USAGE",
        message=f"API key used: {api_key_id}",
        request=request,
        tenant_id=tenant_id,
        additional_data={
            "api_key_id": str(api_key_id),
            "endpoint": endpoint,
        },
        severity="INFO"
    )


def log_rate_limit_exceeded(
    identifier: str,
    limit: str,
    request: Request
):
    """Log rate limit exceeded"""
    log_security_event(
        event_type="RATE_LIMIT_EXCEEDED",
        message=f"Rate limit exceeded for {identifier}",
        request=request,
        additional_data={
            "identifier": identifier,
            "limit": limit,
        },
        severity="WARNING"
    )
