from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
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
import uuid

router = APIRouter(prefix="/setup", tags=["setup"])


@router.get("/status", response_model=SetupStatus)
def get_setup_status(db: Session = Depends(get_db)):
    """Verifica se il sistema è già configurato"""
    try:
        # Controlla se esistono tenant
        tenant_count = db.query(Tenant).count()
        user_count = db.query(User).count()
        role_count = db.query(Role).count()
        
        is_configured = tenant_count > 0 and user_count > 0 and role_count > 0
        
        return SetupStatus(
            is_configured=is_configured,
            tenant_count=tenant_count,
            user_count=user_count,
            role_count=role_count,
            database_connected=True
        )
    except Exception as e:
        return SetupStatus(
            is_configured=False,
            tenant_count=0,
            user_count=0,
            role_count=0,
            database_connected=False,
            error=str(e)
        )


@router.post("/initialize", response_model=SetupResponse)
def initialize_system(setup_data: SetupRequest, db: Session = Depends(get_db)):
    """Inizializza il sistema con i dati forniti"""
    try:
        # Verify that the system is not already configured
        if db.query(Tenant).count() > 0:
            raise HTTPException(status_code=400, detail="System already configured")
        
        # 1. Crea il tenant
        tenant = Tenant(
            id=uuid.uuid4(),
            name=setup_data.tenant_name,
            slug=setup_data.tenant_slug,
            settings={"theme": "industrial", "language": setup_data.language}
        )
        db.add(tenant)
        db.flush()
        
        # 2. Crea i ruoli default per il tenant
        init_tenant_roles(tenant.id, db)
        
        # 3. Ottieni l'ID del ruolo admin
        admin_role_id = get_default_admin_role_id(tenant.id, db)
        
        # 4. Crea l'utente admin
        admin_user = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            email=setup_data.admin_email,
            password_hash=get_password_hash(setup_data.admin_password),
            name=setup_data.admin_name,
            role_id=admin_role_id,
            is_active=True
        )
        db.add(admin_user)
        
        # 4. Inizializza i dati di base
        init_default_templates(tenant_id=tenant.id)
        init_notification_templates(db)  # System-wide notification templates
        init_security_requirements(db)  # ISA/IEC 62443 Security Requirements (system-wide)
        seed_manufacturers()
        setup_asset_statuses()
        setup_asset_types()
        
        db.commit()
        
        return SetupResponse(
            success=True,
            message="System initialized successfully",
            tenant_id=str(tenant.id),
            admin_user_id=str(admin_user.id)
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Setup failed: {str(e)}")


@router.post("/test-database")
def test_database_connection(db: Session = Depends(get_db)):
    """Testa la connessione al database"""
    try:
        # Prova una query semplice
        db.execute("SELECT 1")
        return {"status": "connected", "message": "Database connection successful"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}") 