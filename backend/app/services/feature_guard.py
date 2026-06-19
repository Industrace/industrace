from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Tenant
from app.services.auth import get_current_user
from app.services.tenant_features import is_iec62443_enabled
from app.errors.exceptions import ErrorCodeException
from app.errors.error_codes import ErrorCode


async def require_iec62443_enabled(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    if not is_iec62443_enabled(tenant):
        raise ErrorCodeException(
            status_code=403,
            error_code=ErrorCode.FEATURE_DISABLED,
            detail="Il modulo ISA/IEC 62443 non è abilitato per questo tenant",
        )
