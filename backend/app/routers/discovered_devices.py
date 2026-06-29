from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, false
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

from app.database import get_db
from app.services.auth import get_current_user
from app.services.rbac import require_section_access
from app.models.user import User
from app.models.discovered_device import DiscoveredDevice, DeviceDiscoveryStatus
from app.models.asset import Asset
from app.models.asset_interface import AssetInterface
from app.models.asset_type import AssetType
from app.models.asset_status import AssetStatus
from app.models.manufacturer import Manufacturer
from app.schemas.asset_interface import AssetInterfaceCreate
from app.crud.asset_interface import create_interface
from app.schemas.discovered_device import (
    DiscoveredDeviceRead,
    DiscoveredDeviceReadEnriched,
    DiscoveredDeviceUpdate,
    DiscoveredDeviceOnboardRequest,
    DiscoveredDeviceOnboardResponse,
    DiscoveredDeviceMatchCandidate,
)
from app.services.oui_lookup import lookup_vendor_by_mac
from app.services.audit_decorator import audit_log_action


# NOTE: gli altri router dell'app sono montati senza prefisso `/api`, mentre
# il frontend chiama sempre `/api/...`. Rimuoviamo quindi `/api` da qui per
# evitare un doppio prefisso.
router = APIRouter(
    prefix="/discovered-devices",
    tags=["discovered-devices"],
    dependencies=[Depends(require_section_access("network_probes"))],
)


@router.get("", response_model=List[DiscoveredDeviceReadEnriched])
async def list_discovered_devices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[DeviceDiscoveryStatus] = Query(None, alias="status"),
    probe_id: Optional[UUID] = Query(None),
    site_id: Optional[UUID] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(DiscoveredDevice).filter(DiscoveredDevice.tenant_id == current_user.tenant_id)

    if status_filter:
        query = query.filter(DiscoveredDevice.status == status_filter)
    if probe_id:
        query = query.filter(DiscoveredDevice.probe_id == probe_id)
    if site_id:
        query = query.filter(DiscoveredDevice.site_id == site_id)
    if search:
        term = f"%{search}%"
        query = query.filter(
            or_(
                DiscoveredDevice.mac_address.ilike(term),
                DiscoveredDevice.hostname.ilike(term),
                DiscoveredDevice.vendor.ilike(term),
            )
        )

    devices = query.order_by(DiscoveredDevice.created_at.desc()).offset(skip).limit(limit).all()
    if not devices:
        return []

    tenant_id = current_user.tenant_id
    macs = {d.mac_address for d in devices if d.mac_address}
    ips = {ip for d in devices for ip in (d.ip_addresses or []) if ip}

    candidate_interfaces_query = (
        db.query(AssetInterface, Asset)
        .join(
            Asset,
            and_(Asset.id == AssetInterface.asset_id, Asset.deleted_at.is_(None)),
        )
        .filter(Asset.tenant_id == tenant_id, AssetInterface.tenant_id == tenant_id)
    )
    if macs or ips:
        candidate_interfaces_query = candidate_interfaces_query.filter(
            or_(
                AssetInterface.mac_address.in_(list(macs)) if macs else false(),
                AssetInterface.ip_address.in_(list(ips)) if ips else false(),
            )
        )
    candidate_rows = candidate_interfaces_query.all()

    mac_matches: dict = {}
    ip_matches: dict = {}
    for iface, asset in candidate_rows:
        if iface.mac_address:
            mac_key = iface.mac_address.lower()
            mac_matches.setdefault(mac_key, []).append((iface, asset))
        if iface.ip_address:
            ip_matches.setdefault(iface.ip_address, []).append((iface, asset))

    response = []
    for device in devices:
        unique_possible = []
        seen = set()

        if device.mac_address:
            for iface, asset in mac_matches.get(device.mac_address.lower(), []):
                key = (str(asset.id), "mac", None, iface.mac_address)
                if key in seen:
                    continue
                seen.add(key)
                unique_possible.append(
                    DiscoveredDeviceMatchCandidate(
                        asset_id=asset.id,
                        asset_name=asset.name,
                        match_type="mac",
                        matched_mac=iface.mac_address,
                        matched_ip=None,
                    )
                )

        for ip in device.ip_addresses or []:
            for iface, asset in ip_matches.get(ip, []):
                key = (str(asset.id), "ip", ip, iface.mac_address)
                if key in seen:
                    continue
                seen.add(key)
                unique_possible.append(
                    DiscoveredDeviceMatchCandidate(
                        asset_id=asset.id,
                        asset_name=asset.name,
                        match_type="ip",
                        matched_mac=None,
                        matched_ip=ip,
                    )
                )

        best_match = None
        for candidate in unique_possible:
            if candidate.match_type == "mac":
                best_match = candidate
                break
        if not best_match and unique_possible:
            best_match = unique_possible[0]

        payload = DiscoveredDeviceRead.model_validate(device).model_dump()
        payload["vendor"] = lookup_vendor_by_mac(device.mac_address, default=device.vendor or "Unknown Vendor")
        payload["possible_matches"] = [m.model_dump() for m in unique_possible]
        payload["best_match_asset_id"] = best_match.asset_id if best_match else None
        payload["best_match_asset_name"] = best_match.asset_name if best_match else None
        payload["best_match_type"] = best_match.match_type if best_match else None
        response.append(payload)

    return response


