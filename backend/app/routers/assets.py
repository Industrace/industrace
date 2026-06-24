import uuid
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Request, UploadFile, File, Form, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
import pandas as pd
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models import User, Asset, AssetCommunication, AssetZoneMembership
from app.services.audit_decorator import audit_log_action
from app.schemas import (
    AssetRead as AssetSchema,
    AssetCreate,
    AssetUpdate,
    AssetCustomFieldUpdate,
    AssetRead,
    PositionUpdate,
)
from app.services.auth import get_current_user
from app.services.feature_guard import require_iec62443_enabled
from app.services.audit_log import create_audit_log, resolve_audit_language
from app.crud import assets as crud_assets
from app.errors.exceptions import ErrorCodeException
from app.errors.error_codes import ErrorCode
from app.schemas.asset_status import AssetStatus as AssetStatusSchema
from app.schemas.contact import Contact as ContactSchema
from app.schemas.asset import AssetContact, AssetContactCreate
from app.schemas.asset import AssetBulkUpdateRequest, AssetBulkSoftDeleteRequest
from app.schemas.asset import RiskScoreRequest, RiskScoreResponse, RiskOverviewResponse
from app.services.risk_scoring import CompositeRiskScoringEngine
import io
import json
import math
from app.models.asset_interface import AssetInterface
from app.models.print_history import PrintHistory
from app.models.supplier import Supplier
from app.schemas.supplier import Supplier as SupplierSchema

router = APIRouter(
    prefix="/assets",
    tags=["assets"],
)


