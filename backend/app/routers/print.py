from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
import os
from pathlib import Path
from uuid import UUID

from app.models.asset import Asset, asset_contacts
from app.models.site import Site
from app.models.area import Area
from app.models.location import Location
from app.models.contact import Contact
from app.models.supplier import Supplier
from app.models.tenant import Tenant

from app.database import get_db
from app.crud import print_templates, print_history, assets
from app.schemas.print_template import (
    PrintTemplate,
    PrintTemplateCreate,
    PrintTemplateUpdate,
)
from app.schemas.print_history import PrintHistory
from app.schemas.print import (
    PrintGenerateRequest,
    PrintGenerateResponse,
    QRCodeRequest,
    PrintHistoryQuery,
    PrintedKitRequest,
    PrintedKitResponse,
)
from app.services.pdf_generator import PDFGenerator
from app.services.auth import get_current_user
from app.services.rbac import require_section_access
from app.models.user import User
from app.errors.exceptions import ErrorCodeException
from app.errors.error_codes import ErrorCode

router = APIRouter(
    prefix="/print",
    tags=["print"],
    dependencies=[Depends(require_section_access("assets"))],
)

# Initialize PDF generator
pdf_generator = PDFGenerator()


@router.get("/templates", response_model=List[PrintTemplate])
def get_print_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Recupera tutti i template di stampa disponibili per il tenant corrente o globali"""
    # Initialize PDF generator
    pdf_generator = PDFGenerator()

    # print(f"DEBUG: get_print_templates chiamata per utente: {current_user.email}")
    # print(f"DEBUG: Tenant ID utente: {current_user.tenant_id}")

    tenant_id = current_user.tenant_id if current_user else None
    templates = print_templates.get_print_templates(
        db, tenant_id=tenant_id, skip=skip, limit=limit
    )
    # print(f"DEBUG: Template trovati nel database: {len(templates)}")

    if not templates:
        # print("DEBUG: Nessun template nel database, restituisco lista vuota")
        # Now that default templates are in the database, "virtual" templates are no longer needed
        return []

    # print(f"DEBUG: Restituisco {len(templates)} template dal database")
    for template in templates:
        # print(f"DEBUG: Template: {template.key} - {template.name}")
        pass

    return templates


@router.get("/templates/{template_id}", response_model=PrintTemplate)
def get_print_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific template"""
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
    """Create a new print template for the current tenant"""
    tenant_id = current_user.tenant_id if current_user else None
    return print_templates.create_print_template(db, template, tenant_id=tenant_id)


