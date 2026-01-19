from app.database import SessionLocal
from app.models.asset_type import AssetType
import uuid


def setup_asset_types(tenant_id=None):
    """
    Setup asset types for a specific tenant
    
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

        tipi = [
            {
                "name": "PLC",
                "description": "Programmable Logic Controller",
                "purdue_level": 1,
            },
            {"name": "HMI", "description": "Human Machine Interface", "purdue_level": 2},
            {"name": "EWS", "description": "Engineering Workstation", "purdue_level": 3},
            {"name": "RTU", "description": "Remote Terminal Unit", "purdue_level": 1},
            {"name": "Gateway", "description": "Industrial Gateway", "purdue_level": 1.5},
            {
                "name": "Switch",
                "description": "Industrial network switch",
                "purdue_level": 1,
            },
            {"name": "Server", "description": "Server", "purdue_level": 3},
            {"name": "Workstation", "description": "Workstation", "purdue_level": 3},
            {"name": "Firewall", "description": "Firewall", "purdue_level": 2},
            {"name": "Router", "description": "Router", "purdue_level": 2},
            {"name": "Sensor", "description": "Field Sensor", "purdue_level": 0},
            {"name": "Actuator", "description": "Field Actuator", "purdue_level": 0},
        ]
        
        created_types = []
        for tipo in tipi:
            if (
                not db.query(AssetType)
                .filter_by(name=tipo["name"], tenant_id=tenant.id)
                .first()
            ):
                db.add(AssetType(**tipo, tenant_id=tenant.id))
                created_types.append(tipo["name"])
        
        db.commit()
        # Silently complete - no output needed
            
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating asset types: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    setup_asset_types()
