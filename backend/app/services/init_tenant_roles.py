import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Role


def init_tenant_roles(tenant_id: uuid.UUID, db: Session = None):
    """
    Initialize default roles for a specific tenant
    
    Args:
        tenant_id: ID of the tenant for which to create roles
        db: Database session (optional, creates a new one if not provided)
    """
    should_close_db = False
    if db is None:
        db = SessionLocal()
        should_close_db = True
    
    try:
        base_roles = [
            {
                "name": "admin",
                "description": "Amministratore del sistema con accesso completo",
                "permissions": {
                    "assets": 3,
                    "sites": 3,
                    "areas": 3,
                    "locations": 3,
                    "suppliers": 3,
                    "contacts": 3,
                    "manufacturers": 3,
                    "asset_types": 3,
                    "asset_statuses": 3,
                    "users": 3,
                    "roles": 3,
                    "audit_logs": 3,
                    "utility": 3,
                    "asset_documents": 3,
                    "asset_photos": 3,
                    "locations_floormap": 3,
                    "reset_user_password": 1,
                    "vulnerabilities": 3,
                    "asset_reviews": 3,
                    "asset_dependencies": 3,
                    "compliance": 3,
                    "security_zones": 3,
                    "notifications": 3,
                    "sso": 3,
                },
                "is_inheritable": True,
                "is_active": True
            },
            {
                "name": "editor",
                "description": "Editor con permessi di modifica limitati",
                "permissions": {
                    "assets": 2,
                    "sites": 2,
                    "areas": 2,
                    "locations": 2,
                    "suppliers": 2,
                    "contacts": 2,
                    "manufacturers": 2,
                    "asset_types": 2,
                    "asset_statuses": 2,
                    "users": 1,
                    "roles": 1,
                    "audit_logs": 1,
                    "utility": 2,
                    "asset_documents": 2,
                    "asset_photos": 2,
                    "locations_floormap": 2,
                    "vulnerabilities": 2,
                    "asset_reviews": 2,
                    "asset_dependencies": 2,
                    "compliance": 1,
                    "security_zones": 2,
                    "notifications": 2,
                    "sso": 1,
                },
                "is_inheritable": True,
                "is_active": True
            },
            {
                "name": "viewer",
                "description": "Visualizzatore con accesso in sola lettura",
                "permissions": {
                    "assets": 1,
                    "sites": 1,
                    "areas": 1,
                    "locations": 1,
                    "suppliers": 1,
                    "contacts": 1,
                    "manufacturers": 1,
                    "asset_types": 1,
                    "asset_statuses": 1,
                    "users": 0,
                    "roles": 1,
                    "audit_logs": 1,
                    "utility": 1,
                    "asset_documents": 1,
                    "asset_photos": 1,
                    "locations_floormap": 1,
                    "vulnerabilities": 1,
                    "asset_reviews": 1,
                    "asset_dependencies": 1,
                    "compliance": 1,
                    "security_zones": 1,
                    "notifications": 1,
                    "sso": 0,
                },
                "is_inheritable": True,
                "is_active": True
            },
        ]
        
        created_roles = []
        for role_data in base_roles:
            # Check if role already exists for this tenant
            existing_role = db.query(Role).filter_by(
                name=role_data["name"], 
                tenant_id=tenant_id
            ).first()
            
            if not existing_role:
                new_role = Role(
                    id=uuid.uuid4(),
                    tenant_id=tenant_id,
                    name=role_data["name"],
                    description=role_data["description"],
                    permissions=role_data["permissions"],
                    is_inheritable=role_data["is_inheritable"],
                    is_active=role_data["is_active"],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(new_role)
                created_roles.append(role_data["name"])
                # print(f"✅ Ruolo {role_data['name']} creato per tenant {tenant_id}")
            else:
                # print(f"ℹ️  Role {role_data['name']} already exists for tenant {tenant_id}")
                pass
        
        if created_roles:
            db.commit()
            # print(f"✅ Ruoli creati per tenant {tenant_id}: {', '.join(created_roles)}")
        else:
            # print(f"ℹ️  Nessun nuovo ruolo creato per tenant {tenant_id}")
            pass
            
        return created_roles
        
    except Exception as e:
        db.rollback()
        # print(f"❌ Errore durante la creazione dei ruoli per tenant {tenant_id}: {e}")
        raise
    finally:
        if should_close_db:
            db.close()


def get_default_admin_role_id(tenant_id: uuid.UUID, db: Session = None) -> uuid.UUID:
    """
    Ottiene l'ID del ruolo admin per un tenant specifico
    
    Args:
        tenant_id: ID del tenant
        db: Sessione database (opzionale)
        
    Returns:
        ID del ruolo admin
    """
    should_close_db = False
    if db is None:
        db = SessionLocal()
        should_close_db = True
    
    try:
        admin_role = db.query(Role).filter_by(
            name="admin", 
            tenant_id=tenant_id
        ).first()
        
        if admin_role:
            return admin_role.id
        else:
            raise ValueError(f"Ruolo admin non trovato per tenant {tenant_id}")
    finally:
        if should_close_db:
            db.close()


if __name__ == "__main__":
    # Test della funzione
    test_tenant_id = uuid.uuid4()
    # print(f"Test creazione ruoli per tenant: {test_tenant_id}")
    init_tenant_roles(test_tenant_id) 