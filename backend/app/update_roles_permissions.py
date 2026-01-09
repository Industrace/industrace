import uuid
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Role


def update_roles_permissions():
    """
    Aggiorna i permessi dei ruoli esistenti con i nuovi permessi aggiunti.
    Questo script aggiorna tutti i ruoli di tutti i tenant.
    """
    db: Session = SessionLocal()
    
    # Definizione dei nuovi permessi per ogni ruolo
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
        # Aggiorna tutti i ruoli di tutti i tenant
        roles = db.query(Role).all()
        updated_count = 0
        
        for role in roles:
            role_permissions = new_permissions.get(role.name, {})
            updated = False
            
            if role_permissions:
                # Assicurati che permissions sia un dizionario
                if role.permissions is None:
                    role.permissions = {}
                
                # Aggiungi o aggiorna i permessi mancanti
                for perm_name, perm_level in role_permissions.items():
                    if perm_name not in role.permissions:
                        role.permissions[perm_name] = perm_level
                        updated = True
                        print(f"✅ Aggiornato ruolo '{role.name}' (tenant: {role.tenant_id}): aggiunto permesso '{perm_name}' = {perm_level}")
            
            if updated:
                updated_count += 1
        
        if updated_count > 0:
            db.commit()
            print(f"\n✅ Aggiornati {updated_count} ruoli con i nuovi permessi!")
        else:
            print("\nℹ️  Tutti i ruoli hanno già i permessi aggiornati.")
            
    except Exception as e:
        db.rollback()
        print(f"\n❌ Errore durante l'aggiornamento dei permessi: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    update_roles_permissions() 