# backend/app/crud/sr_assessments.py
"""
CRUD operations for SRAssessment
"""
from typing import List, Optional
from sqlalchemy.orm import Session
import uuid
from app.models.sr_assessment import SRAssessment
from app.schemas.sr_assessment import SRAssessmentCreate, SRAssessmentUpdate


def get_sr_assessment(
    db: Session,
    assessment_id: uuid.UUID,
    tenant_id: uuid.UUID
) -> Optional[SRAssessment]:
    """Get a single SRAssessment by ID"""
    return (
        db.query(SRAssessment)
        .filter(
            SRAssessment.id == assessment_id,
            SRAssessment.tenant_id == tenant_id
        )
        .first()
    )


def get_sr_assessment_by_sr_and_object(
    db: Session,
    sr_id: uuid.UUID,
    object_type: str,
    object_id: uuid.UUID,
    tenant_id: uuid.UUID,
    enhancement_level: Optional[int] = None,
) -> Optional[SRAssessment]:
    """Get SRAssessment by SR, object, and optional RE level (None = legacy SR-level)."""
    query = db.query(SRAssessment).filter(
        SRAssessment.sr_id == sr_id,
        SRAssessment.object_type == object_type,
        SRAssessment.object_id == object_id,
        SRAssessment.tenant_id == tenant_id,
    )
    if enhancement_level is None:
        query = query.filter(SRAssessment.enhancement_level.is_(None))
    else:
        query = query.filter(SRAssessment.enhancement_level == enhancement_level)
    return query.first()


def list_sr_assessments_for_sr_and_object(
    db: Session,
    sr_id: uuid.UUID,
    object_type: str,
    object_id: uuid.UUID,
    tenant_id: uuid.UUID,
) -> List[SRAssessment]:
    return (
        db.query(SRAssessment)
        .filter(
            SRAssessment.sr_id == sr_id,
            SRAssessment.object_type == object_type,
            SRAssessment.object_id == object_id,
            SRAssessment.tenant_id == tenant_id,
        )
        .order_by(SRAssessment.enhancement_level.asc().nullsfirst())
        .all()
    )


def get_sr_assessments(
    db: Session,
    tenant_id: uuid.UUID,
    sr_id: Optional[uuid.UUID] = None,
    object_type: Optional[str] = None,
    object_id: Optional[uuid.UUID] = None,
    skip: int = 0,
    limit: int = 100
) -> List[SRAssessment]:
    """Get SRAssessments with optional filters"""
    query = db.query(SRAssessment).filter(SRAssessment.tenant_id == tenant_id)
    
    if sr_id:
        query = query.filter(SRAssessment.sr_id == sr_id)
    
    if object_type:
        query = query.filter(SRAssessment.object_type == object_type)
    
    if object_id:
        query = query.filter(SRAssessment.object_id == object_id)
    
    return query.offset(skip).limit(limit).all()


def create_sr_assessment(
    db: Session,
    assessment_in: SRAssessmentCreate,
    tenant_id: uuid.UUID
) -> SRAssessment:
    """Create a new SRAssessment"""
    db_assessment = SRAssessment(
        tenant_id=tenant_id,
        **assessment_in.dict()
    )
    db.add(db_assessment)
    db.commit()
    db.refresh(db_assessment)
    return db_assessment


def update_sr_assessment(
    db: Session,
    assessment_id: uuid.UUID,
    assessment_in: SRAssessmentUpdate,
    tenant_id: uuid.UUID
) -> Optional[SRAssessment]:
    """Update an SRAssessment"""
    db_assessment = get_sr_assessment(db, assessment_id, tenant_id)
    if not db_assessment:
        return None
    
    update_data = assessment_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_assessment, field, value)
    
    db.commit()
    db.refresh(db_assessment)
    return db_assessment


def delete_sr_assessment(
    db: Session,
    assessment_id: uuid.UUID,
    tenant_id: uuid.UUID
) -> bool:
    """Delete an SRAssessment (cascade deletes evidence)"""
    db_assessment = get_sr_assessment(db, assessment_id, tenant_id)
    if not db_assessment:
        return False
    
    db.delete(db_assessment)
    db.commit()
    return True

