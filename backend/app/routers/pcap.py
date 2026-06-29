import uuid
from typing import List
import tempfile
from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.services.auth import get_current_user
from app.services.rbac import require_section_access
from app.errors.exceptions import ErrorCodeException
from app.errors.error_codes import ErrorCode
from app.services.pcap_parser import extract_assets_and_communications_from_pcap, normalize_protocol
from app.services.asset_sync import sync_assets, sync_communications
from app.crud.sites import get_site
import app.models

router = APIRouter(
    prefix="/pcap",
    tags=["pcap"],
    dependencies=[Depends(require_section_access("utility"))],
)


@router.get("/protocols")
async def get_supported_protocols():
    """
    Restituisce la lista dei protocolli industriali supportati
    che vengono normalizzati durante l'import PCAP.
    """
    supported_protocols = [
        "Modbus",
        "Profinet", 
        "OPC-UA",
        "EtherNet/IP",
        "BACnet",
        "DNP3",
        "KNX",
        "M-Bus",
        "IEC 61850",
        "S7",
        "MQTT",
        "Other"
    ]
    
    return {
        "protocols": supported_protocols,
        "description": "Protocolli industriali supportati per la normalizzazione durante l'import PCAP"
    }


@router.get("/interface-protocols")
async def get_interface_protocols():
    """
    Restituisce la lista dei protocolli supportati per le interfacce degli asset.
    """
    interface_protocols = [
        "Modbus TCP",
        "Modbus RTU",
        "EtherNet/IP",
        "DNP3",
        "BACNet",
        "OPC UA",
        "HTTP",
        "HTTPS",
        "FTP",
        "SFTP",
        "MQTT",
        "CoAP",
        "XMPP",
        "SNMP",
        "Syslog",
        "NTP",
        "DNS",
        "DHCP",
        "RADIUS",
        "LDAP",
        "Kerberos",
        "TLS",
        "SSL",
        "SSH",
        "Telnet",
        "Seriale",
        "Other"
    ]
    
    return {
        "protocols": interface_protocols,
        "description": "Protocolli supportati per le interfacce degli asset"
    }


@router.post("/upload")
async def upload_pcap_files(
    files: List[UploadFile] = File(...),
    site_id: uuid.UUID = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validazione dimensione file PCAP (50MB)
    PCAP_MAX_SIZE = 50 * 1024 * 1024  # 50MB in bytes
    
    for file in files:
        if not file.filename.lower().endswith('.pcap'):
            raise ErrorCodeException(
                status_code=400,
                error_code=ErrorCode.INVALID_FILE_FORMAT,
                detail=f"File {file.filename} is not a valid PCAP file"
            )
        
        # Leggi dimensione file
        file.file.seek(0, 2)  # Vai alla fine
        file_size = file.file.tell()
        file.file.seek(0)  # Torna all'inizio
        
        if file_size > PCAP_MAX_SIZE:
            raise ErrorCodeException(
                status_code=400,
                error_code=ErrorCode.FILE_TOO_LARGE,
                detail=f"File {file.filename} exceeds maximum size of 50MB (current size: {file_size / 1024 / 1024:.1f}MB)"
            )

    site = get_site(db, site_id)
    if not site:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.SITE_NOT_FOUND)

    all_devices = {}
    all_communications = {}

    for file in files:
        suffix = ".pcap" if file.filename.endswith(".pcap") else ""
        with tempfile.NamedTemporaryFile(delete=True, suffix=suffix) as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp.flush()

            # Now extract devices and communications
            devices, communications = extract_assets_and_communications_from_pcap(
                tmp.name
            )

            # Merge devices without duplicate MAC
            for mac, data in devices.items():
                if mac not in all_devices:
                    all_devices[mac] = data
                else:
                    all_devices[mac]["ips"].update(data["ips"])
                    all_devices[mac]["protocols"].update(data["protocols"])

            # Merge communications (incrementing counters)
            for src_mac, dsts in communications.items():
                if src_mac not in all_communications:
                    all_communications[src_mac] = dsts.copy()
                else:
                    for dst_mac, count in dsts.items():
                        all_communications[src_mac][dst_mac] = (
                            all_communications[src_mac].get(dst_mac, 0) + count
                        )

    # Convert sets to list, like in the parser
    for mac in all_devices:
        all_devices[mac]["ips"] = list(all_devices[mac]["ips"])
        all_devices[mac]["protocols"] = list(all_devices[mac]["protocols"])

    created, updated = sync_assets(db, all_devices, current_user.tenant_id, site.id)
    sync_communications(db, all_communications, current_user.tenant_id, site.id)

    return {
        "created": len(created),
        "updated": len(updated),
        "total_devices_found": len(all_devices),
    }


