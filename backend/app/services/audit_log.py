# backend/services/audit_log.py
import json
from app.models.audit_log import AuditLog
from sqlalchemy.orm import Session
from typing import Optional, Any, Dict
import uuid
import datetime

REDACTED_VALUE = "[REDACTED]"

SENSITIVE_KEY_NAMES = frozenset(
    {
        "api_key",
        "key_hash",
        "password",
        "password_hash",
        "client_secret",
        "client_secret_encrypted",
        "secret",
        "access_token",
        "refresh_token",
        "private_key",
    }
)

NON_SENSITIVE_KEY_NAMES = frozenset(
    {
        "password_change_required",
    }
)


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower()
    if normalized in NON_SENSITIVE_KEY_NAMES:
        return False
    if normalized in SENSITIVE_KEY_NAMES:
        return True
    if normalized.endswith("_secret") or normalized.endswith("_password"):
        return True
    if "password" in normalized:
        return True
    return False


def redact_sensitive_data(data: Any) -> Any:
    """Remove or mask secrets before persisting audit log payloads."""
    if data is None:
        return None

    if isinstance(data, str):
        try:
            parsed = json.loads(data)
        except (json.JSONDecodeError, TypeError):
            return data
        redacted = redact_sensitive_data(parsed)
        return json.dumps(redacted, indent=2, ensure_ascii=False)

    if isinstance(data, dict):
        redacted: Dict[str, Any] = {}
        for key, value in data.items():
            if _is_sensitive_key(key):
                redacted[key] = REDACTED_VALUE if value not in (None, "") else value
            else:
                redacted[key] = redact_sensitive_data(value)
        return redacted

    if isinstance(data, list):
        return [redact_sensitive_data(item) for item in data]

    return data


def clean_dict(obj: Any) -> dict:
    if not obj:
        return {}
    
    result = {}
    
    # Se è un oggetto SQLAlchemy, usa __table__.columns per ottenere i campi
    if hasattr(obj, '_sa_instance_state'):
        for column in obj.__table__.columns:
            key = column.name
            value = getattr(obj, key, None)
            if not key.startswith("_"):
                # Escludi valori tipo funzioni, metodi, classi, ecc.
                if not callable(value):
                    result[key] = value
    # Se è un dizionario, usa il metodo originale
    elif hasattr(obj, 'items'):
        for k, v in obj.items():
            if k.startswith("_"):
                continue
            # Escludi valori tipo funzioni, metodi, classi, ecc.
            if callable(v):
                continue
            result[k] = v
    else:
        # Fallback: prova a convertire in stringa
        result = {"value": str(obj)}
    
    return result


