import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload

from app.models.asset import Asset
from app.models.site import Site
from app.models.location import Location
from app.models.contact import Contact
from app.models.supplier import Supplier
from app.models.tenant import Tenant
from app.models.asset_connection import AssetConnection
from app.database import get_db
from app.crud import print_templates, print_history
from app.schemas.print_template import (
    PrintTemplate,
    PrintTemplateCreate,
    PrintTemplateUpdate,
)
from app.schemas.print_history import PrintHistory, PrintHistoryCreate
from app.schemas.print import (
    PrintGenerateRequest,
    PrintGenerateResponse,
    QRCodeRequest,
    PrintedKitRequest,
    PrintedKitResponse,
    normalize_print_language,
)
from app.services.pdf_generator import PDFGenerator
from app.services.print_data import asset_to_print_dict, merge_print_options
from app.services.auth import get_current_user
from app.services.rbac import require_section_access
from app.models.user import User
from app.errors.exceptions import ErrorCodeException
from app.errors.error_codes import ErrorCode

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/print",
    tags=["print"],
    dependencies=[Depends(require_section_access("assets"))],
)

pdf_generator = PDFGenerator()


def _resolve_template(db: Session, template_id: str, tenant_id: UUID):
    template = None
    raw = (template_id or "").strip()
    if raw.isdigit():
        template = print_templates.get_print_template(
            db, int(raw), tenant_id=tenant_id
        )
    if template is None:
        template = print_templates.get_print_template_by_key(
            db, raw, tenant_id=tenant_id
        )
    return template