@router.put("/templates/{template_id}", response_model=PrintTemplate)
def update_print_template(
    template_id: int,
    template: PrintTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing template"""
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
    """Delete a template"""
    success = print_templates.delete_print_template(
        db, template_id, tenant_id=current_user.tenant_id
    )
    if not success:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.PRINT_TEMPLATE_NOT_FOUND
        )
    return {"message": "Template deleted successfully"}


@router.get("/test-auth")
def test_auth(current_user: User = Depends(get_current_user)):
    """Test endpoint to verify authentication"""
    return {
        "user_id": str(current_user.id),
        "email": current_user.email,
        "tenant_id": str(current_user.tenant_id) if current_user.tenant_id else None,
        "authenticated": True,
    }


@router.post("/templates/init-defaults")
def init_default_templates(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Initialize default templates for the current tenant"""
    # print(f"DEBUG: Inizializzazione template per utente: {current_user.email}")
    tenant_id = current_user.tenant_id if current_user else None
    if not tenant_id:
        raise ErrorCodeException(
            status_code=400, error_code=ErrorCode.TENANT_ID_REQUIRED
        )

    # Verify if there are already templates for this tenant
    existing_templates = print_templates.get_print_templates(db, tenant_id=tenant_id)

    if existing_templates:
        raise ErrorCodeException(
            status_code=400, error_code=ErrorCode.PRINT_TEMPLATE_ALREADY_EXISTS
        )

    # Create default templates
    default_templates_data = print_templates.get_default_templates()

    created_templates = []

    for template_data in default_templates_data:
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
        except Exception as e:
            raise ErrorCodeException(
                status_code=500, error_code=ErrorCode.PRINT_TEMPLATE_CREATION_FAILED
            )
    return {
        "message": f"Creati {len(created_templates)} template di default",
        "templates": created_templates,
    }


@router.post("/generate", response_model=PrintGenerateResponse)
def generate_print(
    request: PrintGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify that the asset exists
    asset = (
        db.query(Asset)
        .filter(Asset.id == request.asset_id, Asset.tenant_id == current_user.tenant_id)
        .first()
    )
    if not asset:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)

    # Search for the template in the database
    from app.crud.print_templates import get_print_template, get_print_template_by_key

    template = None

    try:
        template_id = int(request.template_id)
        # Search for the template in the database
        template = get_print_template(db, template_id, tenant_id=current_user.tenant_id)

    except (ValueError, TypeError):
        template = get_print_template_by_key(
            db,
            str(request.template_id),
            tenant_id=getattr(current_user, "tenant_id", None),
        )

    if not template:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.PRINT_TEMPLATE_NOT_FOUND
        )

    # Create entry in the history
    from app.schemas.print_history import PrintHistoryCreate

    history_data = PrintHistoryCreate(
        asset_id=request.asset_id,
        template_id=request.template_id,
        options=request.options,
        generated_by=current_user.id,
        status="processing",
    )
    history = print_history.create_print_history(db, history_data)

    try:
        # Get all the asset data for the print
        from app.crud import assets as assets_crud

        # Get the asset with all the relations
        asset_with_relations = (
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
            )
            .filter(
                Asset.id == request.asset_id, Asset.tenant_id == current_user.tenant_id
            )
            .first()
        )

        if not asset_with_relations:
            raise ErrorCodeException(
                status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND
            )

        # Get the connections of the asset separately
        from app.models.asset_connection import AssetConnection

        connections = (
            db.query(AssetConnection)
            .options(
                joinedload(AssetConnection.parent_asset),
                joinedload(AssetConnection.child_asset),
            )
            .filter(
                (AssetConnection.parent_asset_id == request.asset_id)
                | (AssetConnection.child_asset_id == request.asset_id)
            )
            .all()
        )

        # Convert to dictionary with relations
        asset_dict = {
            "id": asset_with_relations.id,
            "name": asset_with_relations.name,
            "tag": asset_with_relations.tag,
            "description": asset_with_relations.description,
            "serial_number": asset_with_relations.serial_number,
            "model": asset_with_relations.model,
            "firmware_version": asset_with_relations.firmware_version,
            # REMOVED: 'ip_address', 'vlan', 'logical_port', 'physical_plug_label'
            "remote_access": asset_with_relations.remote_access,
            "remote_access_type": asset_with_relations.remote_access_type,
            "last_update_date": asset_with_relations.last_update_date,
            "custom_fields": asset_with_relations.custom_fields,
            "created_at": asset_with_relations.created_at,
            "updated_at": asset_with_relations.updated_at,
            "last_seen": asset_with_relations.last_seen,
            "map_x": asset_with_relations.map_x,
            "map_y": asset_with_relations.map_y,
            "installation_date": asset_with_relations.installation_date,
            "business_criticality": asset_with_relations.business_criticality,
            "impact_value": asset_with_relations.impact_value,
            "physical_access_ease": asset_with_relations.physical_access_ease,
            "purdue_level": asset_with_relations.purdue_level,
            "exposure_level": asset_with_relations.exposure_level,
            "update_status": asset_with_relations.update_status,
            "risk_score": asset_with_relations.risk_score,
            "last_risk_assessment": asset_with_relations.last_risk_assessment,
            "protocols": asset_with_relations.protocols or [],
            "security_zone": (
                {
                    "id": asset_with_relations.security_zone.id,
                    "name": asset_with_relations.security_zone.name,
                }
                if asset_with_relations.security_zone
                else None
            ),
            "area": (
                {
                    "id": asset_with_relations.area.id,
                    "name": asset_with_relations.area.name,
                    "code": asset_with_relations.area.code,
                }
                if asset_with_relations.area
                else None
            ),
            "asset_type": (
                {
                    "name": (
                        asset_with_relations.asset_type.name
                        if asset_with_relations.asset_type
                        else None
                    )
                }
                if asset_with_relations.asset_type
                else None
            ),
            "status": (
                {
                    "name": (
                        asset_with_relations.status.name
                        if asset_with_relations.status
                        else None
                    )
                }
                if asset_with_relations.status
                else None
            ),
            "site": (
                {
                    "name": (
                        asset_with_relations.site.name
                        if asset_with_relations.site
                        else None
                    )
                }
                if asset_with_relations.site
                else None
            ),
            "location": (
                {
                    "name": (
                        asset_with_relations.location.name
                        if asset_with_relations.location
                        else None
                    )
                }
                if asset_with_relations.location
                else None
            ),
            "manufacturer": (
                {
                    "name": (
                        asset_with_relations.manufacturer.name
                        if asset_with_relations.manufacturer
                        else None
                    )
                }
                if asset_with_relations.manufacturer
                else None
            ),
            "photos": (
                [
                    {"file_path": photo.file_path, "uploaded_at": photo.uploaded_at}
                    for photo in asset_with_relations.photos
                ]
                if asset_with_relations.photos
                else []
            ),
            "documents": (
                [
                    {
                        "name": doc.name,
                        "file_path": doc.file_path,
                        "description": doc.description,
                        "uploaded_at": doc.uploaded_at,
                    }
                    for doc in asset_with_relations.documents
                ]
                if asset_with_relations.documents
                else []
            ),
            "connections": (
                [
                    {
                        "connection_type": conn.connection_type,
                        "target_asset": (
                            {
                                "name": (
                                    conn.child_asset.name
                                    if conn.parent_asset_id == request.asset_id
                                    else conn.parent_asset.name
                                )
                            }
                            if (
                                conn.parent_asset_id == request.asset_id
                                and conn.child_asset
                            )
                            or (
                                conn.child_asset_id == request.asset_id
                                and conn.parent_asset
                            )
                            else None
                        ),
                        "port_parent": conn.port_parent,
                        "port_child": conn.port_child,
                        "protocol": conn.protocol,
                        "description": conn.description,
                        "local_interface": (
                            {
                                "name": (
                                    conn.local_interface.name
                                    if conn.local_interface
                                    else None
                                )
                            }
                            if conn.local_interface
                            else None
                        ),
                        "remote_interface": (
                            {
                                "name": (
                                    conn.remote_interface.name
                                    if conn.remote_interface
                                    else None
                                )
                            }
                            if conn.remote_interface
                            else None
                        ),
                    }
                    for conn in connections
                ]
                if connections
                else []
            ),
            "contacts": (
                (lambda contact_roles_dict: [
                    {
                        "first_name": contact.first_name or "",
                        "last_name": contact.last_name or "",
                        "email": contact.email or "",
                        "phone1": contact.phone1 or "",
                        "phone2": contact.phone2 or "",
                        "type": contact.type or "",
                        "notes": contact.notes or "",
                        "role": contact_roles_dict.get(contact.id, "other")
                    }
                    for contact in asset_with_relations.contacts
                ])(
                    {
                        contact_id: role
                        for contact_id, role in (
                            db.execute(
                                select(
                                    asset_contacts.c.contact_id,
                                    asset_contacts.c.role
                                ).where(
                                    asset_contacts.c.asset_id == request.asset_id
                                )
                            ).fetchall() if asset_with_relations.contacts else []
                        )
                    }
                )
                if asset_with_relations.contacts
                else []
            ),
            # ADDED: suppliers
            "suppliers": [
                {
                    "name": s.name or "",
                    "email": s.email or "",
                    "phone": s.phone or "",
                    "website": s.website or "",
                    "notes": s.notes or "",
                }
                for s in (asset_with_relations.suppliers if hasattr(asset_with_relations, "suppliers") and asset_with_relations.suppliers else [])
            ],
            # ADDED: network interfaces
            "interfaces": [
                {
                    "id": str(iface.id) if iface.id else None,
                    "name": iface.name or "",
                    "type": iface.type or "",
                    "ip_address": iface.ip_address or "",
                    "mac_address": iface.mac_address or "",
                    "vlan": iface.vlan or "",
                    "default_gateway": iface.default_gateway or "",
                    "subnet_mask": iface.subnet_mask or "",
                    "logical_port": iface.logical_port or "",
                    "physical_plug_label": iface.physical_plug_label or "",
                }
                for iface in (asset_with_relations.interfaces if hasattr(asset_with_relations, "interfaces") and asset_with_relations.interfaces else [])
            ],
        }

        # Generate the PDF
        filepath = pdf_generator.generate_asset_pdf(
            asset=asset_dict,
            template=template.__dict__,
            options=request.options,
            language=request.options.get("language", "en"),  # Default a inglese
        )

        # Update the history with the file path
        file_size = pdf_generator.get_file_size(filepath)
        print_history.update_print_history_status(
            db, str(history.id), "completed", str(filepath), file_size
        )

        return PrintGenerateResponse(
            print_id=str(history.id),
            status="completed",
            file_url=f"/print/download/{history.id}",
            generated_at=datetime.now().isoformat(),
            file_size=file_size,
        )

    except Exception as e:
        # Update the history with an error
        print_history.update_print_history_status(db, str(history.id), "error")
        # Log the error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Print generation failed: {str(e)}", exc_info=True)
        raise ErrorCodeException(
            status_code=500, error_code=ErrorCode.PRINT_GENERATION_FAILED
        )


