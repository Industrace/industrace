#!/usr/bin/env python3
"""
Script to manually update roles with missing permissions.
This can be run independently or is automatically executed during migrations.

Usage:
    python backend/scripts/update_roles.py
    
    # Or via docker:
    docker-compose -f docker-compose.prod.yml exec backend python scripts/update_roles.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.init_roles import seed_roles
from app.models import Tenant

def update_all_roles():
    """Update roles for all tenants"""
    db = SessionLocal()
    
    try:
        # Get all tenants
        tenants = db.query(Tenant).all()
        
        if not tenants:
            print("⚠️  No tenants found in database")
            return
        
        print(f"🔄 Updating roles for {len(tenants)} tenant(s)...")
        
        for tenant in tenants:
            print(f"  - Updating roles for tenant: {tenant.name} ({tenant.slug})")
            seed_roles(tenant_id=tenant.id)
        
        print("✅ All roles updated successfully!")
        print("\nUpdated permissions include:")
        print("  ✓ vulnerabilities")
        print("  ✓ asset_reviews")
        print("  ✓ asset_dependencies")
        print("  ✓ compliance (ISA/IEC 62443)")
        print("  ✓ security_zones")
        print("  ✓ evidence")
        print("  ✓ notifications")
        print("  ✓ sso (Single Sign-On)")
        print("  ✓ api_keys")
        
    except Exception as e:
        print(f"❌ Error updating roles: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Industrace - Role Permissions Update Script")
    print("=" * 60)
    print()
    
    update_all_roles()
    
    print()
    print("=" * 60)