def get_entity_name_by_id(
    db: Session, entity_type: str, entity_id: uuid.UUID, tenant_id: uuid.UUID
) -> Optional[str]:
    """Recupera il nome di un'entità dal suo ID"""
    if not entity_id:
        return None

    try:
        if entity_type == "Asset":
            from app.models.asset import Asset

            obj = (
                db.query(Asset)
                .filter(Asset.id == entity_id, Asset.tenant_id == tenant_id)
                .first()
            )
            return obj.name if obj else None
        elif entity_type == "Site":
            from app.models.site import Site

            obj = (
                db.query(Site)
                .filter(Site.id == entity_id, Site.tenant_id == tenant_id)
                .first()
            )
            return obj.name if obj else None
        elif entity_type == "Location":
            from app.models.location import Location

            obj = (
                db.query(Location)
                .filter(Location.id == entity_id, Location.tenant_id == tenant_id)
                .first()
            )
            return obj.name if obj else None
        elif entity_type == "AssetType":
            from app.models.asset_type import AssetType

            obj = (
                db.query(AssetType)
                .filter(AssetType.id == entity_id, AssetType.tenant_id == tenant_id)
                .first()
            )
            return obj.name if obj else None
        elif entity_type == "AssetStatus":
            from app.models.asset_status import AssetStatus

            obj = (
                db.query(AssetStatus)
                .filter(AssetStatus.id == entity_id, AssetStatus.tenant_id == tenant_id)
                .first()
            )
            return obj.name if obj else None
        elif entity_type == "Manufacturer":
            from app.models.manufacturer import Manufacturer

            obj = (
                db.query(Manufacturer)
                .filter(
                    Manufacturer.id == entity_id, Manufacturer.tenant_id == tenant_id
                )
                .first()
            )
            return obj.name if obj else None
        elif entity_type == "Supplier":
            from app.models.supplier import Supplier

            obj = (
                db.query(Supplier)
                .filter(Supplier.id == entity_id, Supplier.tenant_id == tenant_id)
                .first()
            )
            return obj.name if obj else None
        elif entity_type == "Contact":
            from app.models.contact import Contact

            obj = (
                db.query(Contact)
                .filter(Contact.id == entity_id, Contact.tenant_id == tenant_id)
                .first()
            )
            return f"{obj.first_name} {obj.last_name}" if obj else None
        elif entity_type == "User":
            from app.models.user import User

            obj = (
                db.query(User)
                .filter(User.id == entity_id, User.tenant_id == tenant_id)
                .first()
            )
            return obj.name or obj.email if obj else None
        elif entity_type == "Role":
            from app.models.role import Role

            obj = (
                db.query(Role)
                .filter(Role.id == entity_id, Role.tenant_id == tenant_id)
                .first()
            )
            return obj.name if obj else None
        elif entity_type == "NetworkProbe":
            from app.models.network_probe import NetworkProbe

            obj = (
                db.query(NetworkProbe)
                .filter(NetworkProbe.id == entity_id, NetworkProbe.tenant_id == tenant_id)
                .first()
            )
            return obj.name if obj else None
        elif entity_type == "DiscoveredDevice":
            from app.models.discovered_device import DiscoveredDevice

            obj = (
                db.query(DiscoveredDevice)
                .filter(
                    DiscoveredDevice.id == entity_id,
                    DiscoveredDevice.tenant_id == tenant_id,
                )
                .first()
            )
            if not obj:
                return None
            return obj.hostname or obj.mac_address or str(entity_id)
        elif entity_type == "SecurityZone":
            from app.models.security_zone import SecurityZone

            obj = (
                db.query(SecurityZone)
                .filter(
                    SecurityZone.id == entity_id, SecurityZone.tenant_id == tenant_id
                )
                .first()
            )
            return obj.name if obj else None
        elif entity_type == "Conduit":
            from app.models.conduit import Conduit

            obj = (
                db.query(Conduit)
                .filter(Conduit.id == entity_id, Conduit.tenant_id == tenant_id)
                .first()
            )
            return obj.name if obj else None
        elif entity_type == "ApiKey":
            from app.models.api_key import ApiKey

            obj = (
                db.query(ApiKey)
                .filter(ApiKey.id == entity_id, ApiKey.tenant_id == tenant_id)
                .first()
            )
            return obj.name if obj else None
        elif entity_type == "Tenant":
            from app.models.tenant import Tenant

            obj = db.query(Tenant).filter(Tenant.id == entity_id).first()
            return obj.name if obj else None
    except Exception:
        return None

    return None


def resolve_audit_language(user=None, request=None) -> str:
    """Resolve audit log language from request Accept-Language header."""
    if request is not None:
        accept = (request.headers.get("Accept-Language") or "").lower()
        if accept.startswith("it") or ",it" in accept.split(";")[0]:
            return "it"
    return "en"


