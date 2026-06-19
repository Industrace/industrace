"""Per-tenant feature flags (stored in tenant.settings JSON)."""
from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.tenant import Tenant

FEATURE_IEC62443 = "iec62443"


def get_tenant_features(settings: Optional[Dict[str, Any]] = None) -> Dict[str, bool]:
    """Return resolved feature flags. Missing keys default to enabled (backward compatible)."""
    settings = settings or {}
    features = settings.get("features") or {}
    return {
        FEATURE_IEC62443: bool(features.get(FEATURE_IEC62443, True)),
    }


def is_iec62443_enabled(tenant: Optional[Tenant]) -> bool:
    if not tenant:
        return True
    return get_tenant_features(tenant.settings).get(FEATURE_IEC62443, True)


def is_iec62443_enabled_for_tenant_id(db: Session, tenant_id: UUID) -> bool:
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    return is_iec62443_enabled(tenant)


def set_feature(settings: Optional[Dict[str, Any]], feature: str, enabled: bool) -> Dict[str, Any]:
    updated = dict(settings or {})
    features = dict(updated.get("features") or {})
    features[feature] = enabled
    updated["features"] = features
    return updated


def set_iec62443_enabled(settings: Optional[Dict[str, Any]], enabled: bool) -> Dict[str, Any]:
    return set_feature(settings, FEATURE_IEC62443, enabled)
