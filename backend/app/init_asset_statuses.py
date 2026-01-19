from app.database import SessionLocal
from app.models.asset_status import AssetStatus
import uuid


def setup_asset_statuses(tenant_id=None):
    """
    Setup asset statuses for a specific tenant
    
    Args:
        tenant_id: UUID of the tenant (if None, uses the first tenant)
    """
    db = SessionLocal()
    try:
        from app.models import Tenant

        if tenant_id:
            tenant = db.query(Tenant).filter_by(id=tenant_id).first()
        else:
            # Get the first tenant (Demo Tenant) - backward compatibility
            tenant = db.query(Tenant).first()
            
        if not tenant:
            print("No tenant found. Create a tenant first.")
            return

        stati = [
            {"name": "Active", "description": "Operational asset", "color": "#10b981"},  # Green
            {"name": "Disposed", "description": "Asset no longer in use", "color": "#6b7280"},  # Gray
            {"name": "In stock", "description": "Asset in stock", "color": "#3b82f6"},  # Blue
            {"name": "Faulty", "description": "Faulty asset", "color": "#ef4444"},  # Red
            {"name": "In maintenance", "description": "Asset in maintenance", "color": "#f59e0b"},  # Amber/Orange
        ]
        
        created_statuses = []
        for stato in stati:
            if (
                not db.query(AssetStatus)
                .filter_by(name=stato["name"], tenant_id=tenant.id)
                .first()
            ):
                db.add(AssetStatus(**stato, tenant_id=tenant.id))
                created_statuses.append(stato["name"])
        
        db.commit()
        # Silently complete - no output needed
            
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating asset statuses: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    setup_asset_statuses()
