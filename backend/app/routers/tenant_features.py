from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Tenant
from app.schemas.tenant_features import TenantFeaturesRead, TenantFeaturesUpdate
from app.services.auth import get_current_user
from app.services.audit_decorator import audit_log_action
from app.services.rbac import require_permission
from app.services.tenant_features import get_tenant_features, set_iec62443_enabled

router = APIRouter(prefix="/tenant-features", tags=["tenant-features"])


@router.get("", response_model=TenantFeaturesRead)
def get_tenant_features_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    features = get_tenant_features(tenant.settings if tenant else None)
    return TenantFeaturesRead(iec62443=features["iec62443"])


@router.patch("", response_model=TenantFeaturesRead)
@audit_log_action("update", "TenantFeatures")
def update_tenant_features_config(
    update: TenantFeaturesUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    perm=Depends(require_permission("roles", 2)),
):
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    if not tenant:
        from app.errors.exceptions import ErrorCodeException
        from app.errors.error_codes import ErrorCode

        raise ErrorCodeException(status_code=404, error_code=ErrorCode.TENANT_NOT_FOUND)

    tenant.settings = set_iec62443_enabled(tenant.settings, update.iec62443)
    db.commit()
    db.refresh(tenant)
    features = get_tenant_features(tenant.settings)
    return TenantFeaturesRead(iec62443=features["iec62443"])
