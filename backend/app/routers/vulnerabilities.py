# backend/app/routers/vulnerabilities.py
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models import User, Asset
from app.models.vulnerability import AssetVulnerability, Vulnerability
from app.services.auth import get_current_user
from app.services.audit_decorator import audit_log_action
from app.services.rbac import require_permission
from app.crud import vulnerabilities as crud_vulns
from app.schemas.vulnerability import (
    VulnerabilityRead,
    VulnerabilityCreate,
    VulnerabilityUpdate,
    AssetVulnerabilityRead,
    AssetVulnerabilityCreate,
    AssetVulnerabilityUpdate,
    VulnerabilityFeedSourceRead,
    VulnerabilityFeedSourceCreate,
    VulnerabilityFeedSourceUpdate,
    VulnerabilityStats
)
from app.errors.exceptions import ErrorCodeException
from app.errors.error_codes import ErrorCode
from app.services.vulnerability_matcher import VulnerabilityMatcher
from app.services.vulnerability_feed import VulnerabilityFeedService
from app.services.vulnerability_impact import VulnerabilityImpactCalculator

router = APIRouter(
    prefix="/vulnerabilities",
    tags=["vulnerabilities"],
)


# Feed Sources - DEVE essere PRIMA di /{vulnerability_id} per evitare conflitti di routing
@router.get("/feeds", response_model=List[VulnerabilityFeedSourceRead])
def list_vulnerability_feeds(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("vulnerabilities", 1)),
):
    """List all vulnerability feed sources"""
    return crud_vulns.get_vulnerability_feed_sources(
        db, tenant_id=current_user.tenant_id
    )


@router.post("/feeds", response_model=VulnerabilityFeedSourceRead, status_code=201)
@audit_log_action("create", "VulnerabilityFeedSource")
def create_vulnerability_feed(
    feed_source: VulnerabilityFeedSourceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("vulnerabilities", 2)),
):
    """Create a new vulnerability feed source"""
    if feed_source.tenant_id is None:
        # Only users with delete permission (level 3) can create system-wide feeds
        from app.services.rbac import get_user_permission_level
        if get_user_permission_level(current_user, "vulnerabilities") < 3:
            raise ErrorCodeException(
                status_code=403,
                error_code=ErrorCode.ACCESS_DENIED,
                detail="Only admins can create system-wide feeds"
            )
    else:
        feed_source.tenant_id = current_user.tenant_id
    
    return crud_vulns.create_vulnerability_feed_source(db, feed_source)


