# backend/services/audit_decorator.py
import asyncio
from functools import wraps
from typing import Optional
from fastapi import Request
from app.services.audit_log import (
    create_audit_log,
    clean_dict,
    create_readable_description,
    get_entity_name_by_id,
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


def _write_audit_log(action, entity, model_class, result, kwargs):
    db = kwargs.get("db")
    current_user = kwargs.get("current_user")
    request: Request = kwargs.get("request")

    ip_address = get_client_ip(request)

    entity_id = (
        kwargs.get(f"{entity.lower()}_id")
        or kwargs.get("entity_id")
        or kwargs.get("id")
    )

    old_data = None
    if action in ("update", "delete") and entity_id and db and model_class:
        obj = db.query(model_class).filter(model_class.id == entity_id).first()
        if obj:
            old_data = clean_dict(obj.__dict__)

    new_data = None
    if action in ("create", "update") and result:
        if hasattr(result, '_sa_instance_state'):
            new_data = clean_dict(result)
        elif hasattr(result, "__dict__"):
            new_data = clean_dict(result.__dict__)
        elif isinstance(result, dict):
            new_data = clean_dict(result)
        else:
            try:
                if hasattr(result, 'model_dump'):
                    new_data = clean_dict(result.model_dump())
                elif hasattr(result, 'dict'):
                    new_data = clean_dict(result.dict())
                else:
                    new_data = clean_dict(str(result))
            except Exception:
                new_data = clean_dict(str(result))

    if not entity_id and result and hasattr(result, "id"):
        entity_id = result.id

    entity_name = None
    if entity_id and db and current_user:
        entity_name = get_entity_name_by_id(
            db, entity, entity_id, current_user.tenant_id
        )

    description = create_readable_description(
        action, entity, entity_id, entity_name, old_data, new_data
    )

    if db and current_user:
        create_audit_log(
            db=db,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            action=action,
            entity=entity,
            entity_id=entity_id,
            old_data=old_data,
            new_data=new_data,
            description=description,
            ip_address=ip_address,
            commit=True,
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
                result = await func(*args, **kwargs)
                _write_audit_log(action, entity, model_class, result, kwargs)
                return result

            return async_wrapper

        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            _write_audit_log(action, entity, model_class, result, kwargs)
            return result

        return wrapper

    return decorator
