from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.models import Tenant, User, Role
from app.schemas.setup import SetupStatus, SetupRequest, SetupResponse
from app.services.auth import get_password_hash
from app.services.init_tenant_roles import init_tenant_roles, get_default_admin_role_id
from app.init_print_template import init_default_templates
from app.init_manufacturers import seed_manufacturers
from app.init_asset_statuses import setup_asset_statuses
from app.init_asset_types import setup_asset_types
from app.init_data.init_notification_templates import init_notification_templates
from app.init_data.init_security_requirements import init_security_requirements
from app.services.tenant_features import set_iec62443_enabled
from app.services.setup_auth import verify_setup_token
from app.config import settings
import uuid

router = APIRouter(prefix="/setup", tags=["setup"])


def _is_system_configured(db: Session) -> bool:
    return (
        db.query(Tenant).count() > 0
        and db.query(User).count() > 0
        and db.query(Role).count() > 0
    )


@router.get("/status", response_model=SetupStatus)
def get_setup_status(db: Session = Depends(get_db)):
    """Verifica se il sistema è già configurato"""
    try:
        tenant_count = db.query(Tenant).count()
        user_count = db.query(User).count()
        role_count = db.query(Role).count()
        is_configured = tenant_count > 0 and user_count > 0 and role_count > 0

        if settings.ENVIRONMENT == "production" and is_configured:
            return SetupStatus(
                is_configured=True,
                tenant_count=0,
                user_count=0,
                role_count=0,
                database_connected=True,
            )

        return SetupStatus(
            is_configured=is_configured,
            tenant_count=tenant_count,
            user_count=user_count,
            role_count=role_count,
            database_connected=True,
        )
    except Exception as e:
        if settings.ENVIRONMENT == "production":
            return SetupStatus(
                is_configured=False,
                tenant_count=0,
                user_count=0,
                role_count=0,
                database_connected=False,
            )
        return SetupStatus(
            is_configured=False,
            tenant_count=0,
            user_count=0,
            role_count=0,
            database_connected=False,
            error=str(e),
        )


@router.post("/initialize", response_model=SetupResponse)
def initialize_system(
    setup_data: SetupRequest,
    db: Session = Depends(get_db),
    _: None = Depends(verify_setup_token),
):
    """Inizializza il sistema con i dati forniti"""
    try:
        if _is_system_configured(db):
            raise HTTPException(status_code=400, detail="System already configured")

        tenant = Tenant(
            id=uuid.uuid4(),
            name=setup_data.tenant_name,
            slug=setup_data.tenant_slug,
            settings=set_iec62443_enabled(
                {"theme": "industrial", "language": setup_data.language},
                setup_data.iec62443_enabled,
            ),
        )
        db.add(tenant)
        db.flush()

        init_tenant_roles(tenant.id, db)
        admin_role_id = get_default_admin_role_id(tenant.id, db)

        admin_user = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            email=setup_data.admin_email,
            password_hash=get_password_hash(setup_data.admin_password),
            name=setup_data.admin_name,
            role_id=admin_role_id,
            is_active=True,
        )
        db.add(admin_user)

        init_default_templates(tenant_id=tenant.id)
        init_notification_templates(db)
        init_security_requirements(db)
        seed_manufacturers()
        setup_asset_statuses()
        setup_asset_types()

        db.commit()

        return SetupResponse(
            success=True,
            message="System initialized successfully",
            tenant_id=str(tenant.id),
            admin_user_id=str(admin_user.id),
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Setup failed: {str(e)}")


@router.post("/test-database")
def test_database_connection(
    db: Session = Depends(get_db),
    _: None = Depends(verify_setup_token),
):
    """Testa la connessione al database"""
    if _is_system_configured(db):
        raise HTTPException(status_code=403, detail="System already configured")
    try:
        db.execute(text("SELECT 1"))
        return {"status": "connected", "message": "Database connection successful"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")
