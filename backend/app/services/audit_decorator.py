# backend/services/audit_decorator.py
import asyncio
import logging
from functools import wraps
from typing import Optional
from fastapi import Request
from app.services.audit_log import (
    create_audit_log,
    clean_dict,
    resolve_audit_language,
)

logger = logging.getLogger(__name__)

ENTITY_ID_KWARGS = {
    "NetworkProbe": "probe_id",
    "DiscoveredDevice": "device_id",
}

ACTIONS_WITH_OLD_DATA = frozenset(
    {
        "update",
        "delete",
        "deauthorize",
        "soft_delete",
        "hard_delete",
        "restore",
    }
)


def get_client_ip(request: Request) -> Optional[str]:
    if not request:
        return None
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def _extract_entity_id(entity: str, kwargs, result=None):
    alias_key = ENTITY_ID_KWARGS.get(entity)
    entity_id = None
    if alias_key:
        entity_id = kwargs.get(alias_key)
    if not entity_id:
        entity_id = (
            kwargs.get(f"{entity.lower()}_id")
            or kwargs.get("entity_id")
            or kwargs.get("id")
        )
    if not entity_id and result is not None and hasattr(result, "id"):
        entity_id = result.id
    return entity_id


def _capture_old_data(action, entity, model_class, kwargs, result=None):
    if action not in ACTIONS_WITH_OLD_DATA:
        return None

    db = kwargs.get("db")
    if not db or not model_class:
        return None

    entity_id = _extract_entity_id(entity, kwargs, result)
    if not entity_id:
        return None

    query = db.query(model_class).filter(model_class.id == entity_id)
    current_user = kwargs.get("current_user")
    if current_user and hasattr(model_class, "tenant_id"):
        query = query.filter(model_class.tenant_id == current_user.tenant_id)

    obj = query.first()
    if not obj:
        return None
    return clean_dict(obj)


def _extract_new_data(action, result):
    if action not in ("create", "update") or result is None:
        return None

    if hasattr(result, "_sa_instance_state"):
        return clean_dict(result)
    if hasattr(result, "__dict__") and not isinstance(result, dict):
        return clean_dict(result.__dict__)
    if isinstance(result, dict):
        return clean_dict(result)
    try:
        if hasattr(result, "model_dump"):
            return clean_dict(result.model_dump())
        if hasattr(result, "dict"):
            return clean_dict(result.dict())
    except Exception:
        pass
    return clean_dict(str(result))


def _write_audit_log(action, entity, model_class, result, kwargs, old_data=None):
    db = kwargs.get("db")
    current_user = kwargs.get("current_user")
    request: Request = kwargs.get("request")

    if not db or not current_user:
        return

    try:
        ip_address = get_client_ip(request)
        entity_id = _extract_entity_id(entity, kwargs, result)
        new_data = _extract_new_data(action, result)
        language = resolve_audit_language(current_user, request)

        create_audit_log(
            db=db,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            action=action,
            entity=entity,
            entity_id=entity_id,
            old_data=old_data,
            new_data=new_data,
            ip_address=ip_address,
            commit=True,
            language=language,
        )
    except Exception:
        logger.exception(
            "Failed to write audit log for action=%s entity=%s",
            action,
            entity,
        )


def audit_log_action(action: str, entity: str, model_class=None):
    """
    Decorator per aggiungere audit logging agli endpoint.

    L'endpoint deve avere parametri: db, current_user, request, e opzionalmente entity_id (es. asset_id)
    """

    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                old_data = _capture_old_data(action, entity, model_class, kwargs)
                result = await func(*args, **kwargs)
                _write_audit_log(action, entity, model_class, result, kwargs, old_data)
                return result

            return async_wrapper

        @wraps(func)
        def wrapper(*args, **kwargs):
            old_data = _capture_old_data(action, entity, model_class, kwargs)
            result = func(*args, **kwargs)
            _write_audit_log(action, entity, model_class, result, kwargs, old_data)
            return result

        return wrapper

    return decorator
