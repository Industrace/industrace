import uuid
from app.database import SessionLocal
from app.models import Manufacturer, Tenant


def seed_manufacturers(tenant_id=None):
    """
    Seed manufacturers for a specific tenant
    
    Args:
        tenant_id: UUID of the tenant (if None, uses the first tenant)
    """
    db = SessionLocal()
    try:
        if tenant_id:
            tenant = db.query(Tenant).filter_by(id=tenant_id).first()
        else:
            # Get the first available tenant - backward compatibility
            tenant = db.query(Tenant).first()
            
        if not tenant:
            print("No tenant found. Create a tenant first.")
            return
            
        tenant_id = tenant.id
        created_manufacturers = []
        
        manufacturers = [
            {
                "name": "Siemens",
                "description": "Leader manufacturer of PLC, SCADA, DCS, HMI and industrial automation.",
                "website": "https://new.siemens.com/",
                "email": None,
                "phone": None,
            },
            {
                "name": "Schneider Electric",
                "description": "Industrial automation solutions, PLC, SCADA, HMI, electrical protection.",
                "website": "https://www.se.com/",
                "email": None,
                "phone": None,
            },
            {
                "name": "Rockwell Automation",
                "description": "Allen-Bradley PLC, industrial control systems and software.",
                "website": "https://www.rockwellautomation.com/",
                "email": None,
                "phone": None,
            },
            {
                "name": "ABB",
                "description": "Automation, robotics, control systems and energy solutions.",
                "website": "https://new.abb.com/",
                "email": None,
                "phone": None,
            },
            {
                "name": "Honeywell",
                "description": "Industrial control systems, DCS, security and automation.",
                "website": "https://www.honeywellprocess.com/",
                "email": None,
                "phone": None,
            },
            {
                "name": "Emerson",
                "description": "Automation solutions, DCS, process control and instrumentation.",
                "website": "https://www.emerson.com/",
                "email": None,
                "phone": None,
            },
            {
                "name": "Mitsubishi Electric",
                "description": "PLC, inverter, HMI and industrial automation solutions.",
                "website": "https://www.mitsubishielectric.com/",
                "email": None,
                "phone": None,
            },
            {
                "name": "Yokogawa",
                "description": "DCS, measurement instruments, process automation.",
                "website": "https://www.yokogawa.com/",
                "email": None,
                "phone": None,
            },
            {
                "name": "Omron",
                "description": "PLC, sensors, relays, industrial automation.",
                "website": "https://www.omron.com/",
                "email": None,
                "phone": None,
            },
            {
                "name": "GE Digital",
                "description": "Industrial software solutions, SCADA, HMI, automation.",
                "website": "https://www.ge.com/digital/",
                "email": None,
                "phone": None,
            },
            {
                "name": "Phoenix Contact",
                "description": "Components for automation, PLC, industrial connectivity.",
                "website": "https://www.phoenixcontact.com/",
                "email": None,
                "phone": None,
            },
            {
                "name": "B&R Automation",
                "description": "Industrial automation, PLC, HMI, motion control.",
                "website": "https://www.br-automation.com/",
                "email": None,
                "phone": None,
            },
            {
                "name": "Bosch Rexroth",
                "description": "Technologies for automation, motion control, hydraulics, PLC.",
                "website": "https://www.boschrexroth.com/",
                "email": None,
                "phone": None,
            },
            {
                "name": "WAGO",
                "description": "PLC, I/O, automation and industrial connectivity.",
                "website": "https://www.wago.com/",
                "email": None,
                "phone": None,
            },
            {
                "name": "Advantech",
                "description": "Industrial PCs, gateways, IoT solutions and automation.",
                "website": "https://www.advantech.com/",
                "email": None,
                "phone": None,
            },
        ]

        for m in manufacturers:
            # Check if manufacturer exists globally (due to unique constraint on name)
            existing = db.query(Manufacturer).filter_by(name=m["name"]).first()
            if not existing:
                new_man = Manufacturer(
                    id=uuid.uuid4(),
                    tenant_id=tenant_id,
                    name=m["name"],
                    description=m["description"],
                    website=m["website"],
                    email=m["email"],
                    phone=m["phone"],
                )
                db.add(new_man)
                created_manufacturers.append(m["name"])
                # print(f"Created manufacturer: {m['name']}")
            else:
                # print(f"Manufacturer already exists globally: {m['name']}")
                pass
        
        db.commit()
        # Silently complete - no output needed
            
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating manufacturers: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_manufacturers()
