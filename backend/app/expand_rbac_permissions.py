"""
Script per espandere i permessi RBAC con le nuove funzionalità

Questo script aggiorna tutti i ruoli esistenti (admin, editor, viewer) per tutti i tenant
aggiungendo i permessi per le nuove funzionalità:
- Vulnerabilità
- Asset Reviews
- Asset Dependencies
- Compliance ISA62443
- Security Zones
- Notifiche
- SSO
- API Keys
- Evidence

Uso:
    python -m app.expand_rbac_permissions
"""
import uuid
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Role
from app.services.rbac_permissions import (
    ADMIN_DEFAULT_PERMISSIONS,
    EDITOR_DEFAULT_PERMISSIONS,
    VIEWER_DEFAULT_PERMISSIONS
)


def expand_rbac_permissions():
    """
    Espande i permessi RBAC per tutti i ruoli esistenti
    aggiungendo le nuove sezioni per vulnerabilità, review, dipendenze, etc.
    """
    db: Session = SessionLocal()
    
    try:
        # Per ogni tenant nel sistema
        from app.models import Tenant
        tenants = db.query(Tenant).all()
        
        if not tenants:
            print("No tenants found in the system")
            return
        
        roles_to_update = [
            ("admin", ADMIN_DEFAULT_PERMISSIONS),
            ("editor", EDITOR_DEFAULT_PERMISSIONS),
            ("viewer", VIEWER_DEFAULT_PERMISSIONS)
        ]
        
        total_updated = 0
        
        for tenant in tenants:
            print(f"\nProcessing tenant: {tenant.name} (ID: {tenant.id})")
            
            for role_name, default_permissions in roles_to_update:
                role = db.query(Role).filter_by(
                    name=role_name,
                    tenant_id=tenant.id
                ).first()
                
                if role:
                    # Aggiorna i permessi mantenendo quelli esistenti e aggiungendo i nuovi
                    updated_permissions = role.permissions.copy() if role.permissions else {}
                    
                    # Aggiungi/aggiorna le nuove sezioni
                    new_sections_added = []
                    for section, level in default_permissions.items():
                        # Se la sezione non esiste o è una nuova sezione, aggiorna
                        is_new_section = section in [
                            "vulnerabilities", "asset_reviews", "asset_dependencies",
                            "compliance", "security_zones", "notifications", "sso",
                            "api_keys", "evidence"
                        ]
                        
                        if section not in updated_permissions or is_new_section:
                            old_level = updated_permissions.get(section, 0)
                            updated_permissions[section] = level
                            if is_new_section and old_level != level:
                                new_sections_added.append(f"{section}:{old_level}->{level}")
                    
                    role.permissions = updated_permissions
                    
                    if new_sections_added:
                        print(f"  ✓ Updated {role_name} role: {', '.join(new_sections_added)}")
                        total_updated += 1
                    else:
                        print(f"  - {role_name} role already up to date")
                else:
                    print(f"  ⚠ Role {role_name} not found for tenant {tenant.name}")
        
        db.commit()
        print(f"\n✓ RBAC permissions expansion completed! Updated {total_updated} roles across {len(tenants)} tenants")
        
    except Exception as e:
        db.rollback()
        print(f"✗ Error expanding RBAC permissions: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    expand_rbac_permissions()
