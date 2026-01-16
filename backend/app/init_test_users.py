import uuid
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User, Role
from app.services.auth import get_password_hash


def seed_test_users():
    db: Session = SessionLocal()

    # Get existing roles
    admin_role = db.query(Role).filter_by(name="admin").first()
    editor_role = db.query(Role).filter_by(name="editor").first()
    viewer_role = db.query(Role).filter_by(name="viewer").first()

    if not admin_role or not editor_role or not viewer_role:
        # print(
        #     "Error: The admin, editor and viewer roles must be created before the test users."
        # )
        return

    # Get the first available tenant or create a test tenant
    from app.models import Tenant

    tenant = db.query(Tenant).first()
    if not tenant:
        # Create a test tenant if none exists
        tenant = Tenant(id=uuid.uuid4(), name="Test Tenant", domain="test.local")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        # print(f"Test tenant created: {tenant.name}")

    tenant_id = tenant.id

    test_users = [
        {
            "name": "Admin Test",
            "email": "admin@test.com",
            "password": "admin123",
            "role": admin_role,
            "is_active": True,
        },
        {
            "name": "Editor Test",
            "email": "editor@test.com",
            "password": "editor123",
            "role": editor_role,
            "is_active": True,
        },
        {
            "name": "Viewer Test",
            "email": "viewer@test.com",
            "password": "viewer123",
            "role": viewer_role,
            "is_active": True,
        },
        {
            "name": "Limited Editor",
            "email": "editor.limited@test.com",
            "password": "limited123",
            "role": editor_role,
            "is_active": True,
        },
    ]

    for user_data in test_users:
        existing_user = db.query(User).filter_by(email=user_data["email"]).first()
        if not existing_user:
            new_user = User(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                email=user_data["email"],
                password_hash=get_password_hash(user_data["password"]),
                name=user_data["name"],
                role_id=user_data["role"].id,
                is_active=user_data["is_active"],
                password_change_required=True,  # Force password change on first login
            )
            db.add(new_user)
            # print(
            #     f"User {user_data['email']} created with role {user_data['role'].name}."
            # )
        else:
            # print(f"User {user_data['email']} already exists.")
            pass

    db.commit()
    db.close()

    # print("\n=== Test user credentials ===")
    # print("Admin: admin@test.com / admin123")
    # print("Editor: editor@test.com / editor123")
    # print("Viewer: viewer@test.com / viewer123")
    # print("Limited Editor: editor.limited@test.com / limited123")
    # print("=====================================")


if __name__ == "__main__":
    seed_test_users()
