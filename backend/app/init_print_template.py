# init_print_template.py

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.print_template import PrintTemplate
from app.crud.print_templates import get_default_templates


def init_default_templates(tenant_id=None):
    session: Session = SessionLocal()
    try:
        default_templates = get_default_templates()
        for template_data in default_templates:
            query = session.query(PrintTemplate).filter_by(key=template_data["key"])
            if tenant_id:
                query = query.filter_by(tenant_id=tenant_id)
            else:
                query = query.filter(PrintTemplate.tenant_id.is_(None))
            existing = query.first()
            if existing:
                continue
            template = PrintTemplate(
                key=template_data["key"],
                name=template_data["name"],
                name_translations=template_data.get("name_translations", {}),
                description=template_data["description"],
                description_translations=template_data.get(
                    "description_translations", {}
                ),
                icon=template_data["icon"],
                component=template_data["component"],
                options=template_data["options"],
                tenant_id=tenant_id,
            )
            session.add(template)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    init_default_templates()
