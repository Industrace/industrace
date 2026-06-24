# backend/services/api_auth.py
import secrets
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import Depends, HTTPException, status, Header, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.api_key import ApiKey
from app.models.tenant import Tenant
from app.config import settings
from app.services.audit_log import create_audit_log, resolve_audit_language


def generate_api_key() -> str:
    """Genera una nuova API Key sicura"""
    random_bytes = secrets.token_bytes(settings.API_KEY_LENGTH)
    return f"{settings.API_KEY_PREFIX}{secrets.token_urlsafe(settings.API_KEY_LENGTH)}"


def hash_api_key(key: str) -> str:
    """Crea l'hash dell'API Key per il salvataggio sicuro"""
    return hashlib.sha256(key.encode()).hexdigest()


def verify_api_key(key: str, key_hash: str) -> bool:
    """Verifica che l'API Key corrisponda all'hash salvato"""
    return hash_api_key(key) == key_hash


async def get_api_key_user(
    request: Request,
    x_api_key: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> Optional[ApiKey]:
    """
    Dependency per autenticare le API Keys esterne.
    Restituisce l'API Key se valida, altrimenti None.
    """
    if not x_api_key:
        return None

    # Cerca l'API Key nel database
    key_hash = hash_api_key(x_api_key)
    api_key = (
        db.query(ApiKey)
        .filter(ApiKey.key_hash == key_hash, ApiKey.is_active == True)
        .first()
    )

    if not api_key:
        return None

    # Verifica scadenza
    if api_key.expires_at and api_key.expires_at < datetime.utcnow():
        return None

    # Aggiorna last_used_at
    api_key.last_used_at = datetime.utcnow()
    db.commit()

    # Log dell'uso dell'API Key
    ip_address = request.client.host if request.client else None

    create_audit_log(
        db=db,
        user_id=api_key.created_by,
        tenant_id=api_key.tenant_id,
        action="api_key_used",
        entity="ApiKey",
        entity_id=api_key.id,
        ip_address=ip_address,
        commit=False,
        language=resolve_audit_language(request=request),
    )

    return api_key


def require_api_key_scope(required_scopes: List[str]):
    """
    Dependency per verificare che l'API Key abbia i permessi necessari
    """

    def dependency(api_key: ApiKey = Depends(get_api_key_user)):
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="API Key richiesta"
            )

        # Parsing degli scopes
        try:
            api_scopes = (
                json.loads(api_key.scopes)
                if isinstance(api_key.scopes, str)
                else api_key.scopes
            )
        except (json.JSONDecodeError, TypeError):
            api_scopes = ["read"]

        # Verifica che l'API Key abbia tutti gli scopes richiesti
        for required_scope in required_scopes:
            if required_scope not in api_scopes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permesso '{required_scope}' richiesto ma non disponibile",
                )

        return api_key

    return dependency


def get_tenant_from_api_key(
    api_key: ApiKey = Depends(get_api_key_user),
) -> Optional[Tenant]:
    """Restituisce il tenant associato all'API Key"""
    if not api_key:
        return None
    return api_key.tenant


    # Alias for ease of use
require_read_scope = require_api_key_scope(["read"])
require_write_scope = require_api_key_scope(["read", "write"])
require_admin_scope = require_api_key_scope(["read", "write", "admin"])
