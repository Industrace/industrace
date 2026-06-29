from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from uuid import UUID
from app.models.print_template import PrintTemplate
from app.schemas.print_template import PrintTemplateCreate, PrintTemplateUpdate
from app.utils import sanitize_text_fields


def get_print_template(db: Session, template_id: int) -> Optional[PrintTemplate]:
    """Retrieve a print template by ID"""
    return db.query(PrintTemplate).filter(PrintTemplate.id == template_id).first()


def get_print_template_by_key(
    db: Session, key: str, tenant_id: Optional[UUID] = None
) -> Optional[PrintTemplate]:
    """Retrieve a print template by key and tenant (or global)"""
    query = db.query(PrintTemplate).filter(PrintTemplate.key == key)
    if tenant_id:
        query = query.filter(
            (PrintTemplate.tenant_id == tenant_id) | (PrintTemplate.tenant_id == None)
        )
    return query.first()


def get_print_templates(
    db: Session, tenant_id: Optional[UUID] = None, skip: int = 0, limit: int = 100
) -> List[PrintTemplate]:
    """Retrieve all print templates for tenant (or global)"""
    query = db.query(PrintTemplate)
    if tenant_id:
        query = query.filter(
            (PrintTemplate.tenant_id == tenant_id) | (PrintTemplate.tenant_id == None)
        )
    return query.offset(skip).limit(limit).all()


def create_print_template(
    db: Session, template: PrintTemplateCreate, tenant_id: Optional[UUID] = None
) -> PrintTemplate:
    """Create a new print template for tenant"""
    data = sanitize_text_fields(template.model_dump(), ["description"])
    if tenant_id:
        data["tenant_id"] = tenant_id
    db_template = PrintTemplate(**data)
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template


def update_print_template(
    db: Session, template_id: int, template: PrintTemplateUpdate
) -> Optional[PrintTemplate]:
    """Update a print template"""
    db_template = get_print_template(db, template_id)
    if not db_template:
        return None
    update_data = sanitize_text_fields(
        template.model_dump(exclude_unset=True), ["description"]
    )
    for field, value in update_data.items():
        setattr(db_template, field, value)
    db.commit()
    db.refresh(db_template)
    return db_template


def delete_print_template(db: Session, template_id: int) -> bool:
    """Delete a print template"""
    db_template = get_print_template(db, template_id)
    if not db_template:
        return False
    db.delete(db_template)
    db.commit()
    return True


def get_default_templates() -> List[dict]:
    """Retrieve the default templates (global)"""
    return [
        {
            "key": "asset-card",
            "name": "Asset Card",
            "name_translations": {"it": "Scheda Asset", "en": "Asset Card"},
            "description": "Full device sheet",
            "description_translations": {
                "it": "Scheda completa del dispositivo",
                "en": "Full device sheet",
            },
            "icon": "pi pi-server",
            "component": "AssetCardPrint",
            "options": {
                "includePhoto": True,
                "includeQR": True,
                "includeConnections": False,
                "includeRiskMatrix": True,
                "includeCustomFields": True,
            },
        },
        {
            "key": "asset-summary",
            "name": "Asset Summary",
            "name_translations": {"it": "Riepilogo Asset", "en": "Asset Summary"},
            "description": "Compact device sheet",
            "description_translations": {
                "it": "Scheda compatta del dispositivo",
                "en": "Compact device sheet",
            },
            "icon": "pi pi-file",
            "component": "AssetSummaryPrint",
            "options": {
                "includePhoto": False,
                "includeQR": True,
                "includeConnections": False,
                "includeRiskMatrix": False,
                "includeCustomFields": False,
            },
        },
    ]
