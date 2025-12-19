import math
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models import User, Asset, AssetStatus
from app.services.audit_decorator import audit_log_action
from app.services.auth import get_current_user
from app.services.audit_log import create_audit_log

def clean_float_values(data):
    """Clean float values to prevent JSON serialization errors"""
    if isinstance(data, dict):
        return {k: clean_float_values(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_float_values(item) for item in data]
    elif isinstance(data, float):
        if math.isnan(data) or math.isinf(data):
            return None
        return data
    else:
        return data

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
)


# Dashboard endpoints
@router.get("/stats")
def get_dashboard_stats(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Ottimizzato con caching e query unificate"""
    from app.services.dashboard_cache import get_dashboard_stats_cached
    
    # Usa il servizio di cache per le statistiche
    return get_dashboard_stats_cached(str(current_user.tenant_id), db)


@router.get("/risky-assets")
def get_risky_assets(
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db),
    limit: int = 10
):
    """
    Ottieni gli asset più a rischio
    PERFORMANCE: Usa selectinload per evitare N+1 queries
    """
    from sqlalchemy import and_
    from sqlalchemy.orm import selectinload
    
    from app.models import AssetType, Site, Manufacturer
    
    # PERFORMANCE: Limita il numero massimo di risultati
    limit = min(limit, 50)
    
    risky_assets = (
        db.query(Asset)
        .options(
            selectinload(Asset.interfaces),  # Query separate ottimizzata
            selectinload(Asset.asset_type),
            selectinload(Asset.site),
            selectinload(Asset.status),
            selectinload(Asset.manufacturer)
        )
        .filter(
            and_(
                Asset.tenant_id == current_user.tenant_id,
                Asset.deleted_at == None,  # Non mostrare asset eliminati
                Asset.risk_score >= 5
            )
        )
        .order_by(Asset.risk_score.desc())
        .limit(limit)
        .all()
    )
    
    return [
        {
            "id": str(asset.id),
            "name": asset.name,
            "risk_score": clean_float_values(asset.risk_score),
            "business_criticality": asset.business_criticality,
            "asset_type_name": asset.asset_type.name if asset.asset_type else "N/A",
            "status_name": asset.status.name if asset.status else "N/A",
            "site_name": asset.site.name if asset.site else "N/A",
            "manufacturer_name": asset.manufacturer.name if asset.manufacturer else "N/A",
            "ip_address": asset.interfaces[0].ip_address if asset.interfaces else None,
            "created_at": asset.created_at.isoformat() if asset.created_at else None,
            "updated_at": asset.updated_at.isoformat() if asset.updated_at else None
        }
        for asset in risky_assets
    ]


@router.get("/reviews-summary")
def get_reviews_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get summary statistics for asset reviews"""
    from app.services.asset_review_service import AssetReviewService
    from datetime import datetime, timedelta
    from app.models import Tenant
    
    overdue = AssetReviewService.get_overdue_assets(db, current_user.tenant_id)
    
    # Get due assets (excluding overdue - they're already counted)
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    days_ahead = tenant.review_due_days_ahead if tenant and tenant.review_due_days_ahead else 30
    
    today = datetime.utcnow()
    future_date = today + timedelta(days=days_ahead)
    
    # Get assets due in future (not overdue)
    from app.models import Asset
    from sqlalchemy import and_
    
    due_assets = (
        db.query(Asset)
        .filter(
            and_(
                Asset.tenant_id == current_user.tenant_id,
                Asset.deleted_at.is_(None),
                Asset.next_review_date.isnot(None),
                Asset.next_review_date >= today,
                Asset.next_review_date <= future_date,
                Asset.review_status.in_(['pending', None])
            )
        )
        .all()
    )
    
    return {
        "overdue_count": len(overdue),
        "due_count": len(due_assets),  # Only future due, not overdue
        "overdue_assets": [
            {
                "id": str(asset.id),
                "name": asset.name,
                "next_review_date": asset.next_review_date.isoformat() if asset.next_review_date else None,
                "review_status": asset.review_status
            }
            for asset in overdue[:5]  # Top 5
        ],
        "due_assets": [
            {
                "id": str(asset.id),
                "name": asset.name,
                "next_review_date": asset.next_review_date.isoformat() if asset.next_review_date else None,
                "review_status": asset.review_status
            }
            for asset in due_assets[:5]  # Top 5
        ]
    }


@router.get("/dependencies-summary")
def get_dependencies_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get summary statistics for asset dependencies"""
    from app.models.asset_connection import AssetConnection
    from app.services.connection_dependency_analyzer import ConnectionDependencyAnalyzer
    from sqlalchemy import and_
    
    # Get all connections for tenant (filter directly by tenant_id)
    connections = (
        db.query(AssetConnection)
        .filter(AssetConnection.tenant_id == current_user.tenant_id)
        .all()
    )
    
    missing_count = 0
    critical_missing = 0
    
    for conn in connections:
        status = ConnectionDependencyAnalyzer.get_connection_dependency_status(db, conn)
        if status.get('status') == 'missing':
            missing_count += 1
            if status.get('severity') == 'critical':
                critical_missing += 1
    
    return {
        "total_connections": len(connections),
        "missing_dependencies_count": missing_count,
        "critical_missing_count": critical_missing
    }


@router.get("/vulnerabilities-summary")
def get_vulnerabilities_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get summary statistics for vulnerabilities"""
    from app.models.vulnerability import AssetVulnerability, Vulnerability
    from sqlalchemy import func, and_
    
    # Critical unpatched vulnerabilities
    critical_unpatched = (
        db.query(func.count(AssetVulnerability.id))
        .join(Vulnerability, AssetVulnerability.vulnerability_id == Vulnerability.id)
        .filter(
            and_(
                AssetVulnerability.tenant_id == current_user.tenant_id,
                or_(
                    AssetVulnerability.status == "unreviewed",
                    AssetVulnerability.status == "acknowledged"
                ),  # Include both unreviewed and acknowledged
                Vulnerability.severity == "critical"
            )
        )
        .scalar()
    ) or 0
    
    # High unpatched vulnerabilities
    high_unpatched = (
        db.query(func.count(AssetVulnerability.id))
        .join(Vulnerability, AssetVulnerability.vulnerability_id == Vulnerability.id)
        .filter(
            and_(
                AssetVulnerability.tenant_id == current_user.tenant_id,
                or_(
                    AssetVulnerability.status == "unreviewed",
                    AssetVulnerability.status == "acknowledged"
                ),  # Include both unreviewed and acknowledged
                Vulnerability.severity == "high"
            )
        )
        .scalar()
    ) or 0
    
    # Total unpatched
    total_unpatched = (
        db.query(func.count(AssetVulnerability.id))
        .filter(
            and_(
                AssetVulnerability.tenant_id == current_user.tenant_id,
                AssetVulnerability.status == "unpatched"
            )
        )
        .scalar()
    ) or 0
    
    return {
        "critical_unpatched": critical_unpatched,
        "high_unpatched": high_unpatched,
        "total_unpatched": total_unpatched
    }


@router.get("/compliance-summary")
def get_compliance_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get summary statistics for ISA/IEC 62443 compliance"""
    from app.models import SecurityZone, SecurityRequirementCompliance
    from sqlalchemy import func, and_, case
    
    # Total zones
    total_zones = (
        db.query(SecurityZone)
        .filter(SecurityZone.tenant_id == current_user.tenant_id)
        .count()
    )
    
    if total_zones == 0:
        return {
            "total_zones": 0,
            "non_compliant_zones": 0,
            "partial_compliant_zones": 0,
            "compliant_zones": 0
        }
    
    # Get all zones for tenant
    zones = (
        db.query(SecurityZone)
        .filter(SecurityZone.tenant_id == current_user.tenant_id)
        .all()
    )
    
    non_compliant_zones = set()
    partial_zones = set()
    compliant_zones = set()
    
    # For each zone, check its compliance records
    for zone in zones:
        # Get all compliance records for this zone
        compliance_records = (
            db.query(SecurityRequirementCompliance)
            .filter(
                and_(
                    SecurityRequirementCompliance.tenant_id == current_user.tenant_id,
                    SecurityRequirementCompliance.zone_id == zone.id
                )
            )
            .all()
        )
        
        if not compliance_records:
            # No compliance records = not assessed
            continue
        
        # Check if zone has any non_compliant records
        has_non_compliant = any(r.compliance_status == "non_compliant" for r in compliance_records)
        has_partial = any(r.compliance_status == "partial" for r in compliance_records)
        all_compliant = all(r.compliance_status == "compliant" for r in compliance_records)
        
        if has_non_compliant:
            non_compliant_zones.add(zone.id)
        elif has_partial and not has_non_compliant:
            partial_zones.add(zone.id)
        elif all_compliant:
            compliant_zones.add(zone.id)
    
    return {
        "total_zones": total_zones,
        "non_compliant_zones": len(non_compliant_zones),
        "partial_compliant_zones": len(partial_zones),
        "compliant_zones": len(compliant_zones)
    }