@router.post("/feeds/upload", response_model=VulnerabilityFeedSourceRead, status_code=201)
@audit_log_action("create", "VulnerabilityFeedSource")
async def upload_local_feed(
    file: UploadFile = File(...),
    name: str = Form(...),
    source_type: str = Form("custom"),
    feed_format: str = Form(...),
    parser_template: str = Form("nvd"),
    sync_interval_hours: int = Form(24),
    sync_enabled: bool = Form(True),
    auto_match: bool = Form(True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("vulnerabilities", 2)),
):
    """Upload and process a local vulnerability feed file"""
    import os
    import tempfile
    from pathlib import Path
    
    # Validate file format
    file_ext = Path(file.filename).suffix.lower()
    format_map = {
        '.json': 'json',
        '.xml': 'xml',
        '.rss': 'rss',
        '.csv': 'csv'
    }
    
    if file_ext not in format_map:
        raise ErrorCodeException(
            status_code=400,
            error_code=ErrorCode.INVALID_INPUT,
            detail=f"Unsupported file format: {file_ext}. Supported: {', '.join(format_map.keys())}"
        )
    
    if format_map[file_ext] != feed_format:
        raise ErrorCodeException(
            status_code=400,
            error_code=ErrorCode.INVALID_INPUT,
            detail=f"File format ({file_ext}) doesn't match specified format ({feed_format})"
        )
    
    # Save file temporarily
    temp_dir = tempfile.gettempdir()
    temp_file_path = os.path.join(temp_dir, f"vuln_feed_{uuid.uuid4()}{file_ext}")
    
    try:
        # Read and save file
        content = await file.read()
        with open(temp_file_path, 'wb') as f:
            f.write(content)
        
        # Create feed source record
        feed_source_data = VulnerabilityFeedSourceCreate(
            name=name,
            source_type=source_type,
            feed_url=f"file://{temp_file_path}",  # Store file path
            feed_format=feed_format,
            sync_interval_hours=sync_interval_hours,
            sync_enabled=sync_enabled,
            filters={"parser_template": parser_template, "feed_type": "local"}
        )
        feed_source_data.tenant_id = current_user.tenant_id
        
        feed_source = crud_vulns.create_vulnerability_feed_source(db, feed_source_data)
        
        # Process file and create vulnerabilities
        try:
            result = VulnerabilityFeedService.sync_local_feed(
                db, feed_source.id, temp_file_path, feed_format, parser_template, 
                current_user.tenant_id, auto_match
            )
            # Update feed source with sync results
            feed_source.last_sync_at = result.get('synced_at')
            feed_source.last_sync_status = result.get('status', 'success')
            feed_source.last_sync_count = result.get('synced_count', 0)
            feed_source.last_sync_error = result.get('error')
            db.commit()
            db.refresh(feed_source)
        except Exception as e:
            # Log error but don't fail feed creation
            feed_source.last_sync_status = 'failed'
            feed_source.last_sync_error = str(e)
            db.commit()
            db.refresh(feed_source)
        
        return feed_source
        
    except Exception as e:
        # Clean up temp file on error
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise ErrorCodeException(
            status_code=400,
            error_code=ErrorCode.INVALID_INPUT,
            detail=f"Error processing feed file: {str(e)}"
        )


@router.post("/feeds/{feed_source_id}/sync")
def sync_vulnerability_feed(
    feed_source_id: uuid.UUID,
    auto_match: bool = Query(True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("vulnerabilities", 2)),
):
    """Sync a vulnerability feed manually"""
    try:
        result = VulnerabilityFeedService.sync_feed(
            db, feed_source_id, current_user.tenant_id, auto_match
        )
        return result
    except ValueError as e:
        # ValueError per feed non trovato o non abilitato
        raise ErrorCodeException(
            status_code=400,
            error_code=ErrorCode.INVALID_INPUT,
            detail=str(e)
        )
    except Exception as e:
        # Altri errori generici
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error syncing feed {feed_source_id}: {str(e)}", exc_info=True)
        raise ErrorCodeException(
            status_code=500,
            error_code=ErrorCode.INTERNAL_ERROR,
            detail=f"Error syncing feed: {str(e)}"
        )


