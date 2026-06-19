# backend/services/audit_log.py
import json
from app.models.audit_log import AuditLog
from sqlalchemy.orm import Session
from typing import Optional, Any, Dict
import uuid
import datetime


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
    except Exception:
        return None

    return None


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
) -> str:
    """Crea una descrizione leggibile per l'audit log"""
    TRANSLATIONS = {
        "en": {
            "unknown": "unknown",
            "Asset": "device",
            "Site": "site",
            "Location": "location",
            "AssetType": "device type",
            "AssetStatus": "device status",
            "Manufacturer": "manufacturer",
            "Supplier": "supplier",
            "Contact": "contact",
            "User": "user",
            "create": "Created {entity_label} '{entity_identifier}'",
            "update": "Updated {entity_label} '{entity_identifier}'",
            "delete": "Deleted {entity_label} '{entity_identifier}'",
            "bulk_update": "Bulk update of {entity_label}",
            "default": "{action} {entity_label} '{entity_identifier}'",
        },
        "it": {
            "unknown": "sconosciuto",
            "Asset": "dispositivo",
            "Site": "sito",
            "Location": "posizione",
            "AssetType": "tipo dispositivo",
            "AssetStatus": "stato dispositivo",
            "Manufacturer": "produttore",
            "Supplier": "fornitore",
            "Contact": "contatto",
            "User": "utente",
            "create": "Creato {entity_label} '{entity_identifier}'",
            "update": "Aggiornato {entity_label} '{entity_identifier}'",
            "delete": "Eliminato {entity_label} '{entity_identifier}'",
            "bulk_update": "Aggiornamento massivo di {entity_label}",
            "default": "{action} {entity_label} '{entity_identifier}'",
        },
    }
    t = TRANSLATIONS.get(language, TRANSLATIONS["en"])
            # Use entity name if available, otherwise the ID
    entity_identifier = entity_name or str(entity_id) if entity_id else t["unknown"]
            # Translate entity names
    entity_label = t.get(entity, entity.lower())
    # Crea la descrizione base
    if action == "create":
        return t["create"].format(
            entity_label=entity_label, entity_identifier=entity_identifier
        )
    elif action == "update":
        return t["update"].format(
            entity_label=entity_label, entity_identifier=entity_identifier
        )
    elif action == "delete":
        return t["delete"].format(
            entity_label=entity_label, entity_identifier=entity_identifier
        )
    elif action == "bulk_update":
        return t["bulk_update"].format(entity_label=entity_label)
    else:
        return t["default"].format(
            action=action.capitalize(),
            entity_label=entity_label,
            entity_identifier=entity_identifier,
        )


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
    commit: bool = True,  # Commit di default a True per sicurezza
    language: str = "en",  # Nuovo parametro lingua
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
    old_data_with_names = translate_ids_in_data(db, old_data, tenant_id)
    new_data_with_names = translate_ids_in_data(db, new_data, tenant_id)

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