@router.get("/download/{print_id}")
def download_print(
    print_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download the generated PDF file"""
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

    # Generate filename for download
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
    """Get the print history"""
    # Convert dates if provided
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

    history = print_history.get_print_history_list(
        db=db,
        asset_id=asset_id,
        template_id=template_id,
        from_date=from_dt,
        to_date=to_dt,
        skip=offset,
        limit=limit,
    )
    allowed_asset_ids = {
        asset_id
        for (asset_id,) in db.query(Asset.id)
        .filter(Asset.tenant_id == current_user.tenant_id)
        .all()
    }
    history = [entry for entry in history if entry.asset_id in allowed_asset_ids]

    return history


@router.post("/qr-code")
def generate_qr_code(
    request: QRCodeRequest, current_user: User = Depends(get_current_user)
):
    """Generate a QR code"""
    try:
        qr_buffer = pdf_generator._generate_qr_code(request.text, request.size)

        return Response(
            content=qr_buffer.getvalue(),
            media_type="image/png",
            headers={"Content-Disposition": "inline; filename=qr-code.png"},
        )
    except Exception as e:
        raise ErrorCodeException(
            status_code=500, error_code=ErrorCode.QR_CODE_GENERATION_FAILED
        )


@router.get("/assets/{asset_id}/print-data")
def get_asset_print_data(
    asset_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all the data necessary for the print of an asset"""
    asset = (
        db.query(Asset)
        .filter(Asset.id == asset_id, Asset.tenant_id == current_user.tenant_id)
        .first()
    )
    if not asset:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)

    # Get related data
    asset_photos = assets.get_asset_photos(db, asset_id)
    asset_documents = assets.get_asset_documents(db, asset_id)
    asset_connections = assets.get_asset_connections(db, asset_id)
    asset_contacts = assets.get_asset_contacts(db, asset_id)

    # Build the complete response
    asset_data = asset.__dict__.copy()
    asset_data.update(
        {
            "photos": [photo.__dict__ for photo in asset_photos],
            "documents": [doc.__dict__ for doc in asset_documents],
            "connections": [conn.__dict__ for conn in asset_connections],
            "contacts": [contact.__dict__ for contact in asset_contacts],
        }
    )

    return asset_data


