import uuid
from app.database import SessionLocal
from app.models import Tenant, User, Role
from app.services.auth import get_password_hash
from app.init_roles import seed_roles
from app.init_print_template import init_default_templates
from app.init_manufacturers import seed_manufacturers
from app.init_asset_statuses import setup_asset_statuses
from app.init_asset_types import setup_asset_types
from app.init_data.init_notification_templates import init_notification_templates
from app.init_data.init_security_requirements import init_security_requirements
from app.init_data.init_security_capabilities import init_security_capabilities
from app.init_data.init_sr_capability_mappings import init_sr_capability_mappings

ADMIN_EMAIL = "admin@example.com"
EDITOR_EMAIL = "editor@example.com"
VIEWER_EMAIL = "viewer@example.com"
ADMIN_PASSWORD = "Admin@123456!"
EDITOR_PASSWORD = "Editor@123456!"
VIEWER_PASSWORD = "Viewer@123456!"
TENANT_NAME = "Default Tenant"
TENANT_SLUG = "default-tenant"


def setup_system():
    db = SessionLocal()
    # 1. Tenant
    tenant = db.query(Tenant).filter_by(slug=TENANT_SLUG).first()
    if not tenant:
        tenant = Tenant(
            id=uuid.uuid4(), name=TENANT_NAME, slug=TENANT_SLUG, settings={}
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        # print(f"Tenant created: {TENANT_NAME}")
    else:
        # print(f"Tenant already exists: {TENANT_NAME}")
        pass
    tenant_id = tenant.id

    # 2. Roles
    seed_roles(tenant_id=tenant_id)
    roles = {r.name: r for r in db.query(Role).filter_by(tenant_id=tenant_id).all()}

    # 3. Base users
    users = [
        {
            "name": "Admin",
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
            "role": "admin",
        },
        {
            "name": "Editor",
            "email": EDITOR_EMAIL,
            "password": EDITOR_PASSWORD,
            "role": "editor",
        },
        {
            "name": "Viewer",
            "email": VIEWER_EMAIL,
            "password": VIEWER_PASSWORD,
            "role": "viewer",
        },
    ]
    for u in users:
        existing = db.query(User).filter_by(email=u["email"]).first()
        if not existing:
            user = User(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                email=u["email"],
                password_hash=get_password_hash(u["password"]),
                name=u["name"],
                role_id=roles[u["role"]].id,
                is_active=True,
                password_change_required=False,  # Passwords are now secure by default
            )
            db.add(user)
            # print(f"User created: {u['email']} ({u['role']})")
        else:
            # print(f"User already exists: {u['email']}")
            pass
    db.commit()

    # 4. Print templates
    init_default_templates(tenant_id=tenant_id)

    # 5. Notification templates (system-wide)
    try:
        init_notification_templates(db)
    except Exception as e:
        print(f"⚠️  Notification templates initialization failed: {e}")

    # 6. Manufacturers ICS/OT
    seed_manufacturers(tenant_id=tenant_id)

    # 7. Asset types and statuses
    setup_asset_statuses(tenant_id=tenant_id)
    setup_asset_types(tenant_id=tenant_id)
    
    # 8. ISA/IEC 62443 Security Requirements (system-wide)
    try:
        init_security_requirements(db)
    except Exception as e:
        print(f"⚠️  Security Requirements initialization failed: {e}")

    # 9. ISA/IEC 62443 Security Capabilities (system-wide)
    try:
        init_security_capabilities(db)
    except Exception as e:
        print(f"⚠️  Security Capabilities initialization failed: {e}")

    # 10. ISA/IEC 62443 SR-Capability Mappings (system-wide)
    try:
        init_sr_capability_mappings(db)
    except Exception as e:
        print(f"⚠️  SR-Capability mappings initialization failed: {e}")

    # Add demo data if in development environment
    from app.config import settings
    if settings.ENVIRONMENT == "development":
        try:
            from app.init_demo_data import seed_demo_data
            seed_demo_data()
        except Exception as e:
            print(f"⚠️  Demo data seeding failed: {e}")

    db.close()
    
    # Print credentials at the end
    print("\n" + "="*60)
    print("✅ SYSTEM INITIALIZATION COMPLETED")
    print("="*60)
    print("\n🔐 Default Login Credentials:")
    print(f"   Admin:  {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
    print(f"   Editor: {EDITOR_EMAIL} / {EDITOR_PASSWORD}")
    print(f"   Viewer: {VIEWER_EMAIL} / {VIEWER_PASSWORD}")
    print("\n⚠️  IMPORTANT: Change these passwords immediately!")
    print("="*60 + "\n")


if __name__ == "__main__":
    setup_system()