ENTITY_LABELS: Dict[str, Dict[str, str]] = {
    "en": {
        "Asset": "device",
        "Site": "site",
        "Location": "location",
        "AssetType": "device type",
        "AssetStatus": "device status",
        "Manufacturer": "manufacturer",
        "Supplier": "supplier",
        "Contact": "contact",
        "User": "user",
        "Role": "role",
        "Area": "area",
        "ApiKey": "API key",
        "AssetDocument": "asset document",
        "AssetPhoto": "asset photo",
        "AssetInterface": "asset interface",
        "AssetConnection": "asset connection",
        "AssetDependency": "asset dependency",
        "AssetCapability": "asset capability",
        "SecurityZone": "security zone",
        "AssetZoneMembership": "zone membership",
        "Conduit": "conduit",
        "Vulnerability": "vulnerability",
        "VulnerabilityFeedSource": "vulnerability feed",
        "AssetVulnerability": "asset vulnerability",
        "TenantSSOConfig": "SSO configuration",
        "TenantFeatures": "tenant features",
        "LocationFloorplan": "floor plan",
        "SupplierDocument": "supplier document",
        "NotificationPreference": "notification preference",
        "NetworkProbe": "network probe",
        "DiscoveredDevice": "discovered device",
        "TenantSyslogConfig": "syslog configuration",
        "Tenant": "tenant",
    },
    "it": {
        "Asset": "dispositivo",
        "Site": "sito",
        "Location": "posizione",
        "AssetType": "tipo dispositivo",
        "AssetStatus": "stato dispositivo",
        "Manufacturer": "produttore",
        "Supplier": "fornitore",
        "Contact": "contatto",
        "User": "utente",
        "Role": "ruolo",
        "Area": "area",
        "ApiKey": "API key",
        "AssetDocument": "documento dispositivo",
        "AssetPhoto": "foto dispositivo",
        "AssetInterface": "interfaccia dispositivo",
        "AssetConnection": "connessione dispositivo",
        "AssetDependency": "dipendenza dispositivo",
        "AssetCapability": "capability dispositivo",
        "SecurityZone": "security zone",
        "AssetZoneMembership": "appartenenza zona",
        "Conduit": "conduit",
        "Vulnerability": "vulnerabilità",
        "VulnerabilityFeedSource": "feed vulnerabilità",
        "AssetVulnerability": "vulnerabilità dispositivo",
        "TenantSSOConfig": "configurazione SSO",
        "TenantFeatures": "funzionalità tenant",
        "LocationFloorplan": "planimetria",
        "SupplierDocument": "documento fornitore",
        "NotificationPreference": "preferenza notifica",
        "NetworkProbe": "sonda di rete",
        "DiscoveredDevice": "dispositivo scoperto",
        "TenantSyslogConfig": "configurazione syslog",
        "Tenant": "tenant",
    },
}