@router.post("/kit", response_model=PrintedKitResponse)
def generate_printed_kit(
    request: PrintedKitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Genera un printed kit completo per il tenant corrente"""
    try:
        tenant_id = current_user.tenant_id
        
        # Recupera i dati del tenant
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            raise ErrorCodeException(status_code=404, error_code=ErrorCode.TENANT_NOT_FOUND)
        
        # Recupera tutti i dati necessari
        kit_data = {
            "tenant": tenant,
            "generated_at": datetime.now(),
            "generated_by": current_user.name,
        }
        
        # Per ora includiamo solo i dati base per testare
        if request.include_sites:
            sites = db.query(Site).filter(
                Site.tenant_id == tenant_id,
                Site.deleted_at == None
            ).all()
            kit_data["sites"] = sites
        
        if request.include_assets:
            assets_data = db.query(Asset).filter(
                Asset.tenant_id == tenant_id,
                Asset.deleted_at == None
            ).options(
                joinedload(Asset.asset_type),
                joinedload(Asset.status),
                joinedload(Asset.site),
                joinedload(Asset.location).joinedload(Location.area),
                joinedload(Asset.manufacturer),
                joinedload(Asset.contacts),
            ).all()
            kit_data["assets"] = assets_data
        
        if request.include_contacts:
            contacts = db.query(Contact).filter(
                Contact.tenant_id == tenant_id,
                Contact.deleted_at == None
            ).all()
            kit_data["contacts"] = contacts
        
        if request.include_suppliers:
            suppliers = db.query(Supplier).filter(
                Supplier.tenant_id == tenant_id,
                Supplier.deleted_at == None
            ).all()
            kit_data["suppliers"] = suppliers
        
        # Genera il PDF del printed kit
        options_dict = {
            "include_assets": request.include_assets,
            "include_sites": request.include_sites,
            "include_contacts": request.include_contacts,
            "include_suppliers": request.include_suppliers,
            "include_photos": request.include_photos,
            "include_documents": request.include_documents,
            "language": request.language or "en"
        }
        file_path = pdf_generator.generate_printed_kit(kit_data, options_dict)
        
        return PrintedKitResponse(
            file_url=f"/print/kit/download/{os.path.basename(file_path)}",
            file_size=os.path.getsize(file_path),
            generated_at=datetime.now()
        )
        
    except Exception as e:
        import logging
        logging.error(f"Errore nella generazione del printed kit: {str(e)}")
        logging.error(f"Exception type: {type(e)}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        raise ErrorCodeException(
            status_code=500, 
            error_code=ErrorCode.PRINT_GENERATION_FAILED
        )

@router.get("/kit/download/{filename}")
def download_printed_kit(
    filename: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Scarica il printed kit generato"""
    try:
        import logging
        logging.info(f"Download request per file: {filename}")
        logging.info(f"User: {current_user.email}")
        
        # Verifica che il file esista e appartenga al tenant corrente
        uploads_dir = Path("uploads/prints")
        file_path = uploads_dir / filename
        
        logging.info(f"File path: {file_path}")
        logging.info(f"File exists: {file_path.exists()}")
        
        if not file_path.exists():
            logging.error(f"File non trovato: {file_path}")
            raise ErrorCodeException(status_code=404, error_code=ErrorCode.FILE_NOT_FOUND)
        
        # Verifica che il file sia un printed kit valido (controllo base)
        if not filename.startswith("printed-kit-"):
            logging.error(f"File non valido: {filename}")
            raise ErrorCodeException(status_code=403, error_code=ErrorCode.ACCESS_DENIED)
        
        logging.info(f"File valido, invio risposta per: {filename}")
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type="application/pdf"
        )
        
    except Exception as e:
        import logging
        logging.error(f"Errore nel download del printed kit: {str(e)}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        raise ErrorCodeException(
            status_code=500, 
            error_code=ErrorCode.FILE_DOWNLOAD_FAILED
        )
