#!/usr/bin/env python3
"""
Script to manually initialize SR-Capability mappings.
Run with: python init_sr_mappings.py
Or in Docker container: docker-compose exec backend python /app/init_sr_mappings.py
"""
from app.database import SessionLocal
from app.init_data.init_sr_capability_mappings import init_sr_capability_mappings


def main():
    """Initialize SR-Capability mappings"""
    print("🔗 Initializing SR-Capability mappings...")
    print("-" * 60)
    
    db = SessionLocal()
    try:
        count = init_sr_capability_mappings(db)
        print("-" * 60)
        if count > 0:
            print(f"✅ Initialization completed! ({count} mappings created)")
        else:
            print("ℹ️  All mappings were already present in the database.")
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