ACTION_TEMPLATES: Dict[str, Dict[str, str]] = {
    "en": {
        "create": "Created {entity_label} '{entity_identifier}'",
        "update": "Updated {entity_label} '{entity_identifier}'",
        "delete": "Deleted {entity_label} '{entity_identifier}'",
        "bulk_update": "Bulk update: changed {fields} for '{entity_identifier}'",
        "bulk_soft_delete": "Bulk soft delete of {entity_label}",
        "soft_delete": "Moved {entity_label} '{entity_identifier}' to trash",
        "restore": "Restored {entity_label} '{entity_identifier}'",
        "hard_delete": "Permanently deleted {entity_label} '{entity_identifier}'",
        "empty_trash": "Emptied trash for {entity_label}",
        "login": "User login {entity_identifier}",
        "logout": "User logout {entity_identifier}",
        "api_key_used": "API Key '{entity_identifier}' used from {ip_address}",
        "mark_asset_reviewed": "Marked {entity_label} '{entity_identifier}' as reviewed",
        "skip_asset_review": "Skipped review for {entity_label} '{entity_identifier}'",
        "bulk_mark_assets_reviewed": "Bulk marked assets as reviewed",
        "recalculate_all_review_dates": "Recalculated review dates for assets",
        "reset_password": "Reset password for {entity_label} '{entity_identifier}'",
        "deauthorize": "Deauthorized {entity_label} '{entity_identifier}'",
        "onboard": "Onboarded {entity_label} '{entity_identifier}' from discovery",
        "sso_login": "SSO login via {provider} for {entity_identifier}",
        "import_users": "Imported {imported} users, skipped {skipped}",
        "update_vulnerability_status": "Updated vulnerability status to {status} for '{entity_identifier}'",
        "create_security_zone": "Created {entity_label} '{entity_identifier}'",
        "update_security_zone": "Updated {entity_label} '{entity_identifier}'",
        "delete_security_zone": "Deleted {entity_label} '{entity_identifier}'",
        "create_conduit": "Created {entity_label} '{entity_identifier}'",
        "update_conduit": "Updated {entity_label} '{entity_identifier}'",
        "delete_conduit": "Deleted {entity_label} '{entity_identifier}'",
        "default": "{action} {entity_label} '{entity_identifier}'",
    },
    "it": {
        "create": "Creato {entity_label} '{entity_identifier}'",
        "update": "Aggiornato {entity_label} '{entity_identifier}'",
        "delete": "Eliminato {entity_label} '{entity_identifier}'",
        "bulk_update": "Aggiornamento massivo: modificati {fields} per '{entity_identifier}'",
        "bulk_soft_delete": "Eliminazione massiva nel cestino di {entity_label}",
        "soft_delete": "Spostato {entity_label} '{entity_identifier}' nel cestino",
        "restore": "Ripristinato {entity_label} '{entity_identifier}'",
        "hard_delete": "Eliminato definitivamente {entity_label} '{entity_identifier}'",
        "empty_trash": "Svuotato cestino per {entity_label}",
        "login": "Login utente {entity_identifier}",
        "logout": "Logout utente {entity_identifier}",
        "api_key_used": "API Key '{entity_identifier}' utilizzata da {ip_address}",
        "mark_asset_reviewed": "Revisione completata per {entity_label} '{entity_identifier}'",
        "skip_asset_review": "Revisione saltata per {entity_label} '{entity_identifier}'",
        "bulk_mark_assets_reviewed": "Revisione massiva completata per i dispositivi",
        "recalculate_all_review_dates": "Ricalcolate le date di revisione dei dispositivi",
        "reset_password": "Reset password per {entity_label} '{entity_identifier}'",
        "deauthorize": "De-autorizzata {entity_label} '{entity_identifier}'",
        "onboard": "Onboarding {entity_label} '{entity_identifier}' da discovery",
        "sso_login": "Login SSO via {provider} per {entity_identifier}",
        "import_users": "Importati {imported} utenti, saltati {skipped}",
        "update_vulnerability_status": "Aggiornato stato vulnerabilità a {status} per '{entity_identifier}'",
        "create_security_zone": "Creata {entity_label} '{entity_identifier}'",
        "update_security_zone": "Aggiornata {entity_label} '{entity_identifier}'",
        "delete_security_zone": "Eliminata {entity_label} '{entity_identifier}'",
        "create_conduit": "Creato {entity_label} '{entity_identifier}'",
        "update_conduit": "Aggiornato {entity_label} '{entity_identifier}'",
        "delete_conduit": "Eliminato {entity_label} '{entity_identifier}'",
        "default": "{action} {entity_label} '{entity_identifier}'",
    },
}


def translate_ids_in_data(db: Session, data: Any, tenant_id: uuid.UUID) -> Any:
    """Traduce gli ID nei dati JSON in nomi leggibili"""
    if not data:
        return data

    # If it's a JSON string, parse it
    if isinstance(data, str):
        try:
            parsed_data = json.loads(data)
            translated = translate_ids_in_data(db, parsed_data, tenant_id)
            return json.dumps(translated, indent=2, ensure_ascii=False)
        except Exception:
            return data

    # If it's a dictionary, translate ID fields
    if isinstance(data, dict):
        translated = {}
        for key, value in data.items():
            if key.endswith("_id") and value:
                # Determine entity type from field name
                entity_type_map = {
                    "site_id": "Site",
                    "location_id": "Location",
                    "asset_type_id": "AssetType",
                    "asset_status_id": "AssetStatus",
                    "status_id": "AssetStatus",  # AGGIUNTO
                    "manufacturer_id": "Manufacturer",
                    "supplier_id": "Supplier",
                    "contact_id": "Contact",
                    "user_id": "User",
                }

                entity_type = entity_type_map.get(key)
                if entity_type:
                    try:
                        entity_uuid = (
                            uuid.UUID(value) if isinstance(value, str) else value
                        )
                        name = get_entity_name_by_id(
                            db, entity_type, entity_uuid, tenant_id
                        )
                        if name:
                            translated[f"{key}_name"] = name
                        translated[key] = value
                    except Exception:
                        translated[key] = value
                else:
                    translated[key] = value
            else:
                translated[key] = value
        return translated

    # If it's a list, translate each element
    if isinstance(data, list):
        return [translate_ids_in_data(db, item, tenant_id) for item in data]

    return data


