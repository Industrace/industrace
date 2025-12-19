# backend/app/reset_security_requirements.py

import sys
from app.database import SessionLocal
from app.models import SecurityRequirement, SecurityRequirementCompliance
from app.init_data.init_security_requirements import init_security_requirements


def reset_security_requirements():
    """
    Reset ISA/IEC 62443 Security Requirements.
    This will:
    1. Delete all compliance records linked to security requirements
    2. Delete all security requirements
    3. Re-initialize security requirements from the standard
    """
    db = SessionLocal()
    try:
        print("🔄 Resetting ISA/IEC 62443 Security Requirements...")
        
        # 1. Count existing records
        compliance_count = db.query(SecurityRequirementCompliance).count()
        requirements_count = db.query(SecurityRequirement).count()
        
        print(f"📊 Found {compliance_count} compliance records")
        print(f"📊 Found {requirements_count} security requirements")
        
        # 2. Delete compliance records first (due to foreign key constraint)
        if compliance_count > 0:
            print("🗑️  Deleting compliance records...")
            deleted_compliance = db.query(SecurityRequirementCompliance).delete()
            db.commit()
            print(f"✅ Deleted {deleted_compliance} compliance records")
        
        # 3. Delete all security requirements
        if requirements_count > 0:
            print("🗑️  Deleting security requirements...")
            deleted_requirements = db.query(SecurityRequirement).delete()
            db.commit()
            print(f"✅ Deleted {deleted_requirements} security requirements")
        
        # 4. Re-initialize security requirements
        print("🌱 Re-initializing security requirements...")
        created_count = init_security_requirements(db)
        print(f"✅ Created {created_count} security requirements")
        
        print("\n" + "="*50)
        print("🎉 Security Requirements reset completed!")
        print("="*50)
        return True
        
    except Exception as e:
        print(f"❌ Error resetting security requirements: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = reset_security_requirements()
    sys.exit(0 if success else 1)
