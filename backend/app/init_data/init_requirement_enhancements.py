# backend/app/init_data/init_requirement_enhancements.py
"""
Seed Requirement Enhancements (RE 1-4) for each Security Requirement.
Full RE text should be refined against IEC 62443-3-3 tables; placeholders enable SL-RE structure.
"""
import uuid
from sqlalchemy.orm import Session
from app.models import SecurityRequirement, RequirementEnhancement
from app.init_data.iec62443_re_texts import RE_TEXTS


def init_requirement_enhancements(db: Session) -> int:
    requirements = db.query(SecurityRequirement).filter(
        SecurityRequirement.requirement_category == "SR"
    ).all()
    created = 0
    for sr in requirements:
        for level in range(1, 5):
            existing = (
                db.query(RequirementEnhancement)
                .filter(
                    RequirementEnhancement.security_requirement_id == sr.id,
                    RequirementEnhancement.enhancement_level == level,
                )
                .first()
            )
            re_texts = RE_TEXTS.get(sr.requirement_id, {})
            title = f"{sr.requirement_id} — RE {level}"
            description = re_texts.get(level) or (
                f"Requirement Enhancement {level} for {sr.requirement_id} "
                f"({sr.title}). Refer to IEC 62443-3-3:2013 for the normative RE text."
            )
            if not existing:
                db.add(
                    RequirementEnhancement(
                        id=uuid.uuid4(),
                        security_requirement_id=sr.id,
                        enhancement_level=level,
                        title=title,
                        description=description,
                        standard_version=sr.standard_version or "62443-3-3:2013",
                    )
                )
                created += 1
            else:
                existing.title = title
                existing.description = description
                existing.standard_version = sr.standard_version or "62443-3-3:2013"
    db.commit()
    return created