def create_readable_description(
    action: str,
    entity: str,
    entity_id: Optional[uuid.UUID],
    entity_name: Optional[str] = None,
    old_data: Optional[Any] = None,
    new_data: Optional[Any] = None,
    language: str = "en",
    **context: Any,
) -> str:
    """Create a human-readable audit log description."""
    labels = ENTITY_LABELS.get(language, ENTITY_LABELS["en"])
    templates = ACTION_TEMPLATES.get(language, ACTION_TEMPLATES["en"])
    unknown = "sconosciuto" if language == "it" else "unknown"

    entity_identifier = entity_name or (str(entity_id) if entity_id else unknown)
    entity_label = labels.get(entity, entity.replace("_", " ").lower())

    fields = context.get("fields")
    if not fields and isinstance(new_data, dict) and action == "bulk_update":
        fields = ", ".join(new_data.keys())

    template = templates.get(action, templates["default"])
    format_args = {
        "entity_label": entity_label,
        "entity_identifier": entity_identifier,
        "action": action.replace("_", " "),
        "fields": fields or ("-" if language == "en" else "-"),
        "ip_address": context.get("ip_address") or unknown,
        "provider": context.get("provider") or unknown,
        "imported": context.get("imported", 0),
        "skipped": context.get("skipped", 0),
        "status": context.get("status") or unknown,
    }
    try:
        return template.format(**format_args)
    except (KeyError, ValueError):
        return templates["default"].format(**format_args)


def create_audit_log(
    db: Session,
    user_id: uuid.UUID,
    tenant_id: uuid.UUID,
    action: str,
    entity: str,
    entity_id: Optional[uuid.UUID] = None,
    old_data: Optional[Any] = None,
    new_data: Optional[Any] = None,
    description: Optional[str] = None,
    ip_address: Optional[str] = None,
    commit: bool = True,
    language: str = "en",
    **context: Any,
):

    def serialize(data):
        import datetime

        if data is None:
            return None

        def default(o):
            if isinstance(o, (uuid.UUID, datetime.datetime, datetime.date)):
                return str(o)
            return str(o)

        try:
            if isinstance(data, dict):
                return json.dumps(data, indent=2, default=default)
            if hasattr(data, "__dict__"):
                clean = clean_dict(data.__dict__)
                return json.dumps(clean, indent=2, default=default)
            return json.dumps(str(data), indent=2, default=default)
        except Exception:
            return str(data)

            # Translate IDs in data to make them more readable
    old_data_with_names = redact_sensitive_data(
        translate_ids_in_data(db, old_data, tenant_id)
    )
    new_data_with_names = redact_sensitive_data(
        translate_ids_in_data(db, new_data, tenant_id)
    )

            # Get the main entity name
    entity_name = (
        get_entity_name_by_id(db, entity, entity_id, tenant_id) if entity_id else None
    )

    # Crea una descrizione leggibile
    readable_description = create_readable_description(
        action,
        entity,
        entity_id,
        entity_name,
        old_data_with_names,
        new_data_with_names,
        language,
        ip_address=ip_address or context.get("ip_address"),
        **context,
    )

    audit_entry = AuditLog(
        user_id=user_id,
        tenant_id=tenant_id,
        action=action,
        entity=entity,
        entity_id=entity_id,
        old_data=serialize(old_data_with_names),
        new_data=serialize(new_data_with_names),
        description=description or readable_description,
        ip_address=ip_address,
    )
    db.add(audit_entry)
    if commit:
        db.commit()
    # Inoltro verso server syslog esterno se configurato (non blocca in caso di errore)
    try:
        from app.services.syslog_forwarder import forward_audit_entry_to_syslog
        forward_audit_entry_to_syslog(db, audit_entry)
    except Exception:
        pass  # Ignorato: l'audit è già salvato in DB
    return audit_entry
