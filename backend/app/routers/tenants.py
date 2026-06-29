# routers/tenants.py

from typing import List
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.services.audit_decorator import audit_log_action
from app.models import Tenant
from app.crud import tenants as crud_tenants
from app.services.rbac import require_section_access

router = APIRouter(
    prefix="/tenants",
    tags=["tenants"],
    dependencies=[Depends(require_section_access("roles"))],
)


@router.post("", response_model=schemas.Tenant)
@audit_log_action("create", "Tenant", model_class=Tenant)
def create_tenant(
    tenant: schemas.Tenant, request: Request, db: Session = Depends(get_db)
):
    return crud_tenants.create_tenant(db, tenant)


@router.get("", response_model=List[schemas.Tenant])
@audit_log_action("list", "Tenant", model_class=Tenant)
def list_tenants(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_tenants.get_tenants(db, skip=skip, limit=limit)
