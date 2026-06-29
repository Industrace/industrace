# backend/app/routers/evidence.py
"""
API endpoints for managing Evidence
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.models import User
from app.services.auth import get_current_user
from app.services.feature_guard import require_iec62443_enabled
from app.services.rbac import require_section_access
from app.schemas.evidence import EvidenceCreate, EvidenceUpdate, EvidenceResponse
from app.crud import evidence as crud_evidence
from app.errors.exceptions import ErrorCodeException
from app.errors.error_codes import ErrorCode
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/evidence",
    tags=["evidence"],
    dependencies=[
        Depends(require_iec62443_enabled),
        Depends(require_section_access("evidence")),
    ],
)


@router.get("", response_model=List[EvidenceResponse])
def list_evidences(
    asset_id: Optional[UUID] = None,
    zone_id: Optional[UUID] = None,
    conduit_id: Optional[UUID] = None,
    capability_id: Optional[UUID] = None,
    sr_assessment_id: Optional[UUID] = None,
    source: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lista Evidence con filtri opzionali"""
    evidences = crud_evidence.get_evidences_by_filter(
        db,
        tenant_id=current_user.tenant_id,
        asset_id=asset_id,
        zone_id=zone_id,
        conduit_id=conduit_id,
        capability_id=capability_id,
        sr_assessment_id=sr_assessment_id,
        source=source
    )
    
    # Arricchisci con nomi
    result = []
    for ev in evidences:
        ev_dict = {
            **ev.__dict__,
            "creator_name": ev.creator.name if ev.creator else None,
            "asset_name": ev.asset.name if ev.asset else None,
            "zone_name": ev.zone.name if ev.zone else None,
            "capability_name": ev.capability.name if ev.capability else None,
        }
        result.append(EvidenceResponse(**ev_dict))
    
    return result


@router.post("", response_model=EvidenceResponse, status_code=201)
def create_evidence(
    evidence_data: EvidenceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Crea una nuova Evidence"""
    evidence = crud_evidence.create_evidence(
        db,
        evidence_data.model_dump(exclude_unset=True),
        tenant_id=current_user.tenant_id,
        created_by=current_user.id
    )
    
    return EvidenceResponse(
        **evidence.__dict__,
        creator_name=current_user.name,
        asset_name=evidence.asset.name if evidence.asset else None,
        zone_name=evidence.zone.name if evidence.zone else None,
        capability_name=evidence.capability.name if evidence.capability else None,
    )


@router.get("/{evidence_id}", response_model=EvidenceResponse)
def get_evidence(
    evidence_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Recupera una Evidence per ID"""
    evidence = crud_evidence.get_evidence(db, evidence_id, current_user.tenant_id)
    if not evidence:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.EVIDENCE_NOT_FOUND)
    
    return EvidenceResponse(
        **evidence.__dict__,
        creator_name=evidence.creator.full_name if evidence.creator else None,
        asset_name=evidence.asset.name if evidence.asset else None,
        zone_name=evidence.zone.name if evidence.zone else None,
        capability_name=evidence.capability.name if evidence.capability else None,
    )


@router.put("/{evidence_id}", response_model=EvidenceResponse)
def update_evidence(
    evidence_id: UUID,
    evidence_data: EvidenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Aggiorna una Evidence"""
    evidence = crud_evidence.update_evidence(
        db,
        evidence_id,
        current_user.tenant_id,
        evidence_data.model_dump(exclude_unset=True)
    )
    if not evidence:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.EVIDENCE_NOT_FOUND)
    
    return EvidenceResponse(
        **evidence.__dict__,
        creator_name=evidence.creator.full_name if evidence.creator else None,
        asset_name=evidence.asset.name if evidence.asset else None,
        zone_name=evidence.zone.name if evidence.zone else None,
        capability_name=evidence.capability.name if evidence.capability else None,
    )


@router.delete("/{evidence_id}", status_code=204)
def delete_evidence(
    evidence_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Elimina una Evidence"""
    if not crud_evidence.delete_evidence(db, evidence_id, current_user.tenant_id):
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.EVIDENCE_NOT_FOUND)

