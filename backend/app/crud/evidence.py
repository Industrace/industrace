# backend/app/crud/evidence.py
from typing import List, Optional
from sqlalchemy.orm import Session
from uuid import UUID
from app.models.evidence import Evidence


def create_evidence(db: Session, evidence_data: dict, tenant_id: UUID, created_by: Optional[UUID] = None) -> Evidence:
    """Crea una nuova Evidence"""
    evidence = Evidence(
        **evidence_data,
        tenant_id=tenant_id,
        created_by=created_by
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return evidence


def get_evidence(db: Session, evidence_id: UUID, tenant_id: UUID) -> Optional[Evidence]:
    """Recupera una Evidence per ID"""
    return db.query(Evidence).filter(
        Evidence.id == evidence_id,
        Evidence.tenant_id == tenant_id
    ).first()


def get_evidences_by_filter(
    db: Session,
    tenant_id: UUID,
    asset_id: Optional[UUID] = None,
    zone_id: Optional[UUID] = None,
    conduit_id: Optional[UUID] = None,
    capability_id: Optional[UUID] = None,
    sr_assessment_id: Optional[UUID] = None,
    source: Optional[str] = None
) -> List[Evidence]:
    """Recupera Evidence con filtri opzionali"""
    query = db.query(Evidence).filter(Evidence.tenant_id == tenant_id)
    
    if asset_id:
        query = query.filter(Evidence.asset_id == asset_id)
    if zone_id:
        query = query.filter(Evidence.zone_id == zone_id)
    if conduit_id:
        query = query.filter(Evidence.conduit_id == conduit_id)
    if capability_id:
        query = query.filter(Evidence.capability_id == capability_id)
    if sr_assessment_id:
        query = query.filter(Evidence.sr_assessment_id == sr_assessment_id)
    if source:
        query = query.filter(Evidence.source == source)
    
    return query.order_by(Evidence.created_at.desc()).all()


def update_evidence(db: Session, evidence_id: UUID, tenant_id: UUID, update_data: dict) -> Optional[Evidence]:
    """Aggiorna una Evidence"""
    evidence = get_evidence(db, evidence_id, tenant_id)
    if not evidence:
        return None
    
    for key, value in update_data.items():
        if value is not None or key in ['raw_data']:  # Allow setting raw_data to None
            setattr(evidence, key, value)
    
    db.commit()
    db.refresh(evidence)
    return evidence


def delete_evidence(db: Session, evidence_id: UUID, tenant_id: UUID) -> bool:
    """Elimina una Evidence"""
    evidence = get_evidence(db, evidence_id, tenant_id)
    if not evidence:
        return False
    
    db.delete(evidence)
    db.commit()
    return True