@router.post("/preview")
async def preview_pcap_files(
    files: List[UploadFile] = File(...),
    site_id: uuid.UUID = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validazione dimensione file PCAP (50MB)
    PCAP_MAX_SIZE = 50 * 1024 * 1024  # 50MB in bytes
    
    for file in files:
        if not file.filename.lower().endswith('.pcap'):
            raise ErrorCodeException(
                status_code=400,
                error_code=ErrorCode.INVALID_FILE_FORMAT,
                detail=f"File {file.filename} is not a valid PCAP file"
            )
        
        # Leggi dimensione file
        file.file.seek(0, 2)  # Vai alla fine
        file_size = file.file.tell()
        file.file.seek(0)  # Torna all'inizio
        
        if file_size > PCAP_MAX_SIZE:
            raise ErrorCodeException(
                status_code=400,
                error_code=ErrorCode.FILE_TOO_LARGE,
                detail=f"File {file.filename} exceeds maximum size of 50MB (current size: {file_size / 1024 / 1024:.1f}MB)"
            )
    site = get_site(db, site_id)
    if not site:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.SITE_NOT_FOUND)

    all_devices = {}
    all_communications = {}

    for file in files:
        suffix = ".pcap" if file.filename.endswith(".pcap") else ""
        with tempfile.NamedTemporaryFile(delete=True, suffix=suffix) as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp.flush()
            devices, communications = extract_assets_and_communications_from_pcap(
                tmp.name
            )
            for mac, data in devices.items():
                if mac not in all_devices:
                    all_devices[mac] = data
                else:
                    all_devices[mac]["ips"].update(data["ips"])
                    all_devices[mac]["protocols"].update(data["protocols"])
            for src_mac, dsts in communications.items():
                if src_mac not in all_communications:
                    all_communications[src_mac] = dsts.copy()
                else:
                    for dst_mac, count in dsts.items():
                        all_communications[src_mac][dst_mac] = (
                            all_communications[src_mac].get(dst_mac, 0) + count
                        )
    for mac in all_devices:
        all_devices[mac]["ips"] = list(all_devices[mac]["ips"])
        all_devices[mac]["protocols"] = list(all_devices[mac]["protocols"])

    # --- LOGICA PREVIEW ---
    from app.services.oui_lookup import load_oui_map

    OUI_MAP = load_oui_map()
    preview = {
        "to_create": [],
        "to_update": [],
        "manufacturers_to_create": set(),
        "interfaces_to_create": [],
        "communications": [],
    }
    # AssetType
    asset_type = db.query(app.models.AssetType).filter_by(name="Network Device").first()
    asset_type_id = asset_type.id if asset_type else None
    # Existing manufacturers
    existing_manufacturers = {
        m.name
        for m in db.query(app.models.manufacturer.Manufacturer)
        .filter_by(tenant_id=current_user.tenant_id)
        .all()
    }
    # Existing assets
    existing_assets = (
        db.query(app.models.Asset)
        .filter_by(tenant_id=current_user.tenant_id, site_id=site.id)
        .all()
    )
    mac_to_asset = {
        a.custom_fields.get("mac_address"): a
        for a in existing_assets
        if a.custom_fields.get("mac_address")
    }
    # Existing interfaces
    existing_ifaces = (
        db.query(app.models.asset_interface.AssetInterface)
        .filter_by(tenant_id=current_user.tenant_id)
        .all()
    )
    mac_to_iface = {i.mac_address: i for i in existing_ifaces if i.mac_address}
    ip_to_ifaces = {}
    for iface in existing_ifaces:
        if iface.ip_address:
            ip_to_ifaces.setdefault(str(iface.ip_address), []).append(iface)

    for mac, data in all_devices.items():
        vendor = OUI_MAP.get(
            mac.replace(":", "").replace("-", "")[:6].upper(), "Unknown Vendor"
        )
        manufacturer_new = vendor not in existing_manufacturers
        if manufacturer_new:
            preview["manufacturers_to_create"].add(vendor)
        asset = mac_to_asset.get(mac)
        ip = data["ips"][0] if data["ips"] else None
        asset_name = f"imported - {ip}" if ip else "imported - unknown"
        asset_info = {
            "mac": mac,
            "ip": ip,
            "name": asset_name,
            "vendor": vendor,
            "manufacturer_new": manufacturer_new,
            "protocols": list(data["protocols"]),
        }
        if not asset and ip:
            ifaces_by_ip = ip_to_ifaces.get(ip, [])
            if len(ifaces_by_ip) == 1:
                iface_by_ip = ifaces_by_ip[0]
                asset = (
                    db.query(app.models.Asset)
                    .filter(app.models.Asset.id == iface_by_ip.asset_id)
                    .first()
                )
        if asset:
            # Show differences
            diff = {}
            if ip and getattr(asset, "ip_address", None) != ip:
                diff["ip_address"] = {
                    "old": getattr(asset, "ip_address", None),
                    "new": ip,
                }
            if vendor and (not asset.manufacturer or asset.manufacturer.name != vendor):
                diff["manufacturer"] = {
                    "old": asset.manufacturer.name if asset.manufacturer else None,
                    "new": vendor,
                }
            asset_info["diff"] = diff
            preview["to_update"].append(asset_info)
        else:
            preview["to_create"].append(asset_info)
        # Interfaces to create
        if mac not in mac_to_iface:
            preview["interfaces_to_create"].append(
                {"mac": mac, "asset_name": asset_name, "ip": ip, "vendor": vendor}
            )
    # Communications
    for src_mac, dsts in all_communications.items():
        for dst_mac, count in dsts.items():
            preview["communications"].append(
                {"src_mac": src_mac, "dst_mac": dst_mac, "count": count}
            )
    preview["manufacturers_to_create"] = list(preview["manufacturers_to_create"])
    return preview
