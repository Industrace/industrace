from fastapi import Depends, HTTPException, status, Request
from app.services.auth import get_current_user
from app.models import User
from typing import Optional

_BULK_PATH_KEYWORDS = ("bulk", "/import/", "recalculate-all", "recalculate", "/empty")


def _resolve_min_level(method: str, path: str) -> int:
    """Infer minimum RBAC level from HTTP method and route path."""
    path_lower = path.lower()
    if any(keyword in path_lower for keyword in _BULK_PATH_KEYWORDS):
        return 4
    method_upper = method.upper()
    if method_upper in ("GET", "HEAD", "OPTIONS"):
        return 1
    if method_upper == "DELETE":
        return 3
    if method_upper in ("POST", "PUT", "PATCH"):
        return 2
    return 1


def _enforce_permission(current_user: User, section: str, min_level: int) -> None:
    role = getattr(current_user, "role", None)
    if not role or not role.permissions:
        user_level = 0
    else:
        effective_permissions = (
            role.get_effective_permissions()
            if hasattr(role, "get_effective_permissions")
            else role.permissions
        )
        user_level = effective_permissions.get(section, 0)

    if user_level < min_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied for {section} (required: {min_level}, user: {user_level})",
        )


def require_section_access(
    section: str,
    skip_path_contains: tuple = (),
):
    """
    Router-level RBAC: infer permission level from HTTP method and path.
    Use skip_path_contains for self-service routes (e.g. /users/me).
    """

    def dependency(
        request: Request,
        current_user: User = Depends(get_current_user),
    ):
        path = request.url.path
        for fragment in skip_path_contains:
            if fragment in path:
                return True
        min_level = _resolve_min_level(request.method, path)
        _enforce_permission(current_user, section, min_level)
        return True

    return dependency


def require_permission(section: str, min_level: int):
    """
    Dependency FastAPI per RBAC basato su ruolo.
    section: nome della sezione (es: 'assets', 'vulnerabilities', ...)
    min_level: livello minimo richiesto (0=none, 1=read, 2=write, 3=delete, 4=bulk)
    """
    def dependency(current_user: User = Depends(get_current_user)):
        _enforce_permission(current_user, section, min_level)
        return True
    return dependency


def check_permission(user: User, section: str, min_level: int = 1) -> bool:
    """
    Utility function per verificare permessi programmaticamente.
    
    Args:
        user: L'utente di cui verificare i permessi
        section: La sezione di permesso da verificare
        min_level: Il livello minimo richiesto (default: 1 = read)
    
    Returns:
        True se l'utente ha il permesso richiesto, False altrimenti
    """
    role = getattr(user, "role", None)
    if not role or not role.permissions:
        return False
    
    effective_permissions = role.get_effective_permissions() if hasattr(role, 'get_effective_permissions') else role.permissions
    user_level = effective_permissions.get(section, 0)
    return user_level >= min_level


def get_user_permission_level(user: User, section: str) -> int:
    """
    Ottiene il livello di permesso dell'utente per una sezione specifica.
    
    Args:
        user: L'utente di cui ottenere i permessi
        section: La sezione di permesso
    
    Returns:
        Il livello di permesso (0-4) o 0 se non ha permessi
    """
    role = getattr(user, "role", None)
    if not role or not role.permissions:
        return 0
    
    effective_permissions = role.get_effective_permissions() if hasattr(role, 'get_effective_permissions') else role.permissions
    return effective_permissions.get(section, 0)
