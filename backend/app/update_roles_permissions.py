import uuid
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Role


def update_roles_permissions():
    """
    Update existing roles permissions with newly added permissions.
    This script updates all roles for all tenants.
    """
    db: Session = SessionLocal()
    
    # Definition of new permissions for each role
    new_permissions = {
        "admin": {
            "reset_user_password": 1,
            "vulnerabilities": 3,
            "asset_reviews": 3,
            "asset_dependencies": 3,
            "compliance": 3,
            "security_zones": 3,
            "notifications": 3,
            "sso": 3,
        },
        "editor": {
            "vulnerabilities": 2,
            "asset_reviews": 2,
            "asset_dependencies": 2,
            "compliance": 1,
            "security_zones": 2,
            "notifications": 2,
            "sso": 1,
        },
        "viewer": {
            "vulnerabilities": 1,
            "asset_reviews": 1,
            "asset_dependencies": 1,
            "compliance": 1,
            "security_zones": 1,
            "notifications": 1,
            "sso": 0,
        },
    }
    
    try:
        # Update all roles for all tenants
        roles = db.query(Role).all()
        updated_count = 0
        
        for role in roles:
            role_permissions = new_permissions.get(role.name, {})
            updated = False
            
            if role_permissions:
                # Ensure permissions is a dictionary
                if role.permissions is None:
                    role.permissions = {}
                
                # Add or update missing permissions
                for perm_name, perm_level in role_permissions.items():
                    if perm_name not in role.permissions:
                        role.permissions[perm_name] = perm_level
                        updated = True
                        print(f"✅ Updated role '{role.name}' (tenant: {role.tenant_id}): added permission '{perm_name}' = {perm_level}")
            
            if updated:
                updated_count += 1
        
        if updated_count > 0:
            db.commit()
            print(f"\n✅ Updated {updated_count} roles with new permissions!")
        else:
            print("\nℹ️  All roles already have updated permissions.")
            
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error during permissions update: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    update_roles_permissions() 