@router.get("/{device_id}", response_model=DiscoveredDeviceRead)
async def get_discovered_device(
    device_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    device = (
        db.query(DiscoveredDevice)
        .filter(and_(DiscoveredDevice.id == device_id, DiscoveredDevice.tenant_id == current_user.tenant_id))
        .first()
    )
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispositivo non trovato")
    return device


@router.put("/{device_id}", response_model=DiscoveredDeviceRead)
@audit_log_action("update", "DiscoveredDevice", model_class=DiscoveredDevice)
async def update_discovered_device(
    device_id: UUID,
    update_data: DiscoveredDeviceUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    device = (
        db.query(DiscoveredDevice)
        .filter(and_(DiscoveredDevice.id == device_id, DiscoveredDevice.tenant_id == current_user.tenant_id))
        .first()
    )
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispositivo non trovato")

    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(device, field, value)

    db.commit()
    db.refresh(device)
    return device


@router.post("/{device_id}/onboard", response_model=DiscoveredDeviceOnboardResponse)
@audit_log_action("onboard", "DiscoveredDevice", model_class=DiscoveredDevice)
async def onboard_discovered_device(
    device_id: UUID,
    request_data: DiscoveredDeviceOnboardRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    device = (
        db.query(DiscoveredDevice)
        .filter(and_(DiscoveredDevice.id == device_id, DiscoveredDevice.tenant_id == current_user.tenant_id))
        .first()
    )
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispositivo non trovato")

    if device.matched_asset_id:
        existing_asset = (
            db.query(Asset)
            .filter(and_(Asset.id == device.matched_asset_id, Asset.tenant_id == current_user.tenant_id))
            .first()
        )
        if existing_asset:
            return DiscoveredDeviceOnboardResponse(
                discovered_device_id=device.id,
                asset_id=existing_asset.id,
                asset_name=existing_asset.name,
            )

    asset_type = (
        db.query(AssetType)
        .filter(
            or_(AssetType.tenant_id == current_user.tenant_id, AssetType.tenant_id.is_(None)),
            AssetType.name.ilike("Network Device"),
        )
        .first()
    ) or db.query(AssetType).filter(
        or_(AssetType.tenant_id == current_user.tenant_id, AssetType.tenant_id.is_(None))
    ).first()
    if not asset_type:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Asset type non disponibile")

    asset_status = (
        db.query(AssetStatus)
        .filter(
            AssetStatus.tenant_id == current_user.tenant_id,
            or_(AssetStatus.name == "Active", AssetStatus.name == "Attivo"),
        )
        .first()
    ) or db.query(AssetStatus).filter(AssetStatus.tenant_id == current_user.tenant_id).first()
    if not asset_status:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Asset status non disponibile")

    resolved_vendor = lookup_vendor_by_mac(device.mac_address, default=device.vendor or "Unknown Vendor")
    manufacturer = (
        db.query(Manufacturer)
        .filter(
            Manufacturer.tenant_id == current_user.tenant_id,
            Manufacturer.name == resolved_vendor,
        )
        .first()
    )
    if not manufacturer and resolved_vendor:
        manufacturer = Manufacturer(tenant_id=current_user.tenant_id, name=resolved_vendor)
        db.add(manufacturer)
        db.flush()

    preferred_ip = (device.ip_addresses or [None])[0]
    suggested_name = request_data.name or device.hostname or (f"Discovered {preferred_ip}" if preferred_ip else f"Discovered {device.mac_address}")

    asset = Asset(
        tenant_id=current_user.tenant_id,
        site_id=device.site_id,
        asset_type_id=asset_type.id,
        status_id=asset_status.id,
        manufacturer_id=manufacturer.id if manufacturer else None,
        name=suggested_name,
        tag=request_data.tag,
        protocols=device.protocols or [],
        custom_fields={
            "discovered_device_id": str(device.id),
            "discovered_by_probe_id": str(device.probe_id),
        },
        description=f"Onboarded from discovered device {device.mac_address}",
    )
    db.add(asset)
    db.flush()

    if device.mac_address or preferred_ip:
        iface_data = AssetInterfaceCreate(
            asset_id=asset.id,
            tenant_id=current_user.tenant_id,
            name="eth0",
            type="ethernet",
            ip_address=preferred_ip,
            mac_address=device.mac_address,
            protocols=device.protocols or [],
        )
        create_interface(db, iface_data)

    device.status = DeviceDiscoveryStatus.IMPORTED.value
    device.matched_asset_id = asset.id
    device.match_confidence = 100
    device.match_reason = "onboarded"
    device.processed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(asset)
    db.refresh(device)

    return DiscoveredDeviceOnboardResponse(
        discovered_device_id=device.id,
        asset_id=asset.id,
        asset_name=asset.name,
    )
