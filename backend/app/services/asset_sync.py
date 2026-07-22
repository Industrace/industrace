# backend/services/asset_sync.py

from sqlalchemy.orm import Session

from app.models import Asset, AssetType, AssetCommunication
from uuid import UUID
from app.services.oui_lookup import get_cached_oui_map
from app.models.asset_interface import AssetInterface
from app.crud.asset_interface import create_interface
from app.schemas.asset_interface import AssetInterfaceCreate
from app.models.manufacturer import Manufacturer
from app.crud.manufacturers import create_manufacturer
from app.schemas.manufacturer import ManufacturerCreate
from app.models.asset_status import AssetStatus


def get_vendor_from_mac(mac: str) -> str:
    prefix = mac.replace(":", "").replace("-", "")[:6].upper()
    return get_cached_oui_map().get(prefix, "Unknown Vendor")


def sync_assets(session: Session, devices: dict, tenant_id: UUID, site_id: UUID):
    """
    Sync assets from devices dict (key=mac) to DB.
    Update or create Asset.
    """
    # Retrieve or create AssetType for network devices
    asset_type = (
        session.query(AssetType).filter(AssetType.name == "Network Device").first()
    )
    if not asset_type:
        asset_type = AssetType(name="Network Device")
        session.add(asset_type)
        session.commit()

    created_assets = []
    updated_assets = []

    for mac, data in devices.items():
        # Search interface with that MAC
        iface = (
            session.query(AssetInterface)
            .filter(AssetInterface.mac_address == mac)
            .first()
        )
        asset = None
        if iface:
            asset = session.query(Asset).filter(Asset.id == iface.asset_id).first()
        else:
            # If not found, search by IP (only if there is a single match)
            ip = data["ips"][0] if data["ips"] else None
            iface_by_ip = None
            if ip:
                interfaces_by_ip = (
                    session.query(AssetInterface)
                    .filter(AssetInterface.ip_address == ip)
                    .all()
                )
                if len(interfaces_by_ip) == 1:
                    iface_by_ip = interfaces_by_ip[0]
                    asset = (
                        session.query(Asset)
                        .filter(Asset.id == iface_by_ip.asset_id)
                        .first()
                    )
                # If more than one interface with that IP, don't associate anything (asset remains None)

        vendor = get_vendor_from_mac(mac)
        protocols_list = list(data["protocols"])

        # Search or create manufacturer
        manufacturer = (
            session.query(Manufacturer)
            .filter(Manufacturer.name == vendor, Manufacturer.tenant_id == tenant_id)
            .first()
        )
        if not manufacturer:
            manufacturer_in = ManufacturerCreate(name=vendor, description=None)
            manufacturer = create_manufacturer(session, manufacturer_in, tenant_id)

        if asset:
            # update fields if necessary
            asset.site_id = site_id
            asset.custom_fields["mac_address"] = mac
            asset.custom_fields["vendor"] = vendor
            asset.protocols = protocols_list
            asset.manufacturer_id = manufacturer.id
            
            # Aggiorna i protocolli dell'interfaccia corrispondente
            if iface:
                iface.protocols = protocols_list
            elif iface_by_ip:
                iface_by_ip.protocols = protocols_list
                
            updated_assets.append(asset)
        else:
            # Retrieve the 'Active' status if it exists, otherwise the first available
            status_active = (
                session.query(AssetStatus).filter(AssetStatus.name == "Attivo").first()
            )
            if not status_active:
                status_active = session.query(AssetStatus).first()
            status_id = status_active.id if status_active else None
            asset_name = (
                f"imported - {data['ips'][0]}" if data["ips"] else "imported - unknown"
            )
            new_asset = Asset(
                tenant_id=tenant_id,
                site_id=site_id,
                asset_type_id=asset_type.id,
                name=asset_name,
                custom_fields={"mac_address": mac, "vendor": vendor},
                status_id=status_id,
                manufacturer_id=manufacturer.id,
                protocols=protocols_list,
            )
            session.add(new_asset)
            session.commit()  # To get the ID
            # Create the associated interface immediately
            ip = data["ips"][0] if data["ips"] else None
            if ip:
                new_interface = AssetInterface(
                    asset_id=new_asset.id,
                    tenant_id=tenant_id,
                    name=f"eth0",
                    type="ethernet",
                    ip_address=ip,
                    mac_address=mac,
                    protocols=protocols_list,  # Associa i protocolli all'interfaccia
                )
                session.add(new_interface)
            session.commit()
            created_assets.append(new_asset)

    return created_assets, updated_assets


def sync_communications(
    session: Session, communications: dict, tenant_id: UUID, site_id: UUID
):
    """
    Sync communications between assets, based on the dict
    communications[src_mac][dst_mac] = count packets
    Now works at interface level: src_interface_id, dst_interface_id
    """
    # First retrieve all assets involved by MAC address
    mac_to_asset = {}
    macs = list(
        set(communications.keys())
        | set(dst for src in communications for dst in communications[src])
    )

    assets = (
        session.query(Asset)
        .filter(Asset.custom_fields["mac_address"].astext.in_(macs))
        .all()
    )
    for asset in assets:
        mac = asset.custom_fields.get("mac_address")
        if mac:
            mac_to_asset[mac] = asset

    # Retrieve all interfaces involved by MAC address
    mac_to_interface = {}
    interfaces = (
        session.query(AssetInterface).filter(AssetInterface.mac_address.in_(macs)).all()
    )
    for iface in interfaces:
        mac_to_interface[iface.mac_address] = iface

    # Iterate communications
    for src_mac, dsts in communications.items():
        # Search or create source interface
        src_iface = mac_to_interface.get(src_mac)
        if not src_iface:
            src_asset = mac_to_asset.get(src_mac)
            if src_asset:
                src_iface_data = AssetInterfaceCreate(
                    asset_id=src_asset.id,
                    tenant_id=tenant_id,
                    name="Auto-imported",
                    type="ethernet",
                    mac_address=src_mac,
                    vlan=None,
                    logical_port=None,
                    physical_plug_label=None,
                )
                src_iface = create_interface(session, src_iface_data)
                mac_to_interface[src_mac] = src_iface
            else:
                continue  # Can't create interface without asset
        for dst_mac, count in dsts.items():
            # Search or create destination interface
            dst_iface = mac_to_interface.get(dst_mac)
            if not dst_iface:
                dst_asset = mac_to_asset.get(dst_mac)
                if dst_asset:
                    dst_iface_data = AssetInterfaceCreate(
                        asset_id=dst_asset.id,
                        tenant_id=tenant_id,
                        name="Auto-imported",
                        type="ethernet",
                        mac_address=dst_mac,
                        vlan=None,
                        logical_port=None,
                        physical_plug_label=None,
                    )
                    dst_iface = create_interface(session, dst_iface_data)
                    mac_to_interface[dst_mac] = dst_iface
                else:
                    continue  # Can't create interface without asset

            # Search existing record
            comm = (
                session.query(AssetCommunication)
                .filter_by(
                    src_interface_id=src_iface.id,
                    dst_interface_id=dst_iface.id,
                    tenant_id=tenant_id,
                    site_id=site_id,
                )
                .first()
            )

            if comm:
                comm.packet_count = count  # or += count if you want to accumulate
            else:
                comm = AssetCommunication(
                    src_interface_id=src_iface.id,
                    dst_interface_id=dst_iface.id,
                    packet_count=count,
                    tenant_id=tenant_id,
                    site_id=site_id,
                )
                session.add(comm)

    session.commit()