# Create asset
@router.post("", response_model=AssetSchema)
@audit_log_action("create", "Asset", model_class=Asset)
def create_asset(
    asset_in: AssetCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Inserisco tenant_id nel body
    data = asset_in.dict()
    data["tenant_id"] = current_user.tenant_id
    result = crud_assets.create_asset(db, AssetCreate(**data), current_user.tenant_id)
    
    # Invalida cache dashboard dopo creazione asset
    from app.services.dashboard_cache import invalidate_dashboard_cache
    invalidate_dashboard_cache(str(current_user.tenant_id))
    
    # Auto-match vulnerabilities in background
    from app.services.vulnerability_auto_match import VulnerabilityAutoMatcher
    if VulnerabilityAutoMatcher.should_auto_match_asset(result):
        VulnerabilityAutoMatcher.match_asset_async(result.id, current_user.tenant_id)
    
    return result


# Schema per la risposta paginata
class PaginatedAssetsResponse(BaseModel):
    data: List[AssetSchema]
    total: int
    skip: int
    limit: int

# List assets (with optional filters)
@router.get("", response_model=PaginatedAssetsResponse)
def list_assets(
    skip: int = 0,
    limit: int = 100,
    status_id: Optional[uuid.UUID] = None,
    site_id: Optional[uuid.UUID] = None,
    area_id: Optional[uuid.UUID] = None,
    location_id: Optional[uuid.UUID] = None,
    global_search: Optional[str] = None,
    business_criticality: Optional[str] = None,
    risk_score_min: Optional[float] = None,
    risk_score_max: Optional[float] = None,
    has_critical_vulns: Optional[bool] = Query(None, description="Filter assets with critical/high vulnerabilities"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from sqlalchemy.orm import selectinload
    from app.models.area import Area
    from sqlalchemy import func, or_
    
    # PERFORMANCE: Usa un limite ragionevole per la paginazione
    # Massimo 500 record per richiesta invece di caricare tutti gli asset
    limit = min(limit, 500)
    
    # PERFORMANCE: Usa selectinload invece di joinedload per ridurre le query duplicate
    # selectinload esegue query separate ottimizzate invece di JOIN pesanti
    query = (
        db.query(Asset)
        .options(
            selectinload(Asset.interfaces),  # Carica interfacce in una query separata
            selectinload(Asset.site),
            selectinload(Asset.location),
            selectinload(Asset.status),
            selectinload(Asset.manufacturer),
            selectinload(Asset.asset_type),
            selectinload(Asset.area),  # PERFORMANCE: Carica area qui per evitare N+1
        )
        .filter(Asset.tenant_id == current_user.tenant_id, Asset.deleted_at == None)
    )

    # Filtri specifici con indici database
    if status_id:
        query = query.filter(Asset.status_id == status_id)
    if site_id:
        query = query.filter(Asset.site_id == site_id)
    if area_id:
        query = query.filter(Asset.area_id == area_id)
    if location_id:
        query = query.filter(Asset.location_id == location_id)
    if business_criticality:
        # Supporta valori multipli separati da virgola (es: "critical,high")
        criticality_values = [v.strip().lower() for v in business_criticality.split(',') if v.strip()]
        if criticality_values:
            query = query.filter(Asset.business_criticality.in_(criticality_values))
    if risk_score_min is not None:
        query = query.filter(Asset.risk_score >= risk_score_min)
    if risk_score_max is not None:
        query = query.filter(Asset.risk_score <= risk_score_max)
    
    if has_critical_vulns:
        from app.models.vulnerability import AssetVulnerability, Vulnerability
        from sqlalchemy import and_
        # Subquery to find assets with critical/high unpatched vulnerabilities
        assets_with_vulns_subquery = (
            db.query(AssetVulnerability.asset_id)
            .join(Vulnerability, AssetVulnerability.vulnerability_id == Vulnerability.id)
            .filter(
                and_(
                    AssetVulnerability.tenant_id == current_user.tenant_id,
                    AssetVulnerability.status.in_(["unreviewed", "acknowledged"]),
                    Vulnerability.severity.in_(["critical", "high"])
                )
            )
            .distinct()
            .subquery()
        )
        query = query.filter(Asset.id.in_(db.query(assets_with_vulns_subquery.c.asset_id)))

    # Ricerca globale ottimizzata
    if global_search:
        search_term = f"%{global_search}%"
        query = query.filter(
            or_(
                Asset.name.ilike(search_term),
                Asset.tag.ilike(search_term),
                Asset.serial_number.ilike(search_term)
            )
        )

    # PERFORMANCE: Usa count ottimizzato con func.count()
    # Esegue COUNT(*) invece di caricare tutti i record
    total_count = query.with_entities(func.count(Asset.id)).scalar()
    
    # PERFORMANCE: Applica paginazione prima di caricare i dati
    assets = query.offset(skip).limit(limit).all()
    
    if assets:
        # PERFORMANCE: Processo batch invece di query N+1
        # Calcola il rischio totale (base + dipendenze) per tutti gli asset in batch
        from app.services.risk_propagation import RiskPropagationService
        
        # Calcola i rischi da dipendenze in batch per ottimizzare le performance
        asset_ids = [asset.id for asset in assets]
        risk_adjustments = RiskPropagationService.get_dependency_risk_adjustments_batch(
            db, asset_ids, current_user.tenant_id
        )
        
        result = []
        for asset in assets:
            asset_dict = AssetRead.from_orm(asset).dict()
            # Area is already loaded via selectinload, no additional query needed
            if asset.area:
                asset_dict["area_name"] = asset.area.name
                asset_dict["area_code"] = asset.area.code
            
            # Assicurati che le interfacce siano incluse (potrebbero non essere serializzate automaticamente)
            if asset.interfaces:
                from app.schemas.asset_interface import AssetInterface
                # Serialize interfaces manually if not already present
                if not asset_dict.get("interfaces") or len(asset_dict.get("interfaces", [])) == 0:
                    asset_dict["interfaces"] = [AssetInterface.from_orm(iface).dict() for iface in asset.interfaces]
            
            # Calcola rischio totale (base + dipendenze) usando i valori batch
            base_risk = asset.risk_score or 0.0
            risk_from_deps = risk_adjustments.get(str(asset.id), 0.0)
            total_risk = min(10.0, base_risk + risk_from_deps)
            
            asset_dict["total_risk_score"] = round(total_risk, 2)
            result.append(asset_dict)
        
        return {
            "data": result,
            "total": total_count,
            "skip": skip,
            "limit": limit
        }
    
    return {
        "data": [],
        "total": total_count,
        "skip": skip,
        "limit": limit
    }


# Trash: lista asset eliminati
@router.get("/trash", response_model=List[AssetSchema])
def list_assets_trash(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Asset)
        .filter(Asset.tenant_id == current_user.tenant_id, Asset.deleted_at != None)
        .offset(skip)
        .limit(limit)
        .all()
    )


# Get assets by location
@router.get("/by-location/{location_id}", response_model=List[AssetSchema])
def get_assets_by_location(
    location_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all assets for a specific location"""
    query = (
        db.query(Asset)
        .options(
            joinedload(Asset.interfaces),
            joinedload(Asset.site),
            joinedload(Asset.location),
            joinedload(Asset.status),
            joinedload(Asset.manufacturer),
            joinedload(Asset.asset_type),
            joinedload(Asset.security_zone),
        )
        .filter(
            Asset.tenant_id == current_user.tenant_id,
            Asset.location_id == location_id,
            Asset.deleted_at == None
        )
        .offset(skip)
        .limit(limit)
    )
    
    assets = query.all()
    return assets


@router.get("/for-network-map")
def get_assets_for_network_map(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 1000,  # Limite ragionevole per la network map
):
    """Get assets for network map visualization with pagination"""
    query = (
        db.query(Asset)
        .options(
            joinedload(Asset.interfaces),
            joinedload(Asset.site),
            joinedload(Asset.location),
            joinedload(Asset.status),
            joinedload(Asset.manufacturer),
            joinedload(Asset.asset_type),
            joinedload(Asset.security_zone),
        )
        .filter(Asset.tenant_id == current_user.tenant_id, Asset.deleted_at == None)
        .offset(skip)
        .limit(limit)
    )
    
    assets = query.all()
    result = []
    for asset in assets:
        # Converti manualmente senza validazione
        asset_dict = {
            "id": str(asset.id),
            "name": asset.name,
            "tag": asset.tag,
            "serial_number": asset.serial_number,
            "model": asset.model,
            "manufacturer_id": str(asset.manufacturer_id) if asset.manufacturer_id else None,
            "firmware_version": asset.firmware_version,
            "description": asset.description,
            "custom_fields": asset.custom_fields or {},
            "map_x": asset.map_x,
            "map_y": asset.map_y,
            "created_at": asset.created_at,
            "updated_at": asset.updated_at,
            "status_id": str(asset.status_id) if asset.status_id else None,
            "installation_date": asset.installation_date,
            "business_criticality": asset.business_criticality,
            "protocols": asset.protocols or [],
            "site_id": str(asset.site_id) if asset.site_id else None,
            "asset_type_id": str(asset.asset_type_id) if asset.asset_type_id else None,
            "location_id": str(asset.location_id) if asset.location_id else None,
            "area_id": str(asset.area_id) if asset.area_id else None,
            "impact_value": asset.impact_value,
            "purdue_level": asset.purdue_level,
            "exposure_level": asset.exposure_level,
            "update_status": asset.update_status,
            "risk_score": asset.risk_score,
            "last_risk_assessment": asset.last_risk_assessment,
            "remote_access": asset.remote_access,
            "remote_access_type": asset.remote_access_type,
            "last_update_date": asset.last_update_date,
            "physical_access_ease": asset.physical_access_ease,
            "interfaces": [],
            "manufacturer": {
                "id": str(asset.manufacturer.id),
                "name": asset.manufacturer.name
            } if asset.manufacturer else None,
            "site": {
                "id": str(asset.site.id),
                "name": asset.site.name
            } if asset.site else None,
            "asset_type": {
                "id": str(asset.asset_type.id),
                "name": asset.asset_type.name,
                "purdue_level": asset.asset_type.purdue_level
            } if asset.asset_type else None,
            "location": {
                "id": str(asset.location.id),
                "name": asset.location.name
            } if asset.location else None,
            "status": {
                "id": str(asset.status.id),
                "name": asset.status.name,
                "color": asset.status.color
            } if asset.status else None,
        }
        
        # Add area info if present
        if asset.area_id:
            from app.models.area import Area
            area = db.query(Area).filter(Area.id == asset.area_id).first()
            if area:
                asset_dict["area_name"] = area.name
                asset_dict["area_code"] = area.code
        
        result.append(asset_dict)
    
    return result


@router.get("/risk-overview", response_model=RiskOverviewResponse)
def get_risk_overview(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Restituisce l'overview generale del risk scoring (nuova logica composita)"""
    assets = (
        db.query(Asset)
        .filter(Asset.tenant_id == current_user.tenant_id, Asset.deleted_at == None)
        .all()
    )

    risk_engine = CompositeRiskScoringEngine()

    # Calculate risk score for all assets
    total_score = 0
    high_risk_count = 0
    medium_risk_count = 0
    low_risk_count = 0

    for asset in assets:
        breakdown = risk_engine.calculate(asset, db=db)
        risk_score = breakdown["final_score"]
        if risk_score is not None:
            total_score += risk_score
            # Update asset if the score has changed
            if asset.risk_score != risk_score:
                asset.risk_score = risk_score
                asset.last_risk_assessment = datetime.utcnow()
            # Count by risk level
            if risk_score >= 7:
                high_risk_count += 1
            elif risk_score >= 4:
                medium_risk_count += 1
            else:
                low_risk_count += 1

    db.commit()

    # Top 10 risky assets
    top_risk_assets = sorted(assets, key=lambda x: x.risk_score or 0, reverse=True)[:10]
    top_risk_data = []
    for asset in top_risk_assets:
        top_risk_data.append(
            {
                "id": str(asset.id),
                "name": asset.name,
                "risk_score": asset.risk_score,
                "risk_level": (
                    "alto"
                    if asset.risk_score is not None and asset.risk_score >= 7
                    else (
                        "medio"
                        if asset.risk_score is not None and asset.risk_score >= 4
                        else "basso"
                    )
                ),
                "business_criticality": getattr(asset, "business_criticality", None),
                "site_name": asset.site.name if asset.site else None,
            }
        )

    return RiskOverviewResponse(
        high_risk_count=high_risk_count,
        medium_risk_count=medium_risk_count,
        low_risk_count=low_risk_count,
        total_assets=len(assets),
        average_risk_score=round(total_score / len(assets), 2) if assets else 0,
        top_risk_assets=top_risk_data,
    )


@router.post("/recalculate-all-risk-scores")
def recalculate_all_risk_scores(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Recalculate the risk score for all tenant assets (new composite logic)"""
    assets = (
        db.query(Asset)
        .filter(Asset.tenant_id == current_user.tenant_id, Asset.deleted_at == None)
        .all()
    )

    risk_engine = CompositeRiskScoringEngine()
    updated_count = 0

    for asset in assets:
        breakdown = risk_engine.calculate(asset, db=db)
        new_score = breakdown["final_score"]
        old_score = asset.risk_score
        if new_score is not None and old_score != new_score:
            asset.risk_score = new_score
            asset.last_risk_assessment = datetime.utcnow()
            updated_count += 1

    db.commit()
    
    # Invalida tutta la cache del rischio per questo tenant
    from app.services.risk_cache import risk_cache
    risk_cache.invalidate_tenant(str(current_user.tenant_id))

    return {
        "message": f"Risk scores ricalcolati per {updated_count} asset su {len(assets)} totali",
        "updated_count": updated_count,
        "total_count": len(assets),
    }


@router.delete("/trash/empty")
@audit_log_action("empty_trash", "Asset", model_class=Asset)
def empty_assets_trash(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    from app.models.asset_interface import AssetInterface
    from app.models.asset_document import AssetDocument
    from app.models.asset_photo import AssetPhoto
    from app.models.asset_connection import AssetConnection
    from app.models.asset_communication import AssetCommunication
    from app.models.contact import Contact

    assets = (
        db.query(Asset)
        .filter(Asset.tenant_id == current_user.tenant_id, Asset.deleted_at != None)
        .all()
    )
    count = 0
    for asset in assets:
        # Delete communications where the asset's interfaces are involved
        interface_ids = [
            i.id
            for i in db.query(AssetInterface).filter(
                AssetInterface.asset_id == asset.id
            )
        ]
        if interface_ids:
            db.query(AssetCommunication).filter(
                (AssetCommunication.src_interface_id.in_(interface_ids))
                | (AssetCommunication.dst_interface_id.in_(interface_ids))
            ).delete(synchronize_session=False)
        # Delete connections where the asset is involved
        db.query(AssetConnection).filter(
            (AssetConnection.parent_asset_id == asset.id)
            | (AssetConnection.child_asset_id == asset.id)
        ).delete(synchronize_session=False)
        # Delete documents
        db.query(AssetDocument).filter(AssetDocument.asset_id == asset.id).delete(
            synchronize_session=False
        )
        # Delete photos
        db.query(AssetPhoto).filter(AssetPhoto.asset_id == asset.id).delete(
            synchronize_session=False
        )
        # Delete interfaces
        db.query(AssetInterface).filter(AssetInterface.asset_id == asset.id).delete(
            synchronize_session=False
        )
        # Delete associated contacts (many-to-many table)
        asset.contacts = []
        # Delete print history connected
        db.query(PrintHistory).filter(PrintHistory.asset_id == asset.id).delete(
            synchronize_session=False
        )
        db.delete(asset)
        count += 1
    db.commit()
    return {"detail": f"Trash emptied: {count} assets deleted"}


@router.post("/import/xlsx/preview")
def import_assets_xlsx_preview(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy import func
    from app.models.manufacturer import Manufacturer
    from app.models.asset_interface import AssetInterface
    import os

    def _validate_business_criticality(value):
        """Valida e pulisce il valore di business_criticality"""
        if not value or str(value).strip() in ["[NULL]", "NULL", ""]:
            return None
        clean_value = str(value).strip().lower()
        if clean_value in ["low", "medium", "high", "critical"]:
            return clean_value
        return None

    try:
        filename = file.filename.lower()
        if filename.endswith(".csv"):
            # Read CSV with string dtype for all columns to avoid numeric interpretation
            df = pd.read_csv(file.file, dtype=str)
            # Replace NaN values with None
            df = df.where(pd.notnull(df), None)
        else:
            df = pd.read_excel(file.file, engine="openpyxl")
    except Exception as e:
        return {"error": f"Error reading file: {str(e)}"}
    to_create, to_update, errors = [], [], []
    for idx, row in df.iterrows():
        name = row.get("nome") or row.get("name")
        tag = row.get("tag")
        site_code = row.get("site_code")
        asset_type_name = row.get("asset_type") or row.get("asset_type_name")
        ip_address = row.get("ip_address")
        manufacturer_name = row.get("manufacturer")
        missing = []
        # Handle None, empty string
        if name is None or str(name).strip() == "":
            missing.append("name")
        if site_code is None or str(site_code).strip() == "":
            missing.append("site_code")
        if asset_type_name is None or str(asset_type_name).strip() == "":
            missing.append("asset_type")
        site_id = None
        asset_type_id = None
        manufacturer_id = None
        status_id = None
                    # Validation of site_code and asset_type
        if not missing:
            from app.crud.sites import get_site_by_code

            site = get_site_by_code(db, current_user.tenant_id, site_code)
            if not site:
                errors.append(
                    {
                        "row": int(idx) + 2,
                        "error": f"Site con code '{site_code}' non trovato",
                    }
                )
            else:
                site_id = site.id
            from app.models.asset_type import AssetType

            asset_type = (
                db.query(AssetType)
                .filter(
                    AssetType.name.ilike(asset_type_name),
                    (AssetType.tenant_id == current_user.tenant_id)
                    | (AssetType.tenant_id == None),
                )
                .first()
            )
            if not asset_type:
                errors.append(
                    {
                        "row": int(idx) + 2,
                        "error": f"AssetType con name '{asset_type_name}' non trovato",
                    }
                )
            else:
                asset_type_id = asset_type.id
            
            # Get default status (Active)
            from app.models.asset_status import AssetStatus
            default_status = (
                db.query(AssetStatus)
                .filter(
                    AssetStatus.name == "Active",
                    AssetStatus.tenant_id == current_user.tenant_id,
                )
                .first()
            )
            if default_status:
                status_id = default_status.id
            else:
                # Fallback: get first available status
                first_status = (
                    db.query(AssetStatus)
                    .filter(AssetStatus.tenant_id == current_user.tenant_id)
                    .first()
                )
                if first_status:
                    status_id = first_status.id
                else:
                    errors.append(
                        {
                            "row": int(idx) + 2,
                            "error": "No asset status available",
                        }
                    )
                    continue
        # Validation/lookup/creation of manufacturer
        if not missing and manufacturer_name and str(manufacturer_name).strip() != "":
            manufacturer = (
                db.query(Manufacturer)
                .filter(
                    func.lower(Manufacturer.name)
                    == str(manufacturer_name).strip().lower(),
                    Manufacturer.tenant_id == current_user.tenant_id,
                )
                .first()
            )
            if not manufacturer:
                # We don't really create the manufacturer in preview, but we report that it will be created
                manufacturer_id = None
                manufacturer_action = "create"
            else:
                manufacturer_id = manufacturer.id
                manufacturer_action = "use_existing"
        else:
            manufacturer_action = None
        if missing or not site_id or not asset_type_id:
            if missing:
                errors.append(
                    {
                        "row": int(idx) + 2,
                        "error": f"Campi obbligatori mancanti: {', '.join(missing)}",
                    }
                )
            continue
        # Search asset only if tag is filled
        if tag is not None and not pd.isna(tag) and str(tag).strip() != "":
            asset = (
                db.query(Asset)
                .filter(Asset.tag == tag, Asset.tenant_id == current_user.tenant_id)
                .first()
            )
        else:
            asset = None
        # Prepare preview of interfaces
        interfaces = []
        if ip_address and not pd.isna(ip_address) and str(ip_address).strip() != "":
            interfaces.append(
                {
                    "name": "LAN",
                    "type": "ethernet",
                    "ip_address": str(ip_address).strip(),
                }
            )
        if asset:
            diff = {}
            # Check all CSV fields for differences
            csv_fields = {
                "name": name,
                "site_code": site_code,
                "asset_type": asset_type_name,
                "ip_address": row.get("ip_address"),
                "manufacturer": manufacturer_name,
                "serial_number": row.get("serial_number"),
                "model": row.get("model"),
                "firmware_version": row.get("firmware_version"),
                "description": row.get("description"),
                "business_criticality": row.get("business_criticality"),
                "physical_access_ease": row.get("physical_access_ease"),
                "purdue_level": row.get("purdue_level"),
                "installation_date": row.get("installation_date"),
            }
            
            for field, new_value in csv_fields.items():
                if field == "manufacturer":
                    # compare the manufacturer name
                    old_manuf = asset.manufacturer.name if asset.manufacturer else None
                    if (
                        str(old_manuf).strip().lower()
                        != str(new_value).strip().lower()
                    ):
                        diff[field] = {"old": old_manuf, "new": new_value}
                elif field == "site_code":
                    # compare site code
                    old_site_code = asset.site.code if asset.site else None
                    if str(old_site_code) != str(new_value):
                        diff[field] = {"old": old_site_code, "new": new_value}
                elif field == "asset_type":
                    # compare asset type name
                    old_asset_type = asset.asset_type.name if asset.asset_type else None
                    if str(old_asset_type) != str(new_value):
                        diff[field] = {"old": old_asset_type, "new": new_value}
                else:
                    old_value = getattr(asset, field, None)
                    if str(old_value) != str(new_value):
                        diff[field] = {"old": old_value, "new": new_value}
            
            if diff or interfaces:
                to_update.append(
                    {
                        "tag": tag,
                        "diff": diff,
                        "interfaces": interfaces,
                        "manufacturer_action": manufacturer_action,
                    }
                )
        else:
            to_create.append(
                {
                    "name": name,
                    "tag": tag,
                    "site_code": site_code,
                    "asset_type": asset_type_name,
                    "ip_address": row.get("ip_address"),
                    "manufacturer": manufacturer_name,
                    "serial_number": row.get("serial_number"),
                    "model": row.get("model"),
                    "firmware_version": row.get("firmware_version"),
                    "description": row.get("description"),
                    "business_criticality": row.get("business_criticality"),
                    "physical_access_ease": row.get("physical_access_ease"),
                    "purdue_level": row.get("purdue_level"),
                    "installation_date": row.get("installation_date"),
                    "manufacturer_action": manufacturer_action,
                    "interfaces": interfaces,
                }
            )
    return sanitize_for_json(
        {"to_create": to_create, "to_update": to_update, "errors": errors}
    )


def _validate_business_criticality(value):
    """Valida e pulisce il valore di business_criticality"""
    if not value or str(value).strip() in ["[NULL]", "NULL", ""]:
        return None
    clean_value = str(value).strip().lower()
    if clean_value in ["low", "medium", "high", "critical"]:
        return clean_value
    return None

@router.post("/import/xlsx/confirm")
def import_assets_xlsx_confirm(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.manufacturer import Manufacturer
    from app.models.asset_interface import AssetInterface
    from sqlalchemy import func
    import os

    try:
        filename = file.filename.lower()
        if filename.endswith(".csv"):
            # Read CSV with string dtype for all columns to avoid numeric interpretation
            df = pd.read_csv(file.file, dtype=str)
            # Replace NaN values with None
            df = df.where(pd.notnull(df), None)
        else:
            df = pd.read_excel(file.file, engine="openpyxl")
    except Exception as e:
        return {"error": f"Error reading file: {str(e)}"}
    created, updated, errors = [], [], []
    for idx, row in df.iterrows():
        name = row.get("nome") or row.get("name")
        tag = row.get("tag")
        site_code = row.get("site_code")
        asset_type_name = row.get("asset_type") or row.get("asset_type_name")
        ip_address = row.get("ip_address")
        manufacturer_name = row.get("manufacturer")
        missing = []
        if name is None or str(name).strip() == "":
            missing.append("name")
        if site_code is None or str(site_code).strip() == "":
            missing.append("site_code")
        if asset_type_name is None or str(asset_type_name).strip() == "":
            missing.append("asset_type")
        site_id = None
        asset_type_id = None
        manufacturer_id = None
        status_id = None
        if not missing:
            from app.crud.sites import get_site_by_code

            site = get_site_by_code(db, current_user.tenant_id, site_code)
            if not site:
                errors.append(
                    {
                        "row": int(idx) + 2,
                        "error": f"Site con code '{site_code}' non trovato",
                    }
                )
            else:
                site_id = site.id
            from app.models.asset_type import AssetType

            asset_type = (
                db.query(AssetType)
                .filter(
                    AssetType.name.ilike(asset_type_name),
                    (AssetType.tenant_id == current_user.tenant_id)
                    | (AssetType.tenant_id == None),
                )
                .first()
            )
            if not asset_type:
                errors.append(
                    {
                        "row": int(idx) + 2,
                        "error": f"AssetType con name '{asset_type_name}' non trovato",
                    }
                )
            else:
                asset_type_id = asset_type.id
            
            # Get default status (Active)
            from app.models.asset_status import AssetStatus
            default_status = (
                db.query(AssetStatus)
                .filter(
                    AssetStatus.name == "Active",
                    AssetStatus.tenant_id == current_user.tenant_id,
                )
                .first()
            )
            if default_status:
                status_id = default_status.id
            else:
                # Fallback: get first available status
                first_status = (
                    db.query(AssetStatus)
                    .filter(AssetStatus.tenant_id == current_user.tenant_id)
                    .first()
                )
                if first_status:
                    status_id = first_status.id
                else:
                    errors.append(
                        {
                            "row": int(idx) + 2,
                            "error": "No asset status available",
                        }
                    )
                    continue
        # Lookup/creazione manufacturer
        if not missing and manufacturer_name and str(manufacturer_name).strip() != "":
            manufacturer = (
                db.query(Manufacturer)
                .filter(
                    func.lower(Manufacturer.name)
                    == str(manufacturer_name).strip().lower(),
                    Manufacturer.tenant_id == current_user.tenant_id,
                )
                .first()
            )
            if not manufacturer:
                try:
                    manufacturer = Manufacturer(
                        name=str(manufacturer_name).strip(),
                        tenant_id=current_user.tenant_id,
                    )
                    db.add(manufacturer)
                    db.commit()
                    db.refresh(manufacturer)
                except Exception as e:
                    db.rollback()
                    errors.append(
                        {
                            "row": int(idx) + 2,
                            "error": f"Error creating manufacturer: {str(e)}",
                        }
                    )
                    continue
            manufacturer_id = manufacturer.id
        if missing or not site_id or not asset_type_id:
            if missing:
                errors.append(
                    {
                        "row": int(idx) + 2,
                        "error": f"Campi obbligatori mancanti: {', '.join(missing)}",
                    }
                )
            continue
        # Search assets only if tag is provided
        if tag is not None and not pd.isna(tag) and str(tag).strip() != "":
            asset = (
                db.query(Asset)
                .filter(Asset.tag == tag, Asset.tenant_id == current_user.tenant_id)
                .first()
            )
        else:
            asset = None
        try:
            if asset:
                # Parse installation_date if provided
                installation_date = None
                if row.get("installation_date") and str(row.get("installation_date")).strip() != "":
                    try:
                        installation_date = datetime.strptime(str(row.get("installation_date")).strip(), "%Y-%m-%d").date()
                    except (ValueError, TypeError):
                        pass  # Keep as None if parsing fails
                
                # Parse purdue_level if provided
                purdue_level = 0.0
                if row.get("purdue_level") and str(row.get("purdue_level")).strip() != "":
                    try:
                        purdue_level = float(str(row.get("purdue_level")).strip())
                    except (ValueError, TypeError):
                        pass  # Keep default if parsing fails
                
                asset.name = name
                asset.site_id = site_id
                asset.asset_type_id = asset_type_id
                if manufacturer_id:
                    asset.manufacturer_id = manufacturer_id
                asset.serial_number = row.get("serial_number")
                asset.model = row.get("model")
                asset.firmware_version = row.get("firmware_version")
                asset.description = row.get("description")
                asset.business_criticality = _validate_business_criticality(row.get("business_criticality"))
                asset.physical_access_ease = row.get("physical_access_ease")
                asset.purdue_level = purdue_level
                asset.installation_date = installation_date
                db.commit()
                updated.append(tag)
                # If ip_address present, create LAN interface if not already present
                if (
                    ip_address
                    and not pd.isna(ip_address)
                    and str(ip_address).strip() != ""
                ):
                    existing_iface = (
                        db.query(AssetInterface)
                        .filter(
                            AssetInterface.asset_id == asset.id,
                            func.lower(AssetInterface.name) == "lan",
                            AssetInterface.type == "ethernet",
                            AssetInterface.ip_address == str(ip_address).strip(),
                        )
                        .first()
                    )
                    if not existing_iface:
                        interface = AssetInterface(
                            asset_id=asset.id,
                            name="LAN",
                            type="ethernet",
                            ip_address=str(ip_address).strip(),
                            tenant_id=current_user.tenant_id,
                        )
                        db.add(interface)
                        db.commit()
            else:
                # Parse installation_date if provided
                installation_date = None
                if row.get("installation_date") and str(row.get("installation_date")).strip() != "":
                    try:
                        installation_date = datetime.strptime(str(row.get("installation_date")).strip(), "%Y-%m-%d").date()
                    except (ValueError, TypeError):
                        pass  # Keep as None if parsing fails
                
                # Parse purdue_level if provided
                purdue_level = 0.0
                if row.get("purdue_level") and str(row.get("purdue_level")).strip() != "":
                    try:
                        purdue_level = float(str(row.get("purdue_level")).strip())
                    except (ValueError, TypeError):
                        pass  # Keep default if parsing fails
                
                new_asset = Asset(
                    name=name,
                    tag=tag,
                    site_id=site_id,
                    asset_type_id=asset_type_id,
                    status_id=status_id,
                    tenant_id=current_user.tenant_id,
                    manufacturer_id=manufacturer_id,
                    serial_number=row.get("serial_number"),
                    model=row.get("model"),
                    firmware_version=row.get("firmware_version"),
                    description=row.get("description"),
                    business_criticality=_validate_business_criticality(row.get("business_criticality")),
                    physical_access_ease=row.get("physical_access_ease"),
                    purdue_level=purdue_level,
                    installation_date=installation_date,
                )
                db.add(new_asset)
                db.commit()
                created.append(tag)
                # If ip_address present, create LAN interface if not already present
                if (
                    ip_address
                    and not pd.isna(ip_address)
                    and str(ip_address).strip() != ""
                ):
                    interface = AssetInterface(
                        asset_id=new_asset.id,
                        name="LAN",
                        type="ethernet",
                        ip_address=str(ip_address).strip(),
                        tenant_id=current_user.tenant_id,
                    )
                    db.add(interface)
                    db.commit()
        except IntegrityError as e:
            db.rollback()
            errors.append(
                {"row": int(idx) + 2, "error": f"Integrity error: {str(e)}"}
            )
        except Exception as e:
            db.rollback()
            errors.append({"row": int(idx) + 2, "error": str(e)})
    return sanitize_for_json({"created": created, "updated": updated, "errors": errors})


@router.post("/bulk-update")
def bulk_update_assets(
    req: AssetBulkUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    updated, errors = [], []
    language = resolve_audit_language(current_user, request)

    for asset_id in req.ids:
        asset = (
            db.query(Asset)
            .filter(Asset.id == asset_id, Asset.tenant_id == current_user.tenant_id)
            .first()
        )
        if not asset:
            errors.append({"id": str(asset_id), "error": "Asset non trovato"})
            continue

        # Prepare old data with names
        old_data = {}
        for field in req.fields.keys():
            if hasattr(asset, field):
                old_data[field] = getattr(asset, field)

        # Apply the changes
        for field, value in req.fields.items():
            if hasattr(asset, field):
                setattr(asset, field, value)

        try:
            db.commit()
            updated.append(str(asset_id))

            create_audit_log(
                db=db,
                user_id=current_user.id,
                tenant_id=current_user.tenant_id,
                action="bulk_update",
                entity="Asset",
                entity_id=asset_id,
                old_data=old_data,
                new_data=req.fields,
                language=language,
            )
        except Exception as e:
            db.rollback()
            errors.append({"id": str(asset_id), "error": str(e)})

    return {"updated": updated, "errors": errors}


# Bulk soft delete
@router.post("/bulk-soft-delete")
def bulk_soft_delete_assets(
    req: AssetBulkSoftDeleteRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    deleted, errors = [], []
    language = resolve_audit_language(current_user, request)

    for asset_id in req.ids:
        asset = (
            db.query(Asset)
            .filter(
                Asset.id == asset_id, 
                Asset.tenant_id == current_user.tenant_id,
                Asset.deleted_at == None
            )
            .first()
        )
        if not asset:
            errors.append({"id": str(asset_id), "error": "Asset non trovato o già nel cestino"})
            continue

        try:
            # Soft delete
            asset.deleted_at = datetime.utcnow()

            db.commit()
            deleted.append(str(asset_id))

            try:
                create_audit_log(
                    db=db,
                    user_id=current_user.id,
                    tenant_id=current_user.tenant_id,
                    action="soft_delete",
                    entity="Asset",
                    entity_id=asset_id,
                    old_data={"deleted_at": None},
                    new_data={"deleted_at": asset.deleted_at.isoformat()},
                    language=language,
                )
            except Exception as audit_error:
                # Log audit error but don't rollback the soft delete
                # print(f"Audit log error for asset {asset_id}: {audit_error}")
                pass
                
        except Exception as e:
            db.rollback()
            errors.append({"id": str(asset_id), "error": str(e)})

    return {"deleted": deleted, "errors": errors}


# Get single asset
@router.get("/{asset_id}", response_model=AssetRead)
def get_asset(
    asset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    asset = (
        db.query(Asset)
        .options(
            joinedload(Asset.security_zone),
        )
        .filter(Asset.id == asset_id)
        .first()
    )
    if not asset or asset.tenant_id != current_user.tenant_id:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)
    
    # Carica l'area se l'asset ha un area_id
    if asset.area_id:
        from app.models.area import Area
        area = db.query(Area).filter(Area.id == asset.area_id).first()
        if area:
            # Assegna direttamente i campi dell'area all'asset
            asset.area_name = area.name
            asset.area_code = area.code
    
    return asset


# Update asset
@router.put("/{asset_id}", response_model=AssetSchema)
@audit_log_action("update", "Asset", model_class=Asset)
def update_asset(
    asset_id: uuid.UUID,
    asset_update: AssetUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    asset = crud_assets.get_asset(db, asset_id)
    if not asset:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)
    
    # Store old risk score before update
    old_risk_score = asset.risk_score
    
    # Check if risk-affecting fields are being updated
    risk_affecting_fields = {
        'business_criticality', 'physical_access_ease', 'remote_access', 
        'remote_access_type', 'purdue_level'
    }
    update_dict = asset_update.dict(exclude_unset=True)
    risk_fields_changed = any(field in update_dict for field in risk_affecting_fields)
    
    result = crud_assets.update_asset(db, asset_id, asset_update, current_user.tenant_id)
    
    # Refresh asset to get updated values
    db.refresh(result)
    
    # Invalida cache dashboard dopo aggiornamento asset
    from app.services.dashboard_cache import invalidate_dashboard_cache
    invalidate_dashboard_cache(str(current_user.tenant_id))
    
    # Auto-match vulnerabilities in background if asset has relevant info
    from app.services.vulnerability_auto_match import VulnerabilityAutoMatcher
    if VulnerabilityAutoMatcher.should_auto_match_asset(result):
        # Controlla se manufacturer, model o firmware sono stati aggiornati
        if (asset_update.manufacturer_id is not None or 
            asset_update.model is not None or 
            asset_update.firmware_version is not None):
            VulnerabilityAutoMatcher.match_asset_async(result.id, current_user.tenant_id)
    
    # Recalculate risk if risk-affecting fields changed
    if risk_fields_changed:
        try:
            from app.services.risk_scoring import CompositeRiskScoringEngine
            risk_engine = CompositeRiskScoringEngine()
            breakdown = risk_engine.calculate(result, db=db)
            new_risk_score = breakdown["final_score"]
            
            if new_risk_score is not None:
                result.risk_score = new_risk_score
                result.last_risk_assessment = datetime.utcnow()
                db.commit()
                db.refresh(result)
                
                # Check if risk changed significantly and send notification
                # The notification service will filter based on user preferences (severity_min)
                should_notify = False
                if old_risk_score is None:
                    # First risk calculation - notify if risk is present
                    should_notify = True
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.info(f"Asset {asset_id}: First risk calculation, risk_score={new_risk_score}, will notify")
                elif old_risk_score is not None:
                    # Check for significant change (>= 2 points increase)
                    if new_risk_score - old_risk_score >= 2:
                        should_notify = True
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.info(f"Asset {asset_id}: Significant risk increase ({old_risk_score} -> {new_risk_score}), will notify")
                    # Also notify if crossing threshold (e.g., from < 7 to >= 7)
                    elif (old_risk_score < 7 and new_risk_score >= 7) or (old_risk_score >= 7 and new_risk_score < 7):
                        should_notify = True
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.info(f"Asset {asset_id}: Risk crossed threshold ({old_risk_score} -> {new_risk_score}), will notify")
                    # Also notify if risk increases and is already high (>= 7)
                    # This ensures users get notified even for smaller increases if risk is already high
                    elif new_risk_score >= 7 and new_risk_score > old_risk_score:
                        should_notify = True
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.info(f"Asset {asset_id}: Risk increased while already high ({old_risk_score} -> {new_risk_score}), will notify")
                
                if should_notify:
                    # Determine risk level for notification
                    risk_level = "high" if new_risk_score >= 7 else ("medium" if new_risk_score >= 4 else "low")
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.info(f"Asset {asset_id}: Sending risk alert notification, risk_score={new_risk_score}, risk_level={risk_level}")
                    from app.services.notification_service import NotificationService
                    notifications = NotificationService.send_risk_alert(
                        db, asset_id, new_risk_score, risk_level
                    )
                    logger.info(f"Asset {asset_id}: Risk alert notification process completed, {len(notifications)} notifications queued")
                else:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.debug(f"Asset {asset_id}: Risk changed ({old_risk_score} -> {new_risk_score}) but notification conditions not met")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error recalculating risk for asset {asset_id}: {e}", exc_info=True)
            # Don't fail the update if risk calculation fails
    
    return result


# Soft delete
@router.delete("/{asset_id}")
@audit_log_action("soft_delete", "Asset", model_class=Asset)
def soft_delete_asset(
    asset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    asset = (
        db.query(Asset)
        .filter(
            Asset.id == asset_id,
            Asset.tenant_id == current_user.tenant_id,
            Asset.deleted_at == None,
        )
        .first()
    )
    if not asset:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)
    asset.deleted_at = datetime.utcnow()
    db.commit()
    
    # Invalida cache dashboard dopo soft delete
    from app.services.dashboard_cache import invalidate_dashboard_cache
    invalidate_dashboard_cache(str(current_user.tenant_id))
    
    return {"detail": "Asset moved to trash"}


# Restore
@router.patch("/{asset_id}/restore")
@audit_log_action("restore", "Asset", model_class=Asset)
def restore_asset(
    asset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    asset = (
        db.query(Asset)
        .filter(
            Asset.id == asset_id,
            Asset.tenant_id == current_user.tenant_id,
            Asset.deleted_at != None,
        )
        .first()
    )
    if not asset:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)
    asset.deleted_at = None
    db.commit()
    return {"detail": "Asset restored"}


    # Hard delete (only if already in trash)
@router.delete("/{asset_id}/hard")
@audit_log_action("hard_delete", "Asset", model_class=Asset)
def hard_delete_asset(
    asset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    asset = (
        db.query(Asset)
        .filter(
            Asset.id == asset_id,
            Asset.tenant_id == current_user.tenant_id,
            Asset.deleted_at != None,
        )
        .first()
    )
    if not asset:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)
    db.delete(asset)
    db.commit()
    return {"detail": "Asset deleted definitively"}


@router.patch("/{asset_id}/custom-fields", response_model=AssetSchema)
@audit_log_action("update_custom_fields", "Asset", model_class=Asset)
def patch_custom_fields(
    asset_id: uuid.UUID,
    custom_fields_update: AssetCustomFieldUpdate,
    db: Session = Depends(get_db),
):
    asset = crud_assets.update_asset_custom_fields(db, asset_id, custom_fields_update)
    if not asset:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)
    return asset


@router.patch("/{asset_id}/position")
@audit_log_action("update_position", "Asset", model_class=Asset)
def update_asset_position_endpoint(
    asset_id: uuid.UUID,
    position: PositionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    asset = crud_assets.update_asset_position(
        db, asset_id, position.map_x, position.map_y
    )
    if not asset or asset.tenant_id != current_user.tenant_id:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)
    return {"id": asset_id, "map_x": asset.map_x, "map_y": asset.map_y}


@router.get("/{asset_id}/zone-memberships")
def get_asset_zone_memberships(
    asset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _iec62443=Depends(require_iec62443_enabled),
):
    """Get all zone memberships for an asset"""
    from app.crud import asset_zone_memberships as crud_memberships
    from app.schemas.asset_zone_membership import AssetZoneMembershipRead
    from sqlalchemy.orm import joinedload
    
    # Verify asset exists
    asset = crud_assets.get_asset(db, asset_id)
    if not asset or asset.tenant_id != current_user.tenant_id:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)
    
    # Get memberships with zone details
    memberships = (
        db.query(AssetZoneMembership)
        .options(
            joinedload(AssetZoneMembership.security_zone),
            joinedload(AssetZoneMembership.asset)
        )
        .filter(
            AssetZoneMembership.asset_id == asset_id,
            AssetZoneMembership.tenant_id == current_user.tenant_id,
            AssetZoneMembership.deleted_at.is_(None)
        )
        .all()
    )
    
    # Convert to response format with zone and asset names
    result = []
    for m in memberships:
        membership_dict = {
            "id": m.id,
            "tenant_id": m.tenant_id,
            "asset_id": m.asset_id,
            "security_zone_id": m.security_zone_id,
            "role": m.role,
            "interface_scope": m.interface_scope,
            "sl_target": m.sl_target,
            "notes": m.notes,
            "created_at": m.created_at,
            "updated_at": m.updated_at,
            "deleted_at": m.deleted_at,
            "asset_name": m.asset.name if m.asset else None,
            "security_zone_name": m.security_zone.name if m.security_zone else None
        }
        result.append(membership_dict)
    
    return result


@router.get("/{asset_id}/communications")
def get_asset_communications(asset_id: uuid.UUID, db: Session = Depends(get_db)):
    # Check if asset exists
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise ErrorCodeException(status_code=404, error_code="ASSET_NOT_FOUND")

    # Find all interfaces of this asset
    interfaces = (
        db.query(AssetInterface).filter(AssetInterface.asset_id == asset_id).all()
    )
    interface_ids = [i.id for i in interfaces]
    if not interface_ids:
        return []

    # Search communications where one of the interfaces is involved
    comms = (
        db.query(AssetCommunication)
        .filter(
            (AssetCommunication.src_interface_id.in_(interface_ids))
            | (AssetCommunication.dst_interface_id.in_(interface_ids))
        )
        .all()
    )

    results = []
    for c in comms:
        # Retrieve all involved entities
        src_iface = c.src_interface
        dst_iface = c.dst_interface
        src_asset = (
            db.query(Asset).filter(Asset.id == src_iface.asset_id).first()
            if src_iface
            else None
        )
        dst_asset = (
            db.query(Asset).filter(Asset.id == dst_iface.asset_id).first()
            if dst_iface
            else None
        )
        if not src_asset or not dst_asset:
            continue
        # Direction relative to the requested asset
        if src_iface and src_iface.asset_id == asset_id:
            direction = "outgoing"
        elif dst_iface and dst_iface.asset_id == asset_id:
            direction = "incoming"
        else:
            direction = "unknown"
        results.append(
            {
                "src_asset": {"id": str(src_asset.id), "name": src_asset.name},
                "src_interface": (
                    {
                        "id": str(src_iface.id),
                        "name": src_iface.name,
                        "mac_address": src_iface.mac_address,
                        "ip_address": src_iface.ip_address,
                    }
                    if src_iface
                    else None
                ),
                "dst_asset": {"id": str(dst_asset.id), "name": dst_asset.name},
                "dst_interface": (
                    {
                        "id": str(dst_iface.id),
                        "name": dst_iface.name,
                        "mac_address": dst_iface.mac_address,
                        "ip_address": dst_iface.ip_address,
                    }
                    if dst_iface
                    else None
                ),
                "packet_count": c.packet_count,
                "direction": direction,
            }
        )

    return results


@router.get("/{asset_id}/contacts", response_model=List[AssetContact])
def list_asset_contacts(
    asset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all contacts for an asset with their roles"""
    asset = (
        db.query(Asset)
        .filter(Asset.id == asset_id, Asset.tenant_id == current_user.tenant_id)
        .first()
    )
    if not asset:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)
    
    contacts_with_roles = crud_assets.get_asset_contacts_with_roles(db, asset_id)
    return [
        AssetContact(contact=ContactSchema.from_orm(item["contact"]), role=item["role"])
        for item in contacts_with_roles
    ]


@router.get("/{asset_id}/contacts/owners", response_model=List[ContactSchema])
def list_asset_owners(
    asset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List owners of an asset"""
    asset = (
        db.query(Asset)
        .filter(Asset.id == asset_id, Asset.tenant_id == current_user.tenant_id)
        .first()
    )
    if not asset:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)
    
    owners = crud_assets.get_asset_contacts_by_role(db, asset_id, "owner")
    return [ContactSchema.from_orm(c) for c in owners]


@router.get("/{asset_id}/contacts/points-of-contact", response_model=List[ContactSchema])
def list_asset_points_of_contact(
    asset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List points of contact for an asset"""
    asset = (
        db.query(Asset)
        .filter(Asset.id == asset_id, Asset.tenant_id == current_user.tenant_id)
        .first()
    )
    if not asset:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)
    
    points_of_contact = crud_assets.get_asset_contacts_by_role(db, asset_id, "point_of_contact")
    return [ContactSchema.from_orm(c) for c in points_of_contact]


@router.put("/{asset_id}/contacts", response_model=List[AssetContact])
@audit_log_action("update_contacts", "Asset", model_class=Asset)
def update_asset_contacts(
    asset_id: uuid.UUID,
    contacts: List[AssetContactCreate],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update contacts for an asset with their roles"""
    from app.models.contact import Contact

    asset = (
        db.query(Asset)
        .filter(Asset.id == asset_id, Asset.tenant_id == current_user.tenant_id)
        .first()
    )
    if not asset:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)
    
    # Validate all contacts exist and belong to tenant
    contact_ids = [c.contact_id for c in contacts]
    db_contacts = (
        db.query(Contact)
        .filter(
            Contact.id.in_(contact_ids), 
            Contact.tenant_id == current_user.tenant_id
        )
        .all()
    )
    
    if len(db_contacts) != len(contact_ids):
        raise ErrorCodeException(
            status_code=404, 
            error_code=ErrorCode.ASSET_NOT_FOUND,
            detail="One or more contacts not found"
        )
    
    # Update contacts with roles
    contacts_data = [
        {"contact_id": c.contact_id, "role": c.role}
        for c in contacts
    ]
    crud_assets.update_asset_contacts_with_roles(db, asset_id, contacts_data)
    
    # Return updated contacts with roles
    contacts_with_roles = crud_assets.get_asset_contacts_with_roles(db, asset_id)
    return [
        AssetContact(contact=ContactSchema.from_orm(item["contact"]), role=item["role"])
        for item in contacts_with_roles
    ]


@router.post("/{asset_id}/contacts", response_model=AssetContact, status_code=201)
@audit_log_action("add_contact", "Asset", model_class=Asset)
def add_asset_contact(
    asset_id: uuid.UUID,
    contact: AssetContactCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a contact to an asset with a specific role"""
    from app.models.contact import Contact
    
    asset = (
        db.query(Asset)
        .filter(Asset.id == asset_id, Asset.tenant_id == current_user.tenant_id)
        .first()
    )
    if not asset:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)
    
    # Validate contact exists and belongs to tenant
    db_contact = (
        db.query(Contact)
        .filter(
            Contact.id == contact.contact_id,
            Contact.tenant_id == current_user.tenant_id
        )
        .first()
    )
    if not db_contact:
        raise ErrorCodeException(
            status_code=404,
            error_code=ErrorCode.ASSET_NOT_FOUND,
            detail="Contact not found"
        )
    
    # Add contact with role
    crud_assets.add_asset_contact_with_role(
        db, asset_id, contact.contact_id, contact.role
    )
    
    return AssetContact(
        contact=ContactSchema.from_orm(db_contact),
        role=contact.role
    )


@router.delete("/{asset_id}/contacts/{contact_id}", status_code=204)
@audit_log_action("delete_contact", "Asset", model_class=Asset)
def delete_asset_contact(
    asset_id: uuid.UUID,
    contact_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a contact from an asset"""
    asset = (
        db.query(Asset)
        .filter(Asset.id == asset_id, Asset.tenant_id == current_user.tenant_id)
        .first()
    )
    if not asset:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)
    
    crud_assets.remove_asset_contact(db, asset_id, contact_id)
    return None


@router.get("/{asset_id}/suppliers", response_model=List[SupplierSchema])
def list_asset_suppliers(
    asset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    asset = (
        db.query(Asset)
        .filter(Asset.id == asset_id, Asset.tenant_id == current_user.tenant_id)
        .first()
    )
    if not asset:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)
    return asset.suppliers


@router.put("/{asset_id}/suppliers", response_model=List[SupplierSchema])
@audit_log_action("update_suppliers", "Asset", model_class=Asset)
def update_asset_suppliers(
    asset_id: uuid.UUID,
    supplier_ids: List[uuid.UUID],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    asset = (
        db.query(Asset)
        .filter(Asset.id == asset_id, Asset.tenant_id == current_user.tenant_id)
        .first()
    )
    if not asset:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)
    suppliers = (
        db.query(Supplier)
        .filter(
            Supplier.id.in_(supplier_ids), Supplier.tenant_id == current_user.tenant_id
        )
        .all()
    )
    asset.suppliers = suppliers
    db.commit()
    db.refresh(asset)
    return asset.suppliers


@router.post("/{asset_id}/calculate-risk", response_model=RiskScoreResponse)
def calculate_asset_risk(
    asset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Calculate the risk score for a single asset (new composite logic)"""
    asset = crud_assets.get_asset(db, asset_id)
    if not asset or asset.tenant_id != current_user.tenant_id:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)

    # Store old risk score to detect changes
    old_risk_score = asset.risk_score
    old_risk_level = None
    if old_risk_score is not None:
        if old_risk_score >= 7:
            old_risk_level = "high"
        elif old_risk_score >= 4:
            old_risk_level = "medium"
        else:
            old_risk_level = "low"

    risk_engine = CompositeRiskScoringEngine()
    breakdown = risk_engine.calculate(asset, db=db)
    risk_score = breakdown["final_score"]
    # Determine level and severity
    if risk_score is None:
        risk_level = "undefined"
        risk_severity = "info"
    elif risk_score >= 7:
        risk_level = "high"
        risk_severity = "danger"
    elif risk_score >= 4:
        risk_level = "medium"
        risk_severity = "warning"
    else:
        risk_level = "low"
        risk_severity = "success"
    
    # Update asset only if risk_score is calculated
    if risk_score is not None:
        asset.risk_score = risk_score
        asset.last_risk_assessment = datetime.utcnow()
        db.commit()
        db.refresh(asset)
        
        # Check if risk changed significantly
        # The notification service will filter based on user preferences (severity_min)
        should_notify = False
        if old_risk_score is None:
            # First risk calculation - notify if risk is present
            should_notify = True
        elif old_risk_score is not None:
            # Check for significant change (>= 2 points increase)
            if risk_score - old_risk_score >= 2:
                should_notify = True
            # Also notify if crossing threshold (e.g., from < 7 to >= 7)
            elif (old_risk_score < 7 and risk_score >= 7) or (old_risk_score >= 7 and risk_score < 7):
                should_notify = True
            # Or if risk level changed significantly
            elif old_risk_level != risk_level and (old_risk_level == "low" and risk_level == "high"):
                should_notify = True
        
        if should_notify:
            # Send risk alert notification
            # The notification service will check user preferences (severity_min) before sending
            try:
                from app.services.notification_service import NotificationService
                NotificationService.send_risk_alert(
                    db, asset_id, risk_score, risk_level
                )
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error sending risk alert for asset {asset_id}: {e}", exc_info=True)
    
    return RiskScoreResponse(
        asset_id=asset_id,
        risk_score=risk_score,
        risk_level=risk_level,
        risk_severity=risk_severity,
        breakdown=breakdown,
    )


def sanitize_for_json(obj):
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(x) for x in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    else:
        return obj
