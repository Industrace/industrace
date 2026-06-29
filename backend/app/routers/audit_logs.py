import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from io import StringIO
import csv
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.models import User, AuditLog
from app.schemas.audit_log import AuditLog as AuditLogSchema
from app.services.auth import get_current_user
from app.services.rbac import require_permission
from app.services.audit_log import get_entity_name_by_id

router = APIRouter(
    prefix="/audit-logs",
    tags=["audit_logs"],
)


@router.get("", response_model=List[AuditLogSchema])
def list_audit_logs(
    from_date: Optional[datetime] = Query(None, alias="from"),
    to_date: Optional[datetime] = Query(None, alias="to"),
    action: Optional[str] = None,
    entity: Optional[str] = None,
    entity_id: Optional[uuid.UUID] = Query(None, alias="entity_id"),
    user_id: Optional[uuid.UUID] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    perm=Depends(require_permission("audit_logs", 1)),
):
    query = db.query(AuditLog).filter(AuditLog.tenant_id == current_user.tenant_id)
    if from_date:
        query = query.filter(AuditLog.timestamp >= from_date)
    if to_date:
        query = query.filter(AuditLog.timestamp <= to_date)
    if action:
        query = query.filter(AuditLog.action == action)
    if entity:
        query = query.filter(AuditLog.entity == entity)
    if entity_id:
        query = query.filter(AuditLog.entity_id == entity_id)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    query = query.order_by(AuditLog.timestamp.desc())
    logs = query.offset(skip).limit(limit).all()

    result = []
    for log in logs:
        # Use centralized function to get entity name
        entity_name = get_entity_name_by_id(
            db, log.entity, log.entity_id, current_user.tenant_id
        )
        result.append(
            AuditLogSchema.model_validate(log).model_dump() | {"entity_name": entity_name}
        )

    return result


@router.get("/export")
def export_audit_logs(
    from_date: Optional[datetime] = Query(None, alias="from"),
    to_date: Optional[datetime] = Query(None, alias="to"),
    action: Optional[str] = None,
    entity: Optional[str] = None,
    entity_id: Optional[uuid.UUID] = Query(None, alias="entity_id"),
    user_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    perm=Depends(require_permission("audit_logs", 1)),
):
    query = db.query(AuditLog).filter(AuditLog.tenant_id == current_user.tenant_id)
    if from_date:
        query = query.filter(AuditLog.timestamp >= from_date)
    if to_date:
        query = query.filter(AuditLog.timestamp <= to_date)
    if action:
        query = query.filter(AuditLog.action == action)
    if entity:
        query = query.filter(AuditLog.entity == entity)
    if entity_id:
        query = query.filter(AuditLog.entity_id == entity_id)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    query = query.order_by(AuditLog.timestamp.desc())
    logs = query.all()

    def iter_csv():
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(
            ["timestamp", "user_id", "action", "entity", "entity_id", "description"]
        )
        for log in logs:
            writer.writerow(
                [
                    log.timestamp.isoformat() if log.timestamp else "",
                    str(log.user_id) if log.user_id else "",
                    log.action,
                    log.entity,
                    str(log.entity_id) if log.entity_id else "",
                    log.description or "",
                ]
            )
        output.seek(0)
        yield output.read()

    return StreamingResponse(
        iter_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_logs.csv"},
    )
