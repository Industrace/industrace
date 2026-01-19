import uuid
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Role


def seed_roles(tenant_id=None):
    db: Session = SessionLocal()
    base_roles = [
        {
            "name": "admin",
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
                "evidence": 3,
                "notifications": 3,
                "sso": 3,
                "api_keys": 3,
            },
        },
        {
            "name": "editor",
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
                "evidence": 2,
                "notifications": 2,
                "sso": 1,
                "api_keys": 1,
            },
        },
        {
            "name": "viewer",
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
                "evidence": 1,
                "notifications": 1,
                "sso": 0,
                "api_keys": 0,
            },
        },
    ]
    for role_data in base_roles:
        role = db.query(Role).filter_by(name=role_data["name"], tenant_id=tenant_id).first()
        if not role:
            new_role = Role(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                name=role_data["name"],
                permissions=role_data["permissions"],
            )
            db.add(new_role)
            # print(f"Role {role_data['name']} created.")
        else:
            # Update existing role with new permissions
            # Merge existing permissions with new ones to avoid removing custom permissions
            updated_permissions = role.permissions.copy() if role.permissions else {}
            updated_permissions.update(role_data["permissions"])
            role.permissions = updated_permissions
            db.add(role)
            # print(f"Role {role_data['name']} updated with new permissions.")
    db.commit()
    db.close()


if __name__ == "__main__":
    seed_roles()
