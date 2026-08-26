from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.models.print_template import PrintTemplate
from app.schemas.print_template import PrintTemplateCreate, PrintTemplateUpdate
from app.utils import sanitize_text_fields


def get_print_template(
    db: Session, template_id: int, tenant_id: Optional[UUID] = None
) -> Optional[PrintTemplate]:
    """Retrieve a print template by ID (tenant-owned or global)."""
    query = db.query(PrintTemplate).filter(PrintTemplate.id == template_id)
    if tenant_id:
        query = query.filter(
            (PrintTemplate.tenant_id == tenant_id) | (PrintTemplate.tenant_id.is_(None))
        )
    return query.first()


def get_print_template_by_key(
    db: Session, key: str, tenant_id: Optional[UUID] = None
) -> Optional[PrintTemplate]:
    """Retrieve a print template by key. Tenant-specific rows win over globals."""
    query = db.query(PrintTemplate).filter(PrintTemplate.key == key)
    if tenant_id:
        tenant_match = query.filter(PrintTemplate.tenant_id == tenant_id).first()
        if tenant_match:
            return tenant_match
        return query.filter(PrintTemplate.tenant_id.is_(None)).first()
    return query.first()


def get_print_templates(
    db: Session,
    tenant_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 100,
    tenant_only: bool = False,
) -> List[PrintTemplate]:
    """List print templates. Tenant rows override globals with the same key."""
    query = db.query(PrintTemplate)
    if tenant_id and tenant_only:
        return (
            query.filter(PrintTemplate.tenant_id == tenant_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    if not tenant_id:
        return query.offset(skip).limit(limit).all()

    global_rows = query.filter(PrintTemplate.tenant_id.is_(None)).all()
    tenant_rows = query.filter(PrintTemplate.tenant_id == tenant_id).all()
    by_key = {row.key: row for row in global_rows}
    by_key.update({row.key: row for row in tenant_rows})
    merged = list(by_key.values())
    return merged[skip : skip + limit]


def _owned_by_tenant(
    db_template: PrintTemplate, tenant_id: Optional[UUID]
) -> bool:
    if not db_template or db_template.tenant_id is None:
        return False
    if tenant_id and db_template.tenant_id != tenant_id:
        return False
    return True


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
    db: Session,
    template_id: int,
    template: PrintTemplateUpdate,
    tenant_id: Optional[UUID] = None,
) -> Optional[PrintTemplate]:
    """Update a tenant-owned print template. Global templates are immutable."""
    db_template = get_print_template(db, template_id, tenant_id=tenant_id)
    if not _owned_by_tenant(db_template, tenant_id):
        return None
    update_data = sanitize_text_fields(
        template.model_dump(exclude_unset=True), ["description"]
    )
    for field, value in update_data.items():
        setattr(db_template, field, value)
    db.commit()
    db.refresh(db_template)
    return db_template


def delete_print_template(
    db: Session, template_id: int, tenant_id: Optional[UUID] = None
) -> bool:
    """Delete a tenant-owned print template. Global templates cannot be deleted."""
    db_template = get_print_template(db, template_id, tenant_id=tenant_id)
    if not _owned_by_tenant(db_template, tenant_id):
        return False
    db.delete(db_template)
    db.commit()
    return True


def get_default_templates() -> List[dict]:
    """Default templates seeded per tenant."""
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
            "component": "reportlab-asset-card",
            "options": {
                "includePhoto": True,
                "includeQR": True,
                "includeConnections": True,
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
            "component": "reportlab-asset-summary",
            "options": {
                "includePhoto": False,
                "includeQR": True,
                "includeConnections": False,
                "includeRiskMatrix": False,
                "includeCustomFields": False,
            },
        },
    ]
