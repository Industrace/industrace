#!/usr/bin/env python3
"""
Script to manually initialize Security Capabilities.
Run with: python init_capabilities.py
Or in Docker container: docker-compose exec backend python /app/init_capabilities.py
"""
from app.database import SessionLocal
from app.init_data.init_security_capabilities import init_security_capabilities


def main():
    """Initialize Security Capabilities"""
    print("🔐 Initializing Security Capabilities...")
    print("-" * 60)
    
    db = SessionLocal()
    try:
        count = init_security_capabilities(db)
        print("-" * 60)
        if count > 0:
            print(f"✅ Initialization completed! ({count} capabilities created)")
        else:
            print("ℹ️  All capabilities were already present in the database.")
    except Exception as e:
        print(f"❌ Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()
    
    return 0


if __name__ == "__main__":
    exit(main())

