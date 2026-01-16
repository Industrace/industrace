import uuid
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import (
    User, Role, Tenant, Asset, Location, Site, Area, 
    Supplier, Manufacturer, Contact, AssetType, AssetStatus,
    AssetInterface, AssetConnection, SecurityZone, Conduit,
    AssetZoneMembership
)
from app.services.auth import get_password_hash
from datetime import datetime, timedelta
import random


def seed_demo_data():
    """Populate database with realistic demo data in English"""
    print("🌱 Seeding demo data using Python...")
    seed_demo_data_python()


def seed_demo_data_python():
    """Populate database with realistic demo data using Python"""
    db: Session = SessionLocal()
    
    # Get or create tenant
    tenant = db.query(Tenant).first()
    if not tenant:
        tenant = Tenant(
            id=uuid.uuid4(),
            name="Industrial Solutions Corp",
            slug="industrial-solutions",
            settings={"theme": "industrial", "language": "en"}
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        print(f"✅ Created tenant: {tenant.name}")
    
    # Get roles
    admin_role = db.query(Role).filter_by(name="admin").first()
    editor_role = db.query(Role).filter_by(name="editor").first()
    viewer_role = db.query(Role).filter_by(name="viewer").first()
    
    # Initialize asset types, statuses and manufacturers if they don't exist
    from app.init_asset_types import setup_asset_types
    from app.init_asset_statuses import setup_asset_statuses
    from app.init_manufacturers import seed_manufacturers
    
    setup_asset_types(tenant.id)
    setup_asset_statuses(tenant.id)
    seed_manufacturers(tenant.id)
    
    # Get asset types and statuses
    asset_types = db.query(AssetType).all()
    asset_statuses = db.query(AssetStatus).all()
    
    # Ensure we have at least one asset type and status
    if not asset_types:
        print("❌ No asset types found. Cannot create assets.")
        db.close()
        return
    if not asset_statuses:
        print("❌ No asset statuses found. Cannot create assets.")
        db.close()
        return
    
    # Create demo sites
    sites_data = [
        {
            "name": "Main Production Plant",
            "code": "MPP",
            "description": "Primary manufacturing facility for automotive components",
            "address": "123 Industrial Blvd, Detroit, MI 48201"
        },
        {
            "name": "Research & Development Center",
            "code": "RDC",
            "description": "Innovation hub for new product development",
            "address": "456 Tech Park Dr, Austin, TX 78701"
        },
        {
            "name": "Distribution Warehouse",
            "code": "DW",
            "description": "Central logistics and distribution facility",
            "address": "789 Logistics Way, Chicago, IL 60601"
        }
    ]
    
    sites = []
    for site_data in sites_data:
        existing_site = db.query(Site).filter_by(name=site_data["name"], tenant_id=tenant.id).first()
        if not existing_site:
            site = Site(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                name=site_data["name"],
                code=site_data["code"],
                description=site_data["description"],
                address=site_data["address"]
            )
            db.add(site)
            sites.append(site)
            print(f"✅ Created site: {site.name}")
        else:
            sites.append(existing_site)
    
    db.commit()
    
    # Create demo areas for each site
    areas_data = [
        # Main Production Plant areas
        {"name": "Assembly Line A", "code": "ALA", "notes": "Primary assembly line for engine components"},
        {"name": "Assembly Line B", "code": "ALB", "notes": "Secondary assembly line for transmission parts"},
        {"name": "Quality Control Lab", "code": "QCL", "notes": "Testing and quality assurance facility"},
        {"name": "Maintenance Bay", "code": "MB", "notes": "Equipment maintenance and repair area"},
        {"name": "Control Room", "code": "CR", "notes": "Central monitoring and control center"},
        
        # R&D Center areas
        {"name": "Prototype Lab", "code": "PL", "notes": "New product prototyping and testing"},
        {"name": "Materials Lab", "code": "ML", "notes": "Material science research and testing"},
        {"name": "Software Development", "code": "SD", "notes": "Control system software development"},
        {"name": "Testing Chamber", "code": "TC", "notes": "Environmental and stress testing"},
        
        # Distribution Warehouse areas
        {"name": "Receiving/Shipping Docks", "code": "RSD", "notes": "Incoming and outgoing logistics"},
        {"name": "Storage Zone A", "code": "SZA", "notes": "High-value component storage"},
        {"name": "Storage Zone B", "code": "SZB", "notes": "Bulk material storage"}
    ]
    
    areas = []
    for area_data in areas_data:
        existing_area = db.query(Area).filter_by(name=area_data["name"], tenant_id=tenant.id).first()
        if not existing_area:
            # Assign area to appropriate site
            if "Assembly" in area_data["name"] or "Quality" in area_data["name"] or "Maintenance" in area_data["name"] or "Control" in area_data["name"]:
                site = next((s for s in sites if "Production Plant" in s.name), sites[0])
            elif "Prototype" in area_data["name"] or "Materials" in area_data["name"] or "Software" in area_data["name"] or "Testing" in area_data["name"]:
                site = next((s for s in sites if "Research" in s.name), sites[0])
            else:
                site = next((s for s in sites if "Distribution" in s.name), sites[0])
            
            area = Area(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                name=area_data["name"],
                site_id=site.id,
                code=area_data["code"],
                notes=area_data["notes"]
            )
            db.add(area)
            areas.append(area)
            print(f"✅ Created area: {area.name}")
        else:
            areas.append(existing_area)
    
    db.commit()
    
    # Create demo locations
    locations_data = [
        # Production Plant locations
        {"name": "Control Panel A1", "code": "CPA1", "description": "Main control panel for Assembly Line A", "area": "Assembly Line A"},
        {"name": "Control Panel A2", "code": "CPA2", "description": "Secondary control panel for Assembly Line A", "area": "Assembly Line A"},
        {"name": "Control Panel B1", "code": "CPB1", "description": "Main control panel for Assembly Line B", "area": "Assembly Line B"},
        {"name": "Quality Station 1", "code": "QS1", "description": "Primary quality control station", "area": "Quality Control Lab"},
        {"name": "Quality Station 2", "code": "QS2", "description": "Secondary quality control station", "area": "Quality Control Lab"},
        {"name": "Maintenance Bay 1", "code": "MB1", "description": "Primary maintenance work area", "area": "Maintenance Bay"},
        {"name": "Maintenance Bay 2", "code": "MB2", "description": "Secondary maintenance work area", "area": "Maintenance Bay"},
        {"name": "Control Room Console", "code": "CRC", "description": "Main control room console", "area": "Control Room"},
        {"name": "Control Room Display", "code": "CRD", "description": "Control room display wall", "area": "Control Room"},
        
        # R&D Center locations
        {"name": "Prototype Station 1", "code": "PS1", "description": "Primary prototype development station", "area": "Prototype Lab"},
        {"name": "Prototype Station 2", "code": "PS2", "description": "Secondary prototype development station", "area": "Prototype Lab"},
        {"name": "Materials Testing Station", "code": "MTS", "description": "Materials testing and analysis station", "area": "Materials Lab"},
        {"name": "Software Development Station", "code": "SDS", "description": "Software development and testing station", "area": "Software Development"},
        {"name": "Testing Chamber 1", "code": "TC1", "description": "Primary environmental testing chamber", "area": "Testing Chamber"},
        
        # Warehouse locations
        {"name": "Receiving Dock 1", "code": "RD1", "description": "Primary receiving dock", "area": "Receiving/Shipping Docks"},
        {"name": "Shipping Dock 1", "code": "SD1", "description": "Primary shipping dock", "area": "Receiving/Shipping Docks"},
        {"name": "Storage Rack A1", "code": "SRA1", "description": "High-value component storage rack", "area": "Storage Zone A"},
        {"name": "Storage Rack A2", "code": "SRA2", "description": "Secondary high-value storage rack", "area": "Storage Zone A"},
        {"name": "Bulk Storage Area 1", "code": "BSA1", "description": "Primary bulk material storage area", "area": "Storage Zone B"}
    ]
    
    locations = []
    for location_data in locations_data:
        existing_location = db.query(Location).filter_by(name=location_data["name"], tenant_id=tenant.id).first()
        if not existing_location:
            # Find the area for this location
            area = next((a for a in areas if a.name == location_data["area"]), None)
            if area:
                location = Location(
                    id=uuid.uuid4(),
                    tenant_id=tenant.id,
                    site_id=area.site_id,
                    area_id=area.id,
                    name=location_data["name"],
                    code=location_data["code"],
                    description=location_data["description"]
                )
                db.add(location)
                locations.append(location)
                print(f"✅ Created location: {location.name}")
        else:
            locations.append(existing_location)
    
    db.commit()
    
    # Create demo manufacturers
    manufacturers_data = [
        {"name": "Siemens", "description": "Industrial automation and control systems"},
        {"name": "Rockwell Automation", "description": "Industrial automation and information solutions"},
        {"name": "Schneider Electric", "description": "Energy management and automation"},
        {"name": "ABB", "description": "Power and automation technologies"}
    ]
    
    manufacturers = []
    for mfg_data in manufacturers_data:
        existing_mfg = db.query(Manufacturer).filter_by(name=mfg_data["name"], tenant_id=tenant.id).first()
        if not existing_mfg:
            manufacturer = Manufacturer(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                name=mfg_data["name"],
                description=mfg_data["description"]
            )
            db.add(manufacturer)
            manufacturers.append(manufacturer)
            print(f"✅ Created manufacturer: {manufacturer.name}")
        else:
            manufacturers.append(existing_mfg)
    
    db.commit()
    
    # Create demo suppliers
    suppliers_data = [
        {"name": "Siemens Industrial Automation", "description": "PLC and HMI systems supplier"},
        {"name": "Rockwell Automation Solutions", "description": "Allen-Bradley products and services"},
        {"name": "Schneider Electric Systems", "description": "Modicon and Telemecanique products"},
        {"name": "ABB Industrial Solutions", "description": "AC500 and 800xA systems"}
    ]
    
    suppliers = []
    for sup_data in suppliers_data:
        existing_sup = db.query(Supplier).filter_by(name=sup_data["name"], tenant_id=tenant.id).first()
        if not existing_sup:
            supplier = Supplier(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                name=sup_data["name"],
                description=sup_data["description"]
            )
            db.add(supplier)
            suppliers.append(supplier)
            print(f"✅ Created supplier: {supplier.name}")
        else:
            suppliers.append(existing_sup)
    
    db.commit()
    
    # Create demo contacts
    contacts_data = [
        {"first_name": "John", "last_name": "Smith", "email": "john.smith@siemens-automation.com", "phone1": "+1-555-0101", "type": "Sales Manager", "supplier": "Siemens Industrial Automation"},
        {"first_name": "Sarah", "last_name": "Johnson", "email": "sarah.johnson@rockwell.com", "phone1": "+1-555-0102", "type": "Technical Support", "supplier": "Rockwell Automation Solutions"},
        {"first_name": "Mike", "last_name": "Davis", "email": "mike.davis@schneider-electric.com", "phone1": "+1-555-0103", "type": "Account Manager", "supplier": "Schneider Electric Systems"},
        {"first_name": "Lisa", "last_name": "Wilson", "email": "lisa.wilson@abb.com", "phone1": "+1-555-0104", "type": "Product Specialist", "supplier": "ABB Industrial Solutions"},
        {"first_name": "David", "last_name": "Brown", "email": "david.brown@siemens-automation.com", "phone1": "+1-555-0105", "type": "Service Engineer", "supplier": "Siemens Industrial Automation"},
        {"first_name": "Emily", "last_name": "Taylor", "email": "emily.taylor@rockwell.com", "phone1": "+1-555-0106", "type": "Sales Representative", "supplier": "Rockwell Automation Solutions"}
    ]
    
    contacts = []
    for contact_data in contacts_data:
        existing_contact = db.query(Contact).filter_by(email=contact_data["email"], tenant_id=tenant.id).first()
        if not existing_contact:
            # Find the supplier for this contact
            supplier = next((s for s in suppliers if s.name == contact_data["supplier"]), None)
            
            contact = Contact(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                first_name=contact_data["first_name"],
                last_name=contact_data["last_name"],
                email=contact_data["email"],
                phone1=contact_data["phone1"],
                type=contact_data["type"]
            )
            db.add(contact)
            contacts.append(contact)
            print(f"✅ Created contact: {contact.first_name} {contact.last_name}")
        else:
            contacts.append(existing_contact)
    
    db.commit()
    
    # Create demo assets
    assets_data = [
        {
            "name": "PLC Controller A1",
            "tag": "PLC-A1",
            "description": "Siemens S7-1500 PLC for Assembly Line A",
            "asset_type": "PLC",
            "manufacturer": "Siemens",
            "model": "S7-1500",
            "serial_number": "SN-PLC-A1-001",
            "location": "Control Panel A1",
            "risk_score": 7.5,
            "business_criticality": "high",
            "remote_access_type": "attended",
            "physical_access_ease": "internal",
            "supplier": "Siemens Industrial Automation",
            "contact": "john.smith@siemens-automation.com"
        },
        {
            "name": "HMI Display A1",
            "tag": "HMI-A1",
            "description": "Siemens KTP900 HMI for Assembly Line A",
            "asset_type": "HMI",
            "manufacturer": "Siemens",
            "model": "KTP900",
            "serial_number": "SN-HMI-A1-001",
            "location": "Control Panel A1",
            "risk_score": 6.0,
            "business_criticality": "medium",
            "remote_access_type": "attended",
            "physical_access_ease": "internal",
            "supplier": "Siemens Industrial Automation",
            "contact": "john.smith@siemens-automation.com"
        },
        {
            "name": "PLC Controller B1",
            "tag": "PLC-B1",
            "description": "Rockwell ControlLogix PLC for Assembly Line B",
            "asset_type": "PLC",
            "manufacturer": "Rockwell Automation",
            "model": "ControlLogix 5580",
            "serial_number": "SN-PLC-B1-001",
            "location": "Control Panel B1",
            "risk_score": 7.0,
            "business_criticality": "high",
            "remote_access_type": "attended",
            "physical_access_ease": "internal",
            "supplier": "Rockwell Automation Solutions",
            "contact": "sarah.johnson@rockwell.com"
        },
        {
            "name": "Quality Control Robot",
            "tag": "ROBOT-QC1",
            "description": "ABB IRB 1200 robot for quality inspection",
            "asset_type": "Actuator",
            "manufacturer": "ABB",
            "model": "IRB 1200",
            "serial_number": "SN-ROBOT-QC1-001",
            "location": "Quality Station 1",
            "risk_score": 8.0,
            "business_criticality": "high",
            "remote_access_type": "unattended",
            "physical_access_ease": "internal",
            "supplier": "ABB Industrial Solutions",
            "contact": "lisa.wilson@abb.com"
        },
        {
            "name": "Network Switch A",
            "tag": "SW-A1",
            "description": "Cisco Catalyst switch for production network",
            "asset_type": "Switch",
            "manufacturer": "Siemens",
            "model": "Catalyst 2960",
            "serial_number": "SN-SW-A1-001",
            "location": "Control Room Console",
            "risk_score": 5.5,
            "business_criticality": "medium",
            "remote_access_type": "attended",
            "physical_access_ease": "internal",
            "supplier": "Siemens Industrial Automation",
            "contact": "david.brown@siemens-automation.com"
        },
        {
            "name": "Temperature Sensor Array",
            "tag": "SENSOR-TEMP1",
            "description": "Temperature monitoring sensors for Assembly Line A",
            "asset_type": "Sensor",
            "manufacturer": "Honeywell",
            "model": "T775",
            "serial_number": "SN-SENSOR-TEMP1-001",
            "location": "Control Panel A1",
            "risk_score": 3.0,
            "business_criticality": "low",
            "remote_access_type": "none",
            "physical_access_ease": "internal",
            "supplier": "Siemens Industrial Automation",
            "contact": "john.smith@siemens-automation.com"
        },
        {
            "name": "Production Server",
            "tag": "SRV-PROD1",
            "description": "Production data collection and analysis server",
            "asset_type": "Server",
            "manufacturer": "Siemens",
            "model": "PowerEdge R740",
            "serial_number": "SN-SRV-PROD1-001",
            "location": "Control Room Console",
            "risk_score": 9.0,
            "business_criticality": "critical",
            "remote_access_type": "unattended",
            "physical_access_ease": "internal",
            "supplier": "Siemens Industrial Automation",
            "contact": "david.brown@siemens-automation.com"
        },
        {
            "name": "Safety System Controller",
            "tag": "SAFETY-CTRL1",
            "description": "Emergency stop and safety monitoring system",
            "asset_type": "PLC",
            "manufacturer": "Schneider Electric",
            "model": "Modicon M580",
            "serial_number": "SN-SAFETY-CTRL1-001",
            "location": "Control Room Console",
            "risk_score": 9.5,
            "business_criticality": "critical",
            "remote_access_type": "none",
            "physical_access_ease": "internal",
            "supplier": "Schneider Electric Systems",
            "contact": "mike.davis@schneider-electric.com"
        },
        {
            "name": "HMI Display B1",
            "tag": "HMI-B1",
            "description": "Rockwell PanelView Plus HMI for Assembly Line B",
            "asset_type": "HMI",
            "manufacturer": "Rockwell Automation",
            "model": "PanelView Plus 7",
            "serial_number": "SN-HMI-B1-001",
            "location": "Control Panel B1",
            "risk_score": 6.5,
            "business_criticality": "medium",
            "remote_access_type": "attended",
            "physical_access_ease": "internal",
            "supplier": "Rockwell Automation Solutions",
            "contact": "emily.taylor@rockwell.com"
        },
        {
            "name": "Firewall Gateway",
            "tag": "FW-GW1",
            "description": "Industrial firewall between production and enterprise networks",
            "asset_type": "Firewall",
            "manufacturer": "Siemens",
            "model": "SCALANCE X208",
            "serial_number": "SN-FW-GW1-001",
            "location": "Control Room Console",
            "risk_score": 8.5,
            "business_criticality": "critical",
            "remote_access_type": "unattended",
            "physical_access_ease": "internal",
            "supplier": "Siemens Industrial Automation",
            "contact": "david.brown@siemens-automation.com"
        },
        {
            "name": "SCADA Server",
            "tag": "SCADA-SRV1",
            "description": "SCADA system server for production monitoring",
            "asset_type": "Server",
            "manufacturer": "Siemens",
            "model": "WinCC Server",
            "serial_number": "SN-SCADA-SRV1-001",
            "location": "Control Room Console",
            "risk_score": 9.0,
            "business_criticality": "critical",
            "remote_access_type": "unattended",
            "physical_access_ease": "internal",
            "supplier": "Siemens Industrial Automation",
            "contact": "john.smith@siemens-automation.com"
        },
        {
            "name": "VFD Motor Controller A1",
            "tag": "VFD-A1",
            "description": "Variable Frequency Drive for motor control on Assembly Line A",
            "asset_type": "Drive",
            "manufacturer": "ABB",
            "model": "ACS880",
            "serial_number": "SN-VFD-A1-001",
            "location": "Control Panel A1",
            "risk_score": 6.0,
            "business_criticality": "high",
            "remote_access_type": "attended",
            "physical_access_ease": "internal",
            "supplier": "ABB Industrial Solutions",
            "contact": "lisa.wilson@abb.com"
        },
        {
            "name": "Pressure Sensor Array",
            "tag": "SENSOR-PRESS1",
            "description": "Pressure monitoring sensors for hydraulic systems",
            "asset_type": "Sensor",
            "manufacturer": "Honeywell",
            "model": "P785",
            "serial_number": "SN-SENSOR-PRESS1-001",
            "location": "Control Panel A2",
            "risk_score": 3.5,
            "business_criticality": "low",
            "remote_access_type": "none",
            "physical_access_ease": "internal",
            "supplier": "Siemens Industrial Automation",
            "contact": "john.smith@siemens-automation.com"
        },
        {
            "name": "Network Switch B",
            "tag": "SW-B1",
            "description": "Secondary network switch for redundancy",
            "asset_type": "Switch",
            "manufacturer": "Siemens",
            "model": "SCALANCE X204",
            "serial_number": "SN-SW-B1-001",
            "location": "Control Room Display",
            "risk_score": 5.0,
            "business_criticality": "medium",
            "remote_access_type": "attended",
            "physical_access_ease": "internal",
            "supplier": "Siemens Industrial Automation",
            "contact": "david.brown@siemens-automation.com"
        },
        {
            "name": "Data Historian",
            "tag": "HIST-SRV1",
            "description": "Production data historian for long-term storage",
            "asset_type": "Server",
            "manufacturer": "Siemens",
            "model": "Process Historian",
            "serial_number": "SN-HIST-SRV1-001",
            "location": "Control Room Console",
            "risk_score": 8.0,
            "business_criticality": "high",
            "remote_access_type": "unattended",
            "physical_access_ease": "internal",
            "supplier": "Siemens Industrial Automation",
            "contact": "john.smith@siemens-automation.com"
        }
    ]
    
    assets = []
    for asset_data in assets_data:
        existing_asset = db.query(Asset).filter_by(tag=asset_data["tag"], tenant_id=tenant.id).first()
        if not existing_asset:
            # Find the asset type
            asset_type = next((at for at in asset_types if at.name.lower() == asset_data["asset_type"].lower()), None)
            if not asset_type and asset_types:
                asset_type = asset_types[0]
                print(f"⚠️  Asset type '{asset_data['asset_type']}' not found, using '{asset_type.name}' for asset '{asset_data['name']}'")
            
            # Find the manufacturer
            manufacturer = next((m for m in manufacturers if m.name.lower() in asset_data["manufacturer"].lower()), None)
            if not manufacturer and manufacturers:
                manufacturer = manufacturers[0]
                print(f"⚠️  Manufacturer '{asset_data['manufacturer']}' not found, using '{manufacturer.name}' for asset '{asset_data['name']}'")
            
            # Find the location
            location = next((l for l in locations if l.name == asset_data["location"]), None)
            if not location and locations:
                location = locations[0]
                print(f"⚠️  Location '{asset_data['location']}' not found, using '{location.name}' for asset '{asset_data['name']}'")
            
            # Get a random asset status
            asset_status = random.choice(asset_statuses) if asset_statuses else None
            
            # Ensure we have all required fields
            if not asset_type:
                print(f"❌ No asset type available for asset '{asset_data['name']}'. Skipping.")
                continue
            if not asset_status:
                print(f"❌ No asset status available for asset '{asset_data['name']}'. Skipping.")
                continue
            
            asset = Asset(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                name=asset_data["name"],
                tag=asset_data["tag"],
                description=asset_data["description"],
                asset_type_id=asset_type.id,
                manufacturer_id=manufacturer.id if manufacturer else None,
                location_id=location.id if location else None,
                site_id=location.site_id if location else None,
                area_id=location.area_id if location else None,
                model=asset_data["model"],
                serial_number=asset_data["serial_number"],
                status_id=asset_status.id,
                risk_score=asset_data["risk_score"],
                business_criticality=asset_data["business_criticality"],
                remote_access_type=asset_data["remote_access_type"],
                physical_access_ease=asset_data["physical_access_ease"],
                installation_date=datetime.now() - timedelta(days=random.randint(30, 365))
            )
            db.add(asset)
            db.flush()  # Flush to get asset.id
            
            # Link asset to supplier if specified
            if "supplier" in asset_data and asset_data["supplier"]:
                supplier = next((s for s in suppliers if s.name == asset_data["supplier"]), None)
                if supplier:
                    asset.suppliers.append(supplier)
            
            # Link asset to contact if specified
            if "contact" in asset_data and asset_data["contact"]:
                contact = next((c for c in contacts if c.email == asset_data["contact"]), None)
                if contact:
                    asset.contacts.append(contact)
            
            assets.append(asset)
            print(f"✅ Created asset: {asset.name}")
        else:
            assets.append(existing_asset)
    
    db.commit()
    
    # Create demo interfaces for assets
    interfaces_data = [
        {"asset": "PLC Controller A1", "name": "Ethernet Port 1", "ip_address": "192.168.1.10", "mac_address": "00:1B:44:11:3A:B7", "type": "Ethernet", "protocols": ["Ethernet/IP"]},
        {"asset": "PLC Controller A1", "name": "Serial Port 1", "ip_address": None, "mac_address": None, "type": "Serial", "protocols": ["Modbus RTU"]},
        {"asset": "HMI Display A1", "name": "Ethernet Port 1", "ip_address": "192.168.1.11", "mac_address": "00:1B:44:11:3A:B8", "type": "Ethernet", "protocols": ["Ethernet/IP"]},
        {"asset": "PLC Controller B1", "name": "Ethernet Port 1", "ip_address": "192.168.1.12", "mac_address": "00:1B:44:11:3A:B9", "type": "Ethernet", "protocols": ["Ethernet/IP"]},
        {"asset": "Quality Control Robot", "name": "Ethernet Port 1", "ip_address": "192.168.1.13", "mac_address": "00:1B:44:11:3A:BA", "type": "Ethernet", "protocols": ["Ethernet/IP"]},
        {"asset": "Network Switch A", "name": "Port 1", "ip_address": "192.168.1.1", "mac_address": "00:1B:44:11:3A:BB", "type": "Ethernet", "protocols": ["Ethernet"]},
        {"asset": "Network Switch A", "name": "Port 2", "ip_address": "192.168.1.1", "mac_address": "00:1B:44:11:3A:BC", "type": "Ethernet", "protocols": ["Ethernet"]},
        {"asset": "Temperature Sensor Array", "name": "Analog Output", "ip_address": None, "mac_address": None, "type": "Analog", "protocols": ["4-20mA"]},
        {"asset": "Production Server", "name": "Ethernet Port 1", "ip_address": "192.168.2.20", "mac_address": "00:1B:44:11:3A:BD", "type": "Ethernet", "protocols": ["Ethernet"]},
        {"asset": "Production Server", "name": "Ethernet Port 2", "ip_address": "192.168.10.20", "mac_address": "00:1B:44:11:3A:BE", "type": "Ethernet", "protocols": ["Ethernet"]},
        {"asset": "Safety System Controller", "name": "Safety Network", "ip_address": "192.168.2.10", "mac_address": "00:1B:44:11:3A:BF", "type": "Safety", "protocols": ["SafetyNet"]},
        {"asset": "HMI Display B1", "name": "Ethernet Port 1", "ip_address": "192.168.1.14", "mac_address": "00:1B:44:11:3A:C0", "type": "Ethernet", "protocols": ["Ethernet/IP"]},
        {"asset": "Firewall Gateway", "name": "Control Network Interface", "ip_address": "192.168.1.254", "mac_address": "00:1B:44:11:3A:C1", "type": "Ethernet", "protocols": ["Ethernet"]},
        {"asset": "Firewall Gateway", "name": "DMZ Network Interface", "ip_address": "192.168.10.1", "mac_address": "00:1B:44:11:3A:C2", "type": "Ethernet", "protocols": ["Ethernet"]},
        {"asset": "Firewall Gateway", "name": "Enterprise Network Interface", "ip_address": "10.0.0.1", "mac_address": "00:1B:44:11:3A:C3", "type": "Ethernet", "protocols": ["Ethernet"]},
        {"asset": "SCADA Server", "name": "Ethernet Port 1", "ip_address": "192.168.2.30", "mac_address": "00:1B:44:11:3A:C4", "type": "Ethernet", "protocols": ["Ethernet"]},
        {"asset": "SCADA Server", "name": "Ethernet Port 2", "ip_address": "192.168.10.30", "mac_address": "00:1B:44:11:3A:C5", "type": "Ethernet", "protocols": ["Ethernet"]},
        {"asset": "VFD Motor Controller A1", "name": "Ethernet Port 1", "ip_address": "192.168.1.15", "mac_address": "00:1B:44:11:3A:C6", "type": "Ethernet", "protocols": ["Ethernet/IP"]},
        {"asset": "Pressure Sensor Array", "name": "Analog Output", "ip_address": None, "mac_address": None, "type": "Analog", "protocols": ["4-20mA"]},
        {"asset": "Network Switch B", "name": "Port 1", "ip_address": "192.168.1.2", "mac_address": "00:1B:44:11:3A:C7", "type": "Ethernet", "protocols": ["Ethernet"]},
        {"asset": "Network Switch B", "name": "Port 2", "ip_address": "192.168.1.2", "mac_address": "00:1B:44:11:3A:C8", "type": "Ethernet", "protocols": ["Ethernet"]},
        {"asset": "Data Historian", "name": "Ethernet Port 1", "ip_address": "192.168.2.40", "mac_address": "00:1B:44:11:3A:C9", "type": "Ethernet", "protocols": ["Ethernet"]}
    ]
    
    interfaces = []
    for interface_data in interfaces_data:
        # Find the asset for this interface
        asset = next((a for a in assets if a.name == interface_data["asset"]), None)
        if asset:
            existing_interface = db.query(AssetInterface).filter_by(
                name=interface_data["name"], 
                asset_id=asset.id
            ).first()
            
            if not existing_interface:
                interface = AssetInterface(
                    id=uuid.uuid4(),
                    tenant_id=tenant.id,
                    asset_id=asset.id,
                    name=interface_data["name"],
                    ip_address=interface_data["ip_address"],
                    mac_address=interface_data["mac_address"],
                    type=interface_data["type"],
                    protocols=interface_data["protocols"]
                )
                db.add(interface)
                interfaces.append(interface)
                print(f"✅ Created interface: {interface.name} for {asset.name}")
            else:
                interfaces.append(existing_interface)
    
    db.commit()
    
    # Create demo connections between assets
    connections_data = [
        {"parent": "PLC Controller A1", "child": "HMI Display A1", "connection_type": "Ethernet/IP", "parent_interface": "Ethernet Port 1", "child_interface": "Ethernet Port 1", "description": "Control communication"},
        {"parent": "PLC Controller A1", "child": "Network Switch A", "connection_type": "Ethernet", "parent_interface": "Ethernet Port 1", "child_interface": "Port 1", "description": "Network connectivity"},
        {"parent": "PLC Controller B1", "child": "HMI Display B1", "connection_type": "Ethernet/IP", "parent_interface": "Ethernet Port 1", "child_interface": "Ethernet Port 1", "description": "Control communication"},
        {"parent": "PLC Controller B1", "child": "Network Switch A", "connection_type": "Ethernet", "parent_interface": "Ethernet Port 1", "child_interface": "Port 2", "description": "Network connectivity"},
        {"parent": "Quality Control Robot", "child": "PLC Controller A1", "connection_type": "Ethernet/IP", "parent_interface": "Ethernet Port 1", "child_interface": "Ethernet Port 1", "description": "Robot control"},
        {"parent": "VFD Motor Controller A1", "child": "PLC Controller A1", "connection_type": "Ethernet/IP", "parent_interface": "Ethernet Port 1", "child_interface": "Ethernet Port 1", "description": "Motor control"},
        {"parent": "Production Server", "child": "Network Switch A", "connection_type": "Ethernet", "parent_interface": "Ethernet Port 1", "child_interface": "Port 1", "description": "Data collection"},
        {"parent": "SCADA Server", "child": "Network Switch A", "connection_type": "Ethernet", "parent_interface": "Ethernet Port 1", "child_interface": "Port 1", "description": "SCADA data collection"},
        {"parent": "Data Historian", "child": "SCADA Server", "connection_type": "Ethernet", "parent_interface": "Ethernet Port 1", "child_interface": "Ethernet Port 1", "description": "Historical data storage"},
        {"parent": "Safety System Controller", "child": "PLC Controller A1", "connection_type": "SafetyNet", "parent_interface": "Safety Network", "child_interface": "Ethernet Port 1", "description": "Safety monitoring"},
        {"parent": "Firewall Gateway", "child": "Network Switch A", "connection_type": "Ethernet", "parent_interface": "Control Network Interface", "child_interface": "Port 1", "description": "Network security"},
        {"parent": "Temperature Sensor Array", "child": "PLC Controller A1", "connection_type": "Analog", "parent_interface": "Analog Output", "child_interface": "Serial Port 1", "description": "Temperature monitoring"},
        {"parent": "Pressure Sensor Array", "child": "PLC Controller A1", "connection_type": "Analog", "parent_interface": "Analog Output", "child_interface": "Serial Port 1", "description": "Pressure monitoring"}
    ]
    
    connections = []
    for connection_data in connections_data:
        # Find the parent and child assets
        parent_asset = next((a for a in assets if a.name == connection_data["parent"]), None)
        child_asset = next((a for a in assets if a.name == connection_data["child"]), None)
        
        if parent_asset and child_asset:
            # Find the interfaces for parent and child
            parent_interface = None
            child_interface = None
            
            if "parent_interface" in connection_data:
                parent_interface = next((i for i in interfaces if i.asset_id == parent_asset.id and i.name == connection_data["parent_interface"]), None)
            
            if "child_interface" in connection_data:
                child_interface = next((i for i in interfaces if i.asset_id == child_asset.id and i.name == connection_data["child_interface"]), None)
            
            # If interfaces not found by name, try to find by type
            if not parent_interface:
                parent_interface = next((i for i in interfaces if i.asset_id == parent_asset.id and i.type == connection_data["connection_type"]), None)
                if not parent_interface:
                    # Try to find any interface of matching type (e.g., Ethernet for Ethernet/IP)
                    type_map = {"Ethernet/IP": "Ethernet", "SafetyNet": "Safety"}
                    search_type = type_map.get(connection_data["connection_type"], connection_data["connection_type"])
                    parent_interface = next((i for i in interfaces if i.asset_id == parent_asset.id and i.type == search_type), None)
            
            if not child_interface:
                child_interface = next((i for i in interfaces if i.asset_id == child_asset.id and i.type == connection_data["connection_type"]), None)
                if not child_interface:
                    # Try to find any interface of matching type (e.g., Ethernet for Ethernet/IP)
                    type_map = {"Ethernet/IP": "Ethernet", "SafetyNet": "Safety"}
                    search_type = type_map.get(connection_data["connection_type"], connection_data["connection_type"])
                    child_interface = next((i for i in interfaces if i.asset_id == child_asset.id and i.type == search_type), None)
            
            existing_connection = db.query(AssetConnection).filter_by(
                parent_asset_id=parent_asset.id,
                child_asset_id=child_asset.id
            ).first()
            
            if not existing_connection:
                connection = AssetConnection(
                    id=uuid.uuid4(),
                    tenant_id=tenant.id,
                    parent_asset_id=parent_asset.id,
                    child_asset_id=child_asset.id,
                    connection_type=connection_data["connection_type"],
                    description=connection_data["description"],
                    local_interface_id=parent_interface.id if parent_interface else None,
                    remote_interface_id=child_interface.id if child_interface else None
                )
                db.add(connection)
                connections.append(connection)
                interface_info = ""
                if parent_interface and child_interface:
                    interface_info = f" ({parent_interface.name} ↔ {child_interface.name})"
                print(f"✅ Created connection: {parent_asset.name} → {child_asset.name}{interface_info}")
            else:
                # Update existing connection with interfaces if not set
                if existing_connection.local_interface_id is None and parent_interface:
                    existing_connection.local_interface_id = parent_interface.id
                if existing_connection.remote_interface_id is None and child_interface:
                    existing_connection.remote_interface_id = child_interface.id
                db.commit()
                connections.append(existing_connection)
    
    db.commit()
    
    # Create ISA62443 Security Zones
    print("\n🔒 Creating ISA62443 Security Zones...")
    security_zones_data = [
        {
            "name": "Level 3 - Control Zone",
            "description": "Production control systems zone (Purdue Level 3)",
            "zone_type": "control",
            "security_level_target": 3,
            "site": "Main Production Plant",
            "network_segment": "192.168.1.0/24"
        },
        {
            "name": "Level 2 - Supervisory Zone",
            "description": "SCADA and supervisory systems zone (Purdue Level 2)",
            "zone_type": "supervisory",
            "security_level_target": 3,
            "site": "Main Production Plant",
            "network_segment": "192.168.2.0/24"
        },
        {
            "name": "Level 3.5 - DMZ Zone",
            "description": "Demilitarized zone for data exchange between control and enterprise",
            "zone_type": "dmz",
            "security_level_target": 2,
            "site": "Main Production Plant",
            "network_segment": "192.168.10.0/24",
            "is_dmz": True
        },
        {
            "name": "Level 4 - Enterprise Zone",
            "description": "Enterprise IT systems zone (Purdue Level 4)",
            "zone_type": "enterprise",
            "security_level_target": 2,
            "site": "Main Production Plant",
            "network_segment": "10.0.0.0/24"
        },
        {
            "name": "Safety Zone",
            "description": "Safety instrumented systems zone",
            "zone_type": "safety",
            "security_level_target": 4,
            "site": "Main Production Plant",
            "network_segment": "192.168.2.0/24"
        }
    ]
    
    security_zones = []
    production_site = next((s for s in sites if "Production Plant" in s.name), sites[0])
    
    for zone_data in security_zones_data:
        existing_zone = db.query(SecurityZone).filter_by(name=zone_data["name"], tenant_id=tenant.id).first()
        if not existing_zone:
            zone = SecurityZone(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                site_id=production_site.id,
                name=zone_data["name"],
                description=zone_data["description"],
                zone_type=zone_data["zone_type"],
                security_level_target=zone_data["security_level_target"],
                network_segment=zone_data.get("network_segment"),
                is_dmz=zone_data.get("is_dmz", False),
                compliance_status="not_assessed"
            )
            db.add(zone)
            security_zones.append(zone)
            print(f"✅ Created security zone: {zone.name} (SL-T: {zone.security_level_target})")
        else:
            security_zones.append(existing_zone)
    
    db.commit()
    
    # Create Asset Zone Memberships
    print("\n🔗 Linking assets to Security Zones...")
    zone_memberships_data = [
        # Control Zone (Level 3) assets
        {"asset": "PLC Controller A1", "zone": "Level 3 - Control Zone", "role": "primary", "sl_target": 3},
        {"asset": "PLC Controller B1", "zone": "Level 3 - Control Zone", "role": "primary", "sl_target": 3},
        {"asset": "HMI Display A1", "zone": "Level 3 - Control Zone", "role": "operator_interface", "sl_target": 3},
        {"asset": "HMI Display B1", "zone": "Level 3 - Control Zone", "role": "operator_interface", "sl_target": 3},
        {"asset": "VFD Motor Controller A1", "zone": "Level 3 - Control Zone", "role": "supporting", "sl_target": 3},
        {"asset": "Temperature Sensor Array", "zone": "Level 3 - Control Zone", "role": "monitoring", "sl_target": 2},
        {"asset": "Pressure Sensor Array", "zone": "Level 3 - Control Zone", "role": "monitoring", "sl_target": 2},
        {"asset": "Network Switch A", "zone": "Level 3 - Control Zone", "role": "supporting", "sl_target": 3},
        {"asset": "Network Switch B", "zone": "Level 3 - Control Zone", "role": "supporting", "sl_target": 3},
        
        # Supervisory Zone (Level 2) assets
        {"asset": "SCADA Server", "zone": "Level 2 - Supervisory Zone", "role": "primary", "sl_target": 3},
        {"asset": "Production Server", "zone": "Level 2 - Supervisory Zone", "role": "data_collector", "sl_target": 3},
        {"asset": "Data Historian", "zone": "Level 2 - Supervisory Zone", "role": "data_collector", "sl_target": 3},
        
        # DMZ Zone assets
        {"asset": "Firewall Gateway", "zone": "Level 3.5 - DMZ Zone", "role": "boundary", "sl_target": 2},
        {"asset": "Production Server", "zone": "Level 3.5 - DMZ Zone", "role": "data_publisher", "sl_target": 2, "interface_scope": "Ethernet Port 1"},
        
        # Safety Zone assets
        {"asset": "Safety System Controller", "zone": "Safety Zone", "role": "primary", "sl_target": 4},
        {"asset": "Quality Control Robot", "zone": "Safety Zone", "role": "supporting", "sl_target": 3}
    ]
    
    zone_memberships = []
    for membership_data in zone_memberships_data:
        asset = next((a for a in assets if a.name == membership_data["asset"]), None)
        zone = next((z for z in security_zones if z.name == membership_data["zone"]), None)
        
        if asset and zone:
            existing_membership = db.query(AssetZoneMembership).filter_by(
                asset_id=asset.id,
                security_zone_id=zone.id,
                role=membership_data["role"]
            ).first()
            
            if not existing_membership:
                membership = AssetZoneMembership(
                    id=uuid.uuid4(),
                    tenant_id=tenant.id,
                    asset_id=asset.id,
                    security_zone_id=zone.id,
                    role=membership_data["role"],
                    sl_target=membership_data.get("sl_target"),
                    interface_scope=membership_data.get("interface_scope")
                )
                db.add(membership)
                zone_memberships.append(membership)
                print(f"✅ Linked {asset.name} to {zone.name} as {membership_data['role']}")
            else:
                zone_memberships.append(existing_membership)
    
    db.commit()
    
    # Create Conduits between Security Zones
    print("\n🌉 Creating Conduits between Security Zones...")
    conduits_data = [
        {
            "name": "Control to Supervisory Conduit",
            "description": "Data flow from control systems to SCADA",
            "from_zone": "Level 3 - Control Zone",
            "to_zone": "Level 2 - Supervisory Zone",
            "conduit_type": "network",
            "protocol": "Ethernet/IP",
            "port_range": "44818",
            "is_encrypted": True,
            "encryption_type": "tls",
            "authentication_required": True,
            "authentication_method": "certificate",
            "security_level_target": 3,
            "flow_justification": "Production data collection for monitoring and analysis"
        },
        {
            "name": "Supervisory to DMZ Conduit",
            "description": "Data flow from SCADA to DMZ for enterprise access",
            "from_zone": "Level 2 - Supervisory Zone",
            "to_zone": "Level 3.5 - DMZ Zone",
            "conduit_type": "network",
            "protocol": "tcp",
            "port_range": "443",
            "is_encrypted": True,
            "encryption_type": "tls",
            "authentication_required": True,
            "authentication_method": "certificate",
            "security_level_target": 2,
            "flow_justification": "Enterprise reporting and business intelligence"
        },
        {
            "name": "DMZ to Enterprise Conduit",
            "description": "Data flow from DMZ to enterprise IT systems",
            "from_zone": "Level 3.5 - DMZ Zone",
            "to_zone": "Level 4 - Enterprise Zone",
            "conduit_type": "network",
            "protocol": "tcp",
            "port_range": "443",
            "is_encrypted": True,
            "encryption_type": "tls",
            "authentication_required": True,
            "authentication_method": "certificate",
            "security_level_target": 2,
            "flow_justification": "Business data integration with ERP and MES systems"
        },
        {
            "name": "Control to Safety Conduit",
            "description": "Safety monitoring data from control systems",
            "from_zone": "Level 3 - Control Zone",
            "to_zone": "Safety Zone",
            "conduit_type": "network",
            "protocol": "SafetyNet",
            "port_range": "502",
            "is_encrypted": False,
            "authentication_required": False,
            "security_level_target": 4,
            "flow_justification": "Real-time safety monitoring and emergency stop signals"
        }
    ]
    
    conduits = []
    for conduit_data in conduits_data:
        from_zone = next((z for z in security_zones if z.name == conduit_data["from_zone"]), None)
        to_zone = next((z for z in security_zones if z.name == conduit_data["to_zone"]), None)
        
        if from_zone and to_zone:
            existing_conduit = db.query(Conduit).filter_by(
                name=conduit_data["name"],
                tenant_id=tenant.id
            ).first()
            
            if not existing_conduit:
                conduit = Conduit(
                    id=uuid.uuid4(),
                    tenant_id=tenant.id,
                    from_zone_id=from_zone.id,
                    to_zone_id=to_zone.id,
                    name=conduit_data["name"],
                    description=conduit_data["description"],
                    conduit_type=conduit_data["conduit_type"],
                    protocol=conduit_data.get("protocol"),
                    port_range=conduit_data.get("port_range"),
                    is_encrypted=conduit_data.get("is_encrypted", False),
                    encryption_type=conduit_data.get("encryption_type"),
                    authentication_required=conduit_data.get("authentication_required", False),
                    authentication_method=conduit_data.get("authentication_method"),
                    security_level_target=conduit_data.get("security_level_target"),
                    flow_justification=conduit_data.get("flow_justification"),
                    compliance_status="not_assessed"
                )
                db.add(conduit)
                conduits.append(conduit)
                print(f"✅ Created conduit: {conduit.name} ({from_zone.name} → {to_zone.name})")
            else:
                conduits.append(existing_conduit)
    
    db.commit()
    
    print(f"\n🎉 Demo data seeding completed successfully!")
    print(f"📊 Created/Found:")
    print(f"   • {len(sites)} Sites")
    print(f"   • {len(areas)} Areas")
    print(f"   • {len(locations)} Locations")
    print(f"   • {len(manufacturers)} Manufacturers")
    print(f"   • {len(suppliers)} Suppliers")
    print(f"   • {len(contacts)} Contacts")
    print(f"   • {len(assets)} Assets")
    print(f"   • {len(interfaces)} Interfaces")
    print(f"   • {len(connections)} Connections")
    print(f"   • {len(security_zones)} Security Zones")
    print(f"   • {len(zone_memberships)} Asset Zone Memberships")
    print(f"   • {len(conduits)} Conduits")
    
    db.close()


if __name__ == "__main__":
    seed_demo_data() 