# Vulnerabilities CRUD
@router.get("")
def list_vulnerabilities(
    cve_id: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    manufacturer: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    search: Optional[str] = Query(None, description="Global search across CVE ID, title, and description"),
    published_from: Optional[str] = Query(None, description="Filter vulnerabilities published from this date (ISO format)"),
    published_to: Optional[str] = Query(None, description="Filter vulnerabilities published until this date (ISO format)"),
    cvss_min: Optional[float] = Query(None, ge=0.0, le=10.0, description="Minimum CVSS score (v3 or v2)"),
    cvss_max: Optional[float] = Query(None, ge=0.0, le=10.0, description="Maximum CVSS score (v3 or v2)"),
    sort_field: Optional[str] = Query(None, description="Field to sort by (cve_id, title, severity, cvss_v3_score, published_date, affected_assets_count)"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc or desc"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("vulnerabilities", 1)),
):
    """List all vulnerabilities with optional filters and affected assets count
    
    Returns: {
        'items': List[Vulnerability],
        'total': int
    }
    """
    result = crud_vulns.get_vulnerabilities(
        db, skip=skip, limit=limit, cve_id=cve_id, severity=severity, 
        manufacturer=manufacturer, source=source, search=search,
        published_from=published_from, published_to=published_to,
        cvss_min=cvss_min, cvss_max=cvss_max,
        sort_field=sort_field, sort_order=sort_order
    )
    return result


@router.get("/stats", response_model=VulnerabilityStats)
def get_vulnerability_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("vulnerabilities", 1)),
):
    """Get vulnerability statistics"""
    from sqlalchemy import func
    from app.models.vulnerability import AssetVulnerability, Vulnerability
    
    # Total vulnerabilities
    total_vulns = db.query(Vulnerability).count()
    
    # By severity
    by_severity = {}
    for severity in ["critical", "high", "medium", "low"]:
        count = db.query(Vulnerability).filter(Vulnerability.severity == severity).count()
        by_severity[severity] = count
    
    # By status (for tenant)
    by_status = {}
    for status in ["unreviewed", "acknowledged", "not_applicable", "mitigated", "patched"]:
        count = db.query(AssetVulnerability).filter(
            AssetVulnerability.tenant_id == current_user.tenant_id,
            AssetVulnerability.status == status
        ).count()
        by_status[status] = count
    
    # Unpatched critical/high (only unreviewed and acknowledged)
    unpatched_critical = db.query(AssetVulnerability).join(
        Vulnerability, AssetVulnerability.vulnerability_id == Vulnerability.id
    ).filter(
        AssetVulnerability.tenant_id == current_user.tenant_id,
        AssetVulnerability.status.in_(["unreviewed", "acknowledged"]),  # Only active vulnerabilities
        Vulnerability.severity == "critical"
    ).count()
    
    unpatched_high = db.query(AssetVulnerability).join(
        Vulnerability, AssetVulnerability.vulnerability_id == Vulnerability.id
    ).filter(
        AssetVulnerability.tenant_id == current_user.tenant_id,
        AssetVulnerability.status.in_(["unreviewed", "acknowledged"]),  # Only active vulnerabilities
        Vulnerability.severity == "high"
    ).count()
    
    # Recent vulnerabilities (last 7 days)
    from datetime import datetime, timedelta
    recent_date = datetime.now() - timedelta(days=7)
    recent_vulns = db.query(Vulnerability).filter(
        Vulnerability.published_date >= recent_date
    ).count()
    
    # By manufacturer (for tenant's affected assets)
    # Count vulnerabilities by manufacturer for assets in this tenant
    by_manufacturer = {}
    try:
        # Get all vulnerabilities that affect assets in this tenant
        vuln_ids = db.query(AssetVulnerability.vulnerability_id).filter(
            AssetVulnerability.tenant_id == current_user.tenant_id
        ).distinct().all()
        vuln_ids_list = [v[0] for v in vuln_ids]
        
        if vuln_ids_list:
            # Get manufacturers from these vulnerabilities
            vulns_with_manufacturers = db.query(Vulnerability.affected_manufacturers).filter(
                Vulnerability.id.in_(vuln_ids_list),
                Vulnerability.affected_manufacturers.isnot(None)
            ).all()
            
            # Count manufacturers
            for manufacturers_list in vulns_with_manufacturers:
                if manufacturers_list:
                    for manufacturer in manufacturers_list:
                        if manufacturer:
                            by_manufacturer[manufacturer] = by_manufacturer.get(manufacturer, 0) + 1
    except Exception as e:
        # If there's an error, just return empty dict
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Error calculating by_manufacturer stats: {str(e)}")
        by_manufacturer = {}
    
    return VulnerabilityStats(
        total_vulnerabilities=total_vulns,
        by_severity=by_severity,
        by_status=by_status,
        by_manufacturer=by_manufacturer,
        unpatched_critical=unpatched_critical,
        unpatched_high=unpatched_high,
        recent_vulnerabilities=recent_vulns
    )


@router.get("/{vulnerability_id}", response_model=VulnerabilityRead)
def get_vulnerability(
    vulnerability_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("vulnerabilities", 1)),
):
    """Get a single vulnerability by ID"""
    vulnerability = crud_vulns.get_vulnerability(db, vulnerability_id)
    if not vulnerability:
        raise ErrorCodeException(
            status_code=404,
            error_code=ErrorCode.ASSET_NOT_FOUND,
            detail="Vulnerability not found"
        )
    return vulnerability


