"""Helpers to serialize assets for PDF generation and normalize print options."""

from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.asset import Asset, asset_contacts
from app.models.asset_connection import AssetConnection


def merge_print_options(
    template_options: Optional[Dict[str, Any]],
    request_options: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    merged = dict(template_options or {})
    merged.update(request_options or {})
    return merged


def option_enabled(
    options: Optional[Dict[str, Any]], *names: str, default: bool = True
) -> bool:
    if not options:
        return default
    for name in names:
        if name in options:
            return bool(options[name])
    return default


def _rel_name(obj, default=None):
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get("name", default)
    return getattr(obj, "name", default)


def _rel_dict(obj, *fields):
    if obj is None:
        return None
    data = {}
    for field in fields:
        data[field] = getattr(obj, field, None)
    return data


def asset_to_print_dict(
    db: Session,
    asset: Asset,
    asset_id: UUID,
    connections: Optional[List[AssetConnection]] = None,
) -> Dict[str, Any]:
    """Build a JSON-serializable dict of an asset and its relations for PDF rendering."""
    contact_roles = {}
    if asset.contacts:
        rows = db.execute(
            select(asset_contacts.c.contact_id, asset_contacts.c.role).where(
                asset_contacts.c.asset_id == asset_id
            )
        ).fetchall()
        contact_roles = {contact_id: role for contact_id, role in rows}

    connection_rows = []
    for conn in connections or []:
        if conn.parent_asset_id == asset_id and conn.child_asset:
            target_name = conn.child_asset.name
        elif conn.child_asset_id == asset_id and conn.parent_asset:
            target_name = conn.parent_asset.name
        else:
            target_name = None
        connection_rows.append(
            {
                "connection_type": conn.connection_type,
                "target_asset": {"name": target_name} if target_name else None,
                "port_parent": conn.port_parent,
                "port_child": conn.port_child,
                "protocol": conn.protocol,
                "description": conn.description,
                "local_interface": _rel_dict(conn.local_interface, "name"),
                "remote_interface": _rel_dict(conn.remote_interface, "name"),
            }
        )

    return {
        "id": asset.id,
        "tenant_id": asset.tenant_id,
        "name": asset.name,
        "tag": asset.tag,
        "description": asset.description,
        "serial_number": asset.serial_number,
        "model": asset.model,
        "firmware_version": asset.firmware_version,
        "remote_access": asset.remote_access,
        "remote_access_type": asset.remote_access_type,
        "last_update_date": asset.last_update_date,
        "custom_fields": asset.custom_fields or {},
        "created_at": asset.created_at,
        "updated_at": asset.updated_at,
        "last_seen": asset.last_seen,
        "installation_date": asset.installation_date,
        "business_criticality": asset.business_criticality,
        "impact_value": asset.impact_value,
        "physical_access_ease": asset.physical_access_ease,
        "purdue_level": asset.purdue_level,
        "exposure_level": asset.exposure_level,
        "update_status": asset.update_status,
        "risk_score": asset.risk_score,
        "last_risk_assessment": asset.last_risk_assessment,
        "protocols": asset.protocols or [],
        "security_zone": _rel_dict(asset.security_zone, "id", "name"),
        "area": _rel_dict(asset.area, "id", "name", "code"),
        "asset_type": {"name": _rel_name(asset.asset_type)} if asset.asset_type else None,
        "status": {"name": _rel_name(asset.status)} if asset.status else None,
        "site": {"name": _rel_name(asset.site)} if asset.site else None,
        "location": {"name": _rel_name(asset.location)} if asset.location else None,
        "manufacturer": (
            {"name": _rel_name(asset.manufacturer)} if asset.manufacturer else None
        ),
        "photos": [
            {"file_path": photo.file_path, "uploaded_at": photo.uploaded_at}
            for photo in (asset.photos or [])
        ],
        "documents": [
            {
                "name": doc.name,
                "file_path": doc.file_path,
                "description": doc.description,
                "uploaded_at": doc.uploaded_at,
            }
            for doc in (asset.documents or [])
        ],
        "connections": connection_rows,
        "contacts": [
            {
                "first_name": contact.first_name or "",
                "last_name": contact.last_name or "",
                "email": contact.email or "",
                "phone1": contact.phone1 or "",
                "phone2": contact.phone2 or "",
                "type": contact.type or "",
                "notes": contact.notes or "",
                "role": contact_roles.get(contact.id, "other"),
            }
            for contact in (asset.contacts or [])
        ],
        "suppliers": [
            {
                "name": supplier.name or "",
                "email": supplier.email or "",
                "phone": supplier.phone or "",
                "website": supplier.website or "",
                "notes": supplier.notes or "",
            }
            for supplier in (asset.suppliers or [])
        ],
        "interfaces": [
            {
                "id": str(iface.id) if iface.id else None,
                "name": iface.name or "",
                "type": iface.type or "",
                "ip_address": iface.ip_address or "",
                "mac_address": iface.mac_address or "",
                "vlan": iface.vlan or "",
                "default_gateway": iface.default_gateway or "",
                "subnet_mask": iface.subnet_mask or "",
                "logical_port": iface.logical_port or "",
                "physical_plug_label": iface.physical_plug_label or "",
            }
            for iface in (asset.interfaces or [])
        ],
    }