@router.get("/templates", response_model=List[PrintTemplate])
def get_print_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return print templates for the current tenant (tenant rows override globals)."""
    return print_templates.get_print_templates(
        db, tenant_id=current_user.tenant_id, skip=skip, limit=limit
    )


@router.get("/templates/{template_id}", response_model=PrintTemplate)
def get_print_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    template = print_templates.get_print_template(
        db, template_id, tenant_id=current_user.tenant_id
    )
    if not template:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.PRINT_TEMPLATE_NOT_FOUND
        )
    return template


@router.post("/templates", response_model=PrintTemplate)
def create_print_template(
    template: PrintTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return print_templates.create_print_template(
        db, template, tenant_id=current_user.tenant_id
    )


@router.put("/templates/{template_id}", response_model=PrintTemplate)
def update_print_template(
    template_id: int,
    template: PrintTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    updated_template = print_templates.update_print_template(
        db, template_id, template, tenant_id=current_user.tenant_id
    )
    if not updated_template:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.PRINT_TEMPLATE_NOT_FOUND
        )
    return updated_template


@router.delete("/templates/{template_id}")
def delete_print_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    success = print_templates.delete_print_template(
        db, template_id, tenant_id=current_user.tenant_id
    )
    if not success:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.PRINT_TEMPLATE_NOT_FOUND
        )
    return {"message": "Template deleted successfully"}


@router.post("/templates/init-defaults")
def init_default_templates(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    tenant_id = current_user.tenant_id
    if not tenant_id:
        raise ErrorCodeException(
            status_code=400, error_code=ErrorCode.TENANT_ID_REQUIRED
        )

    existing_templates = print_templates.get_print_templates(
        db, tenant_id=tenant_id, tenant_only=True
    )
    if existing_templates:
        raise ErrorCodeException(
            status_code=400, error_code=ErrorCode.PRINT_TEMPLATE_ALREADY_EXISTS
        )

    created_templates = []
    for template_data in print_templates.get_default_templates():
        template_create = PrintTemplateCreate(
            key=template_data["key"],
            name=template_data["name"],
            name_translations=template_data.get("name_translations", {}),
            description=template_data["description"],
            description_translations=template_data.get("description_translations", {}),
            icon=template_data["icon"],
            component=template_data["component"],
            options=template_data["options"],
        )
        try:
            created_template = print_templates.create_print_template(
                db, template_create, tenant_id=tenant_id
            )
            created_templates.append(created_template)
        except Exception:
            logger.exception("Failed to create default print template")
            raise ErrorCodeException(
                status_code=500, error_code=ErrorCode.PRINT_TEMPLATE_CREATION_FAILED
            )
    return {
        "message": f"Created {len(created_templates)} default templates",
        "templates": created_templates,
    }


@router.post("/generate", response_model=PrintGenerateResponse)
def generate_print(
    request: PrintGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    asset = (
        db.query(Asset)
        .options(
            joinedload(Asset.asset_type),
            joinedload(Asset.status),
            joinedload(Asset.site),
            joinedload(Asset.location),
            joinedload(Asset.manufacturer),
            joinedload(Asset.photos),
            joinedload(Asset.documents),
            joinedload(Asset.contacts),
            joinedload(Asset.suppliers),
            joinedload(Asset.security_zone),
            joinedload(Asset.area),
            joinedload(Asset.interfaces),
        )
        .filter(
            Asset.id == request.asset_id,
            Asset.tenant_id == current_user.tenant_id,
            Asset.deleted_at.is_(None),
        )
        .first()
    )
    if not asset:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)

    template = _resolve_template(db, request.template_id, current_user.tenant_id)
    if not template:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.PRINT_TEMPLATE_NOT_FOUND
        )

    options = merge_print_options(template.options, request.options)
    language = normalize_print_language(
        options.get("language") or options.get("lang")
    )
    options["language"] = language

    history_data = PrintHistoryCreate(
        asset_id=request.asset_id,
        template_id=template.id,
        options=options,
        generated_by=current_user.id,
        status="processing",
    )
    history = print_history.create_print_history(db, history_data)

    try:
        connections = (
            db.query(AssetConnection)
            .options(
                joinedload(AssetConnection.parent_asset),
                joinedload(AssetConnection.child_asset),
                joinedload(AssetConnection.local_interface),
                joinedload(AssetConnection.remote_interface),
            )
            .filter(
                (AssetConnection.parent_asset_id == request.asset_id)
                | (AssetConnection.child_asset_id == request.asset_id)
            )
            .all()
        )
        asset_dict = asset_to_print_dict(
            db, asset, request.asset_id, connections=connections
        )
        filepath = pdf_generator.generate_asset_pdf(
            asset=asset_dict,
            template={"key": template.key, "options": template.options or {}},
            options=options,
            language=language,
        )
        file_size = pdf_generator.get_file_size(filepath)
        print_history.update_print_history_status(
            db, str(history.id), "completed", str(filepath), file_size
        )
        return PrintGenerateResponse(
            print_id=history.id,
            status="completed",
            file_url=f"/print/download/{history.id}",
            generated_at=datetime.now(timezone.utc),
            file_size=file_size,
        )
    except ErrorCodeException:
        print_history.update_print_history_status(db, str(history.id), "error")
        raise
    except Exception:
        print_history.update_print_history_status(db, str(history.id), "error")
        logger.exception("Print generation failed")
        raise ErrorCodeException(
            status_code=500, error_code=ErrorCode.PRINT_GENERATION_FAILED
        )


@router.get("/download/{print_id}")
def download_print(
    print_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    history = print_history.get_print_history(db, print_id)
    if not history:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.PRINT_NOT_FOUND)
    asset = (
        db.query(Asset)
        .filter(Asset.id == history.asset_id, Asset.tenant_id == current_user.tenant_id)
        .first()
    )
    if not asset:
        raise ErrorCodeException(status_code=403, error_code=ErrorCode.ACCESS_DENIED)

    if not history.file_path or not os.path.exists(history.file_path):
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.PRINT_FILE_NOT_FOUND
        )

    filename = f"asset_{history.asset_id}_{print_id[:8]}.pdf"
    return FileResponse(
        path=history.file_path, filename=filename, media_type="application/pdf"
    )


@router.get("/history", response_model=List[PrintHistory])
def get_print_history(
    asset_id: Optional[UUID] = Query(None),
    template_id: Optional[int] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from_dt = None
    to_dt = None
    if from_date:
        try:
            from_dt = datetime.fromisoformat(from_date.replace("Z", "+00:00"))
        except ValueError:
            raise ErrorCodeException(
                status_code=400, error_code=ErrorCode.INVALID_DATE_FORMAT
            )
    if to_date:
        try:
            to_dt = datetime.fromisoformat(to_date.replace("Z", "+00:00"))
        except ValueError:
            raise ErrorCodeException(
                status_code=400, error_code=ErrorCode.INVALID_DATE_FORMAT
            )

    return print_history.get_print_history_list(
        db=db,
        tenant_id=current_user.tenant_id,
        asset_id=asset_id,
        template_id=template_id,
        from_date=from_dt,
        to_date=to_dt,
        skip=offset,
        limit=limit,
    )


@router.post("/qr-code")
def generate_qr_code(
    request: QRCodeRequest, current_user: User = Depends(get_current_user)
):
    try:
        qr_buffer = pdf_generator.generate_qr_code(request.text, request.size)
        return Response(
            content=qr_buffer.getvalue(),
            media_type="image/png",
            headers={"Content-Disposition": "inline; filename=qr-code.png"},
        )
    except Exception:
        logger.exception("QR code generation failed")
        raise ErrorCodeException(
            status_code=500, error_code=ErrorCode.QR_CODE_GENERATION_FAILED
        )


@router.post("/kit", response_model=PrintedKitResponse)
def generate_printed_kit(
    request: PrintedKitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        tenant_id = current_user.tenant_id
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            raise ErrorCodeException(
                status_code=404, error_code=ErrorCode.TENANT_NOT_FOUND
            )

        kit_data = {
            "tenant": tenant,
            "generated_at": datetime.now(timezone.utc),
            "generated_by": current_user.name,
        }

        if request.include_sites:
            kit_data["sites"] = (
                db.query(Site)
                .filter(Site.tenant_id == tenant_id, Site.deleted_at.is_(None))
                .all()
            )

        if request.include_assets:
            kit_data["assets"] = (
                db.query(Asset)
                .filter(Asset.tenant_id == tenant_id, Asset.deleted_at.is_(None))
                .options(
                    joinedload(Asset.asset_type),
                    joinedload(Asset.status),
                    joinedload(Asset.site),
                    joinedload(Asset.location).joinedload(Location.area),
                    joinedload(Asset.manufacturer),
                    joinedload(Asset.contacts),
                    joinedload(Asset.interfaces),
                )
                .all()
            )

        if request.include_contacts:
            kit_data["contacts"] = (
                db.query(Contact)
                .filter(Contact.tenant_id == tenant_id, Contact.deleted_at.is_(None))
                .all()
            )

        if request.include_suppliers:
            kit_data["suppliers"] = (
                db.query(Supplier)
                .filter(
                    Supplier.tenant_id == tenant_id, Supplier.deleted_at.is_(None)
                )
                .all()
            )

        options_dict = {
            "include_assets": request.include_assets,
            "include_sites": request.include_sites,
            "include_contacts": request.include_contacts,
            "include_suppliers": request.include_suppliers,
            "language": request.language or "en",
        }
        file_path = pdf_generator.generate_printed_kit(kit_data, options_dict)
        return PrintedKitResponse(
            file_url=f"/print/kit/download/{os.path.basename(file_path)}",
            file_size=os.path.getsize(file_path),
            generated_at=datetime.now(timezone.utc),
        )
    except ErrorCodeException:
        raise
    except Exception:
        logger.exception("Printed kit generation failed")
        raise ErrorCodeException(
            status_code=500, error_code=ErrorCode.PRINT_GENERATION_FAILED
        )


@router.get("/kit/download/{filename}")
def download_printed_kit(
    filename: str,
    current_user: User = Depends(get_current_user),
):
    safe_name = Path(filename).name
    if (
        safe_name != filename
        or not filename.startswith("printed-kit-")
        or not filename.lower().endswith(".pdf")
    ):
        raise ErrorCodeException(status_code=403, error_code=ErrorCode.ACCESS_DENIED)

    tenant_dir = (
        Path(pdf_generator.upload_dir) / str(current_user.tenant_id)
    ).resolve()
    file_path = (tenant_dir / safe_name).resolve()
    try:
        file_path.relative_to(tenant_dir)
    except ValueError:
        raise ErrorCodeException(status_code=403, error_code=ErrorCode.ACCESS_DENIED)

    if not file_path.is_file():
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.FILE_NOT_FOUND)

    return FileResponse(
        path=str(file_path),
        filename=safe_name,
        media_type="application/pdf",
    )