@router.post("", response_model=VulnerabilityRead, status_code=201)
@audit_log_action("create", "Vulnerability")
def create_vulnerability(
    vulnerability: VulnerabilityCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("vulnerabilities", 2)),
):
    """Create a new vulnerability"""
    new_vulnerability = crud_vulns.create_vulnerability(db, vulnerability)
    
    # Auto-match vulnerabilità a tutti gli asset in background
    from app.services.vulnerability_auto_match import VulnerabilityAutoMatcher
    VulnerabilityAutoMatcher.match_vulnerability_async(new_vulnerability.id, None)  # None = all tenants
    
    return new_vulnerability


# Asset Vulnerabilities
@router.get("/assets/{asset_id}", response_model=List[AssetVulnerabilityRead])
def get_asset_vulnerabilities(
    asset_id: uuid.UUID,
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("vulnerabilities", 1)),
):
    """Get all vulnerabilities for an asset"""
    asset_vulns = crud_vulns.get_asset_vulnerabilities(
        db, asset_id, current_user.tenant_id, status
    )
    
    # Convert to dict format for Pydantic v2 serialization
    result = []
    for av in asset_vulns:
        # Convert vulnerability to dict if it's a SQLAlchemy object
        vulnerability_dict = None
        if av.vulnerability:
            vulnerability_dict = VulnerabilityRead.from_orm(av.vulnerability).dict()
        
        av_dict = {
            'id': av.id,
            'tenant_id': av.tenant_id,
            'asset_id': av.asset_id,
            'vulnerability_id': av.vulnerability_id,
            'match_confidence': av.match_confidence,
            'match_reason': av.match_reason,
            'status': av.status,
            'mitigation_notes': av.mitigation_notes,
            'risk_impact': av.risk_impact,
            'patched_date': av.patched_date,
            'patched_by': av.patched_by,
            'detected_at': av.detected_at,
            'updated_at': av.updated_at,
            'vulnerability': vulnerability_dict,
            'asset': {
                'id': str(av.asset.id) if av.asset else None,
                'name': av.asset.name if av.asset else None,
                'tag': av.asset.tag if av.asset else None
            } if av.asset else None
        }
        result.append(av_dict)
    
    return result


@router.get("/{vulnerability_id}/assets", response_model=List[AssetVulnerabilityRead])
def get_vulnerability_affected_assets(
    vulnerability_id: uuid.UUID,
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("vulnerabilities", 1)),
):
    """Get all assets affected by a vulnerability"""
    from sqlalchemy.orm import joinedload
    
    asset_vulns = (
        db.query(AssetVulnerability)
        .options(joinedload(AssetVulnerability.asset))
        .join(Asset, AssetVulnerability.asset_id == Asset.id)
        .filter(
            AssetVulnerability.vulnerability_id == vulnerability_id,
            AssetVulnerability.tenant_id == current_user.tenant_id,
            Asset.deleted_at.is_(None)
        )
    )
    
    if status:
        asset_vulns = asset_vulns.filter(AssetVulnerability.status == status)
    
    results = asset_vulns.all()
    
    # Manually construct response with asset info
    response = []
    for av in results:
        av_dict = {
            'id': av.id,
            'tenant_id': av.tenant_id,
            'asset_id': av.asset_id,
            'vulnerability_id': av.vulnerability_id,
            'match_confidence': av.match_confidence,
            'match_reason': av.match_reason,
            'status': av.status,
            'mitigation_notes': av.mitigation_notes,
            'risk_impact': av.risk_impact,
            'patched_date': av.patched_date,
            'patched_by': av.patched_by,
            'detected_at': av.detected_at,
            'updated_at': av.updated_at,
            'asset': {
                'id': str(av.asset.id),
                'name': av.asset.name,
                'tag': av.asset.tag
            } if av.asset else None
        }
        response.append(av_dict)
    
    return response


@router.post("/assets/{asset_id}", response_model=AssetVulnerabilityRead, status_code=201)
@audit_log_action("create", "AssetVulnerability")
def create_asset_vulnerability(
    asset_id: uuid.UUID,
    asset_vulnerability: AssetVulnerabilityCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("vulnerabilities", 2)),
):
    """Create a new asset-vulnerability link"""
    try:
        return crud_vulns.create_asset_vulnerability(
            db, asset_vulnerability, asset_id, current_user.tenant_id
        )
    except ValueError as e:
        raise ErrorCodeException(
            status_code=400,
            error_code=ErrorCode.INVALID_INPUT,
            detail=str(e)
        )


