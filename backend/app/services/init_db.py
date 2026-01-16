# backend/services/init_db.py

from sqlalchemy.exc import IntegrityError
from database import engine, SessionLocal
from models import Base, Tenant, User, Site, AssetType, Asset
from auth import get_password_hash
from services.init_tenant_roles import init_tenant_roles, get_default_admin_role_id
import uuid


def create_tables():
    """Crea tutte le tabelle nel database"""
    Base.metadata.create_all(bind=engine)
    # print("✅ Tabelle create con successo")


def create_sample_data():
    """Inserisce dati di esempio per testing"""
    db = SessionLocal()
    try:
        # Check if data already exists (tenant)
        if db.query(Tenant).count() > 0:
            # print("ℹ️  Data already present, skip sample data insertion")
            return

        # Crea tenant di esempio
        tenant = Tenant(
            name="Acme Industries",
            slug="acme-industries",
            settings={"theme": "industrial", "language": "en"},
        )
        db.add(tenant)
        db.flush()  # Per ottenere l'ID senza committare

        # Crea ruoli default per il tenant
        # print("🔄 Creazione ruoli default per il tenant...")
        init_tenant_roles(tenant.id, db)
        
        # Ottieni l'ID del ruolo admin
        admin_role_id = get_default_admin_role_id(tenant.id, db)
        
        # Crea utente admin
        admin_user = User(
            tenant_id=tenant.id,
            email="admin@acme.com",
            password_hash=get_password_hash("admin123"),
            name="Administrator",
            role_id=admin_role_id,  # Usa l'ID del ruolo invece del nome
            password_change_required=True,  # Force password change on first login
        )
        db.add(admin_user)

        # Crea sito di esempio
        site = Site(
            tenant_id=tenant.id,
            name="Main Plant",
            code="MAIN-01",
            address="123 Industrial Avenue, Milan",
            description="Main production site",
        )
        db.add(site)
        db.flush()

        # Crea tipi di asset globali
        asset_types = [
            AssetType(
                name="Industrial Gateway",
                category="gateway",
                icon="router",
                color="#3b82f6",
            ),
            AssetType(name="PLC", category="plc", icon="cpu", color="#10b981"),
            AssetType(name="HMI", category="hmi", icon="monitor", color="#f59e0b"),
            AssetType(
                name="Sensor", category="sensor", icon="thermometer", color="#ef4444"
            ),
            AssetType(
                name="Actuator", category="actuator", icon="zap", color="#8b5cf6"
            ),
            AssetType(
                name="Industrial Switch",
                category="network",
                icon="wifi",
                color="#06b6d4",
            ),
        ]

        for asset_type in asset_types:
            db.add(asset_type)
        db.flush()

        # Crea asset di esempio
        gateway_type = (
            db.query(AssetType).filter(AssetType.name == "Industrial Gateway").first()
        )
        plc_type = db.query(AssetType).filter(AssetType.name == "PLC").first()
        hmi_type = db.query(AssetType).filter(AssetType.name == "HMI").first()

        # Asset esempio
        assets = [
            Asset(
                tenant_id=tenant.id,
                site_id=site.id,
                asset_type_id=gateway_type.id,
                name="Production Gateway",
                tag="GW-01",
                serial_number="GW123456789",
                model="GW-Model-X",
                manufacturer="IndustrialCo",
                firmware_version="1.0.0",
                status="online",
                location="Control Room",
                description="Main gateway for communication",
                ip_address="192.168.100.10",
            ),
            Asset(
                tenant_id=tenant.id,
                site_id=site.id,
                asset_type_id=plc_type.id,
                name="PLC Line 1",
                tag="PLC-01",
                serial_number="PLC987654321",
                model="PLC-Model-A",
                manufacturer="PLC Inc.",
                firmware_version="2.1.5",
                status="offline",
                location="Production Line 1",
                description="Main PLC for line 1",
                ip_address="192.168.100.20",
            ),
            Asset(
                tenant_id=tenant.id,
                site_id=site.id,
                asset_type_id=hmi_type.id,
                name="Supervision HMI",
                tag="HMI-01",
                serial_number="HMI123987456",
                model="HMI-Model-Z",
                manufacturer="HMI Corp.",
                firmware_version="3.3.3",
                status="online",
                location="Control Room",
                description="Human-machine interface",
                ip_address="192.168.100.30",
            ),
        ]

        for asset in assets:
            db.add(asset)

        # Commit finale
        db.commit()
        # print("✅ Dati di esempio inseriti con successo")

    except IntegrityError as e:
        db.rollback()
        # print(f"❌ Errore durante inserimento dati: {e}")

    finally:
        db.close()


if __name__ == "__main__":
    create_tables()
    create_sample_data()
