import json
import logging
import threading
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models.sso_oauth_state import SsoOAuthState

logger = logging.getLogger(__name__)

SSO_STATE_TTL_SECONDS = 600
SSO_STATE_KEY_PREFIX = "sso:oauth:state:"

_redis_client = None
_redis_available = False
_memory_lock = threading.Lock()
_memory_store: dict[str, dict] = {}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _get_redis():
    global _redis_client, _redis_available

    if not settings.REDIS_ENABLED:
        return None

    if _redis_client is not None:
        return _redis_client if _redis_available else None

    try:
        from redis import Redis
        from redis.exceptions import ConnectionError as RedisConnectionError

        _redis_client = Redis.from_url(
            settings.REDIS_URL,
            decode_responses=False,
            socket_connect_timeout=2,
            socket_timeout=2,
            retry_on_timeout=True,
        )
        _redis_client.ping()
        _redis_available = True
        logger.info("Redis connected for SSO OAuth state storage")
        return _redis_client
    except Exception as exc:
        logger.warning(
            "Redis unavailable for SSO OAuth state storage: %s. Using database fallback.",
            exc,
        )
        _redis_available = False
        _redis_client = None
        return None


def _purge_expired_db_states(db: Session) -> None:
    db.query(SsoOAuthState).filter(SsoOAuthState.expires_at <= _utcnow()).delete(
        synchronize_session=False
    )


def _store_in_db(
    db: Session, state: str, code_verifier: str, tenant_id: uuid.UUID
) -> None:
    _purge_expired_db_states(db)
    db.merge(
        SsoOAuthState(
            state=state,
            code_verifier=code_verifier,
            tenant_id=tenant_id,
            expires_at=_utcnow() + timedelta(seconds=SSO_STATE_TTL_SECONDS),
        )
    )
    db.commit()


def _consume_from_db(db: Session, state: str) -> Optional[dict]:
    row = (
        db.query(SsoOAuthState)
        .filter(SsoOAuthState.state == state, SsoOAuthState.expires_at > _utcnow())
        .first()
    )
    if not row:
        return None

    payload = {
        "code_verifier": row.code_verifier,
        "tenant_id": str(row.tenant_id),
    }
    db.delete(row)
    db.commit()
    return payload


def _purge_expired_memory_states(now: float) -> None:
    expired = [
        key for key, value in _memory_store.items() if value["expires_at"] <= now
    ]
    for key in expired:
        _memory_store.pop(key, None)


def _store_in_memory(state: str, code_verifier: str, tenant_id: uuid.UUID) -> None:
    now = _utcnow().timestamp()
    with _memory_lock:
        _purge_expired_memory_states(now)
        _memory_store[state] = {
            "code_verifier": code_verifier,
            "tenant_id": str(tenant_id),
            "expires_at": now + SSO_STATE_TTL_SECONDS,
        }


def _consume_from_memory(state: str) -> Optional[dict]:
    now = _utcnow().timestamp()
    with _memory_lock:
        row = _memory_store.pop(state, None)
        if not row or row["expires_at"] <= now:
            return None
        return {
            "code_verifier": row["code_verifier"],
            "tenant_id": row["tenant_id"],
        }


def store_sso_state(
    state: str,
    code_verifier: str,
    tenant_id: uuid.UUID,
    db: Optional[Session] = None,
) -> None:
    redis = _get_redis()
    if redis:
        payload = json.dumps(
            {"code_verifier": code_verifier, "tenant_id": str(tenant_id)}
        )
        redis.setex(
            f"{SSO_STATE_KEY_PREFIX}{state}",
            SSO_STATE_TTL_SECONDS,
            payload.encode(),
        )
        return

    if db is not None:
        _store_in_db(db, state, code_verifier, tenant_id)
        return

    logger.warning(
        "SSO OAuth state stored in process memory; use Redis or database in production."
    )
    _store_in_memory(state, code_verifier, tenant_id)


def consume_sso_state(state: str, db: Optional[Session] = None) -> Optional[dict]:
    redis = _get_redis()
    if redis:
        key = f"{SSO_STATE_KEY_PREFIX}{state}"
        raw = redis.getdel(key) if hasattr(redis, "getdel") else None
        if raw is None:
            pipe = redis.pipeline()
            pipe.get(key)
            pipe.delete(key)
            results = pipe.execute()
            raw = results[0]

        if raw:
            if isinstance(raw, bytes):
                raw = raw.decode()
            return json.loads(raw)

        if db is not None:
            return _consume_from_db(db, state)
        return _consume_from_memory(state)

    if db is not None:
        payload = _consume_from_db(db, state)
        if payload:
            return payload

    return _consume_from_memory(state)