@router.put("/assets/{asset_id}/vulnerabilities/{asset_vulnerability_id}", response_model=AssetVulnerabilityRead)
def update_asset_vulnerability(
    asset_id: uuid.UUID,
    asset_vulnerability_id: uuid.UUID,
    asset_vulnerability_update: AssetVulnerabilityUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("vulnerabilities", 2)),
):
    """Update an asset-vulnerability status"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Updating asset vulnerability {asset_vulnerability_id} for asset {asset_id} by user {current_user.id}")
        
        # Get old status before update to detect changes
        old_asset_vuln = db.query(AssetVulnerability).filter(
            AssetVulnerability.id == asset_vulnerability_id,
            AssetVulnerability.tenant_id == current_user.tenant_id
        ).first()
        old_status = old_asset_vuln.status if old_asset_vuln else None
        
        asset_vuln = crud_vulns.update_asset_vulnerability(
            db, asset_vulnerability_id, current_user.tenant_id, asset_vulnerability_update
        )
        if not asset_vuln:
            logger.warning(f"Asset vulnerability {asset_vulnerability_id} not found for tenant {current_user.tenant_id}")
            raise ErrorCodeException(
                status_code=404,
                error_code=ErrorCode.ASSET_NOT_FOUND,
                detail="Asset vulnerability not found"
            )
        
        # Check if status changed (and if it's a status that affects risk calculation)
        status_changed = (
            asset_vulnerability_update.status and 
            asset_vulnerability_update.status != old_status
        )
        
        # Update impact if status changed
        if asset_vulnerability_update.status:
            try:
                logger.debug(f"Updating risk impact for asset vulnerability {asset_vulnerability_id}")
                VulnerabilityImpactCalculator.update_asset_vulnerability_impact(
                    db, asset_vulnerability_id, current_user.tenant_id
                )
            except Exception as impact_error:
                logger.error(f"Error updating risk impact for asset vulnerability {asset_vulnerability_id}: {impact_error}", exc_info=True)
                # Non bloccare l'update se il calcolo dell'impatto fallisce
        
        # Recalculate asset risk score if status changed (status changes affect which vulnerabilities are considered)
        if status_changed:
            try:
                from app.services.risk_scoring import CompositeRiskScoringEngine
                from datetime import datetime
                
                # Get the asset (Asset is already imported at the top of the file)
                asset = db.query(Asset).filter(
                    Asset.id == asset_id,
                    Asset.tenant_id == current_user.tenant_id
                ).first()
                
                if asset:
                    logger.info(f"Recalculating risk score for asset {asset_id} after vulnerability status change from '{old_status}' to '{asset_vulnerability_update.status}'")
                    
                    # Store old risk score
                    old_risk_score = asset.risk_score
                    
                    # Recalculate risk
                    risk_engine = CompositeRiskScoringEngine()
                    breakdown = risk_engine.calculate(asset, db=db)
                    new_risk_score = breakdown["final_score"]
                    
                    # Update asset risk score if calculated
                    if new_risk_score is not None:
                        asset.risk_score = new_risk_score
                        asset.last_risk_assessment = datetime.utcnow()
                        db.commit()
                        
                        logger.info(
                            f"Asset {asset_id} risk score recalculated: {old_risk_score} -> {new_risk_score} "
                            f"(vulnerability status changed from '{old_status}' to '{asset_vulnerability_update.status}')"
                        )
                        
                        # Optionally send notification if risk changed significantly
                        if old_risk_score is not None and abs(new_risk_score - old_risk_score) >= 1.0:
                            try:
                                from app.services.notification_service import NotificationService
                                risk_level = "high" if new_risk_score >= 7 else ("medium" if new_risk_score >= 4 else "low")
                                NotificationService.send_risk_alert(db, asset_id, new_risk_score, risk_level)
                            except Exception as notify_error:
                                logger.warning(f"Failed to send risk notification for asset {asset_id}: {notify_error}")
                    else:
                        logger.warning(f"Could not calculate risk score for asset {asset_id}")
                else:
                    logger.warning(f"Asset {asset_id} not found for risk recalculation")
            except Exception as risk_error:
                logger.error(f"Error recalculating risk score for asset {asset_id} after vulnerability status change: {risk_error}", exc_info=True)
                # Non bloccare l'update se il ricalcolo del rischio fallisce
        
        # Refresh per assicurarsi di avere i dati aggiornati
        db.refresh(asset_vuln)
        
        # Convert to response format
        from sqlalchemy.orm import joinedload
        asset_vuln_with_relations = db.query(AssetVulnerability).options(
            joinedload(AssetVulnerability.vulnerability),
            joinedload(AssetVulnerability.asset)
        ).filter(AssetVulnerability.id == asset_vulnerability_id).first()
        
        if not asset_vuln_with_relations:
            raise ErrorCodeException(
                status_code=404,
                error_code=ErrorCode.ASSET_NOT_FOUND,
                detail="Asset vulnerability not found after update"
            )
        
        # Build response dict manually to ensure proper serialization
        vulnerability_dict = None
        if asset_vuln_with_relations.vulnerability:
            vuln = asset_vuln_with_relations.vulnerability
            vulnerability_dict = {
                'id': str(vuln.id),
                'cve_id': vuln.cve_id,
                'advisory_id': vuln.advisory_id,
                'title': vuln.title,
                'description': vuln.description,
                'cvss_v3_score': vuln.cvss_v3_score,
                'cvss_v3_vector': vuln.cvss_v3_vector,
                'cvss_v2_score': vuln.cvss_v2_score,
                'cvss_v2_vector': vuln.cvss_v2_vector,
                'severity': vuln.severity,
                'affected_manufacturers': vuln.affected_manufacturers,
                'affected_products': vuln.affected_products,
                'affected_versions': vuln.affected_versions,
                'published_date': vuln.published_date.isoformat() if vuln.published_date else None,
                'modified_date': vuln.modified_date.isoformat() if vuln.modified_date else None,
                'references': vuln.references,
                'vendor_advisory_url': vuln.vendor_advisory_url,
                'patch_url': vuln.patch_url,
                'source': vuln.source,
                'source_url': vuln.source_url,
                'created_at': vuln.created_at.isoformat() if vuln.created_at else None,
                'updated_at': vuln.updated_at.isoformat() if vuln.updated_at else None
            }
        
        response_dict = {
            'id': asset_vuln_with_relations.id,
            'tenant_id': asset_vuln_with_relations.tenant_id,
            'asset_id': asset_vuln_with_relations.asset_id,
            'vulnerability_id': asset_vuln_with_relations.vulnerability_id,
            'match_confidence': asset_vuln_with_relations.match_confidence,
            'match_reason': asset_vuln_with_relations.match_reason,
            'status': asset_vuln_with_relations.status,
            'mitigation_notes': asset_vuln_with_relations.mitigation_notes,
            'risk_impact': asset_vuln_with_relations.risk_impact,
            'patched_date': asset_vuln_with_relations.patched_date.isoformat() if asset_vuln_with_relations.patched_date else None,
            'patched_by': asset_vuln_with_relations.patched_by,
            'detected_at': asset_vuln_with_relations.detected_at.isoformat() if asset_vuln_with_relations.detected_at else None,
            'updated_at': asset_vuln_with_relations.updated_at.isoformat() if asset_vuln_with_relations.updated_at else None,
            'vulnerability': vulnerability_dict,
            'asset': {
                'id': str(asset_vuln_with_relations.asset.id) if asset_vuln_with_relations.asset else None,
                'name': asset_vuln_with_relations.asset.name if asset_vuln_with_relations.asset else None,
                'tag': asset_vuln_with_relations.asset.tag if asset_vuln_with_relations.asset else None
            } if asset_vuln_with_relations.asset else None
        }
        
        # Create audit log manually
        try:
            from app.services.audit_log import create_audit_log, resolve_audit_language
            create_audit_log(
                db=db,
                user_id=current_user.id,
                tenant_id=current_user.tenant_id,
                action="update_vulnerability_status",
                entity="AssetVulnerability",
                entity_id=asset_vulnerability_id,
                commit=True,
                language=resolve_audit_language(current_user, request),
                status=asset_vuln_with_relations.status,
            )
        except Exception as audit_error:
            logger.warning(f"Failed to create audit log: {audit_error}")
        
        logger.info(f"Successfully updated asset vulnerability {asset_vulnerability_id}")
        return response_dict
        
    except ErrorCodeException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating asset vulnerability {asset_vulnerability_id}: {e}", exc_info=True)
        raise ErrorCodeException(
            status_code=500,
            error_code=ErrorCode.INTERNAL_ERROR,
            detail=f"Error updating asset vulnerability: {str(e)}"
        )


@router.delete("/assets/{asset_id}/vulnerabilities/{asset_vulnerability_id}", status_code=204)
@audit_log_action("delete", "AssetVulnerability")
def delete_asset_vulnerability(
    asset_id: uuid.UUID,
    asset_vulnerability_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("vulnerabilities", 3)),
):
    """Delete an asset-vulnerability link"""
    success = crud_vulns.delete_asset_vulnerability(
        db, asset_vulnerability_id, current_user.tenant_id
    )
    if not success:
        raise ErrorCodeException(
            status_code=404,
            error_code=ErrorCode.ASSET_NOT_FOUND,
            detail="Asset vulnerability not found"
        )


# Matching
@router.post("/{vulnerability_id}/match-assets")
def match_vulnerability_to_assets(
    vulnerability_id: uuid.UUID,
    min_confidence: float = Query(0.6, ge=0.0, le=1.0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("vulnerabilities", 2)),
):
    """Match a vulnerability to assets automatically"""
    matches = VulnerabilityMatcher.match_vulnerability_to_assets(
        db, vulnerability_id, current_user.tenant_id, min_confidence
    )
    return {
        "matched_count": len(matches),
        "matches": [{"asset_id": str(m.asset_id), "confidence": m.match_confidence} for m in matches]
    }


@router.post("/assets/{asset_id}/match-vulnerabilities")
def match_asset_to_vulnerabilities(
    asset_id: uuid.UUID,
    min_confidence: float = Query(0.6, ge=0.0, le=1.0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("vulnerabilities", 2)),
):
    """Match an asset to vulnerabilities automatically"""
    matches = VulnerabilityMatcher.match_asset_to_vulnerabilities(
        db, asset_id, current_user.tenant_id, min_confidence
    )
    return {
        "matched_count": len(matches),
        "matches": [{"vulnerability_id": str(m.vulnerability_id), "confidence": m.match_confidence} for m in matches]
    }


# Feed Sources - Update/Delete endpoints
@router.put("/feeds/{feed_source_id}", response_model=VulnerabilityFeedSourceRead)
@audit_log_action("update", "VulnerabilityFeedSource")
def update_vulnerability_feed(
    feed_source_id: uuid.UUID,
    feed_source_update: VulnerabilityFeedSourceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("vulnerabilities", 2)),
):
    """Update a vulnerability feed source"""
    feed_source = crud_vulns.update_vulnerability_feed_source(
        db, feed_source_id, current_user.tenant_id, feed_source_update
    )
    if not feed_source:
        raise ErrorCodeException(
            status_code=404,
            error_code=ErrorCode.ASSET_NOT_FOUND,
            detail="Feed source not found"
        )
    return feed_source


@router.delete("/feeds/{feed_source_id}", status_code=204)
@audit_log_action("delete", "VulnerabilityFeedSource")
def delete_vulnerability_feed(
    feed_source_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("vulnerabilities", 3)),
):
    """Delete a vulnerability feed source"""
    success = crud_vulns.delete_vulnerability_feed_source(
        db, feed_source_id, current_user.tenant_id
    )
    if not success:
        raise ErrorCodeException(
            status_code=404,
            error_code=ErrorCode.ASSET_NOT_FOUND,
            detail="Feed source not found"
        )

