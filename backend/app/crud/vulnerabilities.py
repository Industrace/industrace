# backend/app/crud/vulnerabilities.py
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, cast
from sqlalchemy.dialects.postgresql import JSONB
import sqlalchemy as sa
import uuid
from app.models.vulnerability import Vulnerability, AssetVulnerability, VulnerabilityFeedSource
from app.models.asset import Asset
from app.schemas.vulnerability import (
    VulnerabilityCreate,
    VulnerabilityUpdate,
    AssetVulnerabilityCreate,
    AssetVulnerabilityUpdate,
    VulnerabilityFeedSourceCreate,
    VulnerabilityFeedSourceUpdate
)


def get_vulnerability(
    db: Session,
    vulnerability_id: uuid.UUID
) -> Optional[Vulnerability]:
    """Get a single vulnerability by ID"""
    return db.query(Vulnerability).filter(Vulnerability.id == vulnerability_id).first()


def get_vulnerability_by_cve(
    db: Session,
    cve_id: str
) -> Optional[Vulnerability]:
    """Get a vulnerability by CVE ID"""
    return db.query(Vulnerability).filter(Vulnerability.cve_id == cve_id).first()


def get_vulnerabilities(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    cve_id: Optional[str] = None,
    severity: Optional[str] = None,
    manufacturer: Optional[str] = None,
    source: Optional[str] = None,
    search: Optional[str] = None,
    published_from: Optional[str] = None,
    published_to: Optional[str] = None,
    cvss_min: Optional[float] = None,
    cvss_max: Optional[float] = None,
    sort_field: Optional[str] = None,
    sort_order: Optional[str] = "desc"
) -> Dict[str, Any]:
    """Get list of vulnerabilities with optional filters and affected assets count
    
    Returns a dict with 'items' (list of vulnerabilities) and 'total' (total count)
    """
    # Base query for filtering and counting
    base_query = db.query(Vulnerability)
    
    if cve_id:
        base_query = base_query.filter(Vulnerability.cve_id.ilike(f"%{cve_id}%"))
    
    if severity:
        # Support multiple severity values separated by comma (e.g., "critical,high")
        severity_values = [v.strip().lower() for v in severity.split(',') if v.strip()]
        if severity_values:
            base_query = base_query.filter(Vulnerability.severity.in_(severity_values))
    
    if manufacturer:
        # JSONB array contains check - search if array contains the manufacturer name (case-insensitive)
        # affected_manufacturers is a JSONB array like ["Siemens", "Schneider Electric"]
        # Use JSONB @> operator with case-insensitive text search
        # Convert manufacturer to lowercase for case-insensitive matching
        manufacturer_lower = manufacturer.lower()
        # Check if any element in the JSONB array contains the manufacturer (case-insensitive)
        # Using text-based search on the string representation of the JSONB array
        base_query = base_query.filter(
            func.lower(
                func.cast(Vulnerability.affected_manufacturers, sa.String)
            ).contains(manufacturer_lower)
        )
    
    if source:
        base_query = base_query.filter(Vulnerability.source == source)
    
    # Date filters
    if published_from:
        from datetime import datetime
        try:
            # Try ISO format first (with time)
            try:
                published_from_date = datetime.fromisoformat(published_from.replace('Z', '+00:00'))
            except ValueError:
                # Fall back to date-only format (YYYY-MM-DD)
                published_from_date = datetime.strptime(published_from, '%Y-%m-%d')
            base_query = base_query.filter(Vulnerability.published_date >= published_from_date)
        except (ValueError, AttributeError):
            pass  # Ignore invalid date format
    
    if published_to:
        from datetime import datetime
        try:
            # Try ISO format first (with time)
            try:
                published_to_date = datetime.fromisoformat(published_to.replace('Z', '+00:00'))
            except ValueError:
                # Fall back to date-only format (YYYY-MM-DD)
                published_to_date = datetime.strptime(published_to, '%Y-%m-%d')
            # For published_to, we want to include the entire day, so set time to end of day
            if published_to_date.hour == 0 and published_to_date.minute == 0 and published_to_date.second == 0:
                from datetime import timedelta
                published_to_date = published_to_date + timedelta(days=1) - timedelta(seconds=1)
            base_query = base_query.filter(Vulnerability.published_date <= published_to_date)
        except (ValueError, AttributeError):
            pass  # Ignore invalid date format
    
    # CVSS score filters
    if cvss_min is not None:
        # Use cvss_v3_score if available, otherwise cvss_v2_score
        base_query = base_query.filter(
            or_(
                Vulnerability.cvss_v3_score >= cvss_min,
                and_(
                    Vulnerability.cvss_v3_score.is_(None),
                    Vulnerability.cvss_v2_score >= cvss_min
                )
            )
        )
    
    if cvss_max is not None:
        # Use cvss_v3_score if available, otherwise cvss_v2_score
        base_query = base_query.filter(
            or_(
                Vulnerability.cvss_v3_score <= cvss_max,
                and_(
                    Vulnerability.cvss_v3_score.is_(None),
                    Vulnerability.cvss_v2_score <= cvss_max
                )
            )
        )
    
    # Global search across CVE ID, title, and description
    if search:
        search_filter = or_(
            Vulnerability.cve_id.ilike(f"%{search}%"),
            Vulnerability.title.ilike(f"%{search}%"),
            Vulnerability.description.ilike(f"%{search}%")
        )
        base_query = base_query.filter(search_filter)
    
    # Get total count
    total = base_query.count()
    
    # Get vulnerabilities with affected assets count
    query = db.query(
        Vulnerability,
        func.count(AssetVulnerability.id).label('affected_assets_count')
    ).outerjoin(
        AssetVulnerability, Vulnerability.id == AssetVulnerability.vulnerability_id
    )
    
    # Apply same filters
    if cve_id:
        query = query.filter(Vulnerability.cve_id.ilike(f"%{cve_id}%"))
    
    if severity:
        # Support multiple severity values separated by comma (e.g., "critical,high")
        severity_values = [v.strip().lower() for v in severity.split(',') if v.strip()]
        if severity_values:
            query = query.filter(Vulnerability.severity.in_(severity_values))
    
    if manufacturer:
        # JSONB contains check - search if array contains the manufacturer name (case-insensitive)
        # Convert JSONB array to text and search case-insensitively
        # affected_manufacturers is a JSONB array like ["Siemens", "Schneider Electric"]
        manufacturer_lower = manufacturer.lower()
        query = query.filter(
            func.lower(
                func.cast(Vulnerability.affected_manufacturers, sa.String)
            ).contains(manufacturer_lower)
        )
    
    if source:
        query = query.filter(Vulnerability.source == source)
    
    # Date filters
    if published_from:
        from datetime import datetime
        try:
            # Try ISO format first (with time)
            try:
                published_from_date = datetime.fromisoformat(published_from.replace('Z', '+00:00'))
            except ValueError:
                # Fall back to date-only format (YYYY-MM-DD)
                published_from_date = datetime.strptime(published_from, '%Y-%m-%d')
            query = query.filter(Vulnerability.published_date >= published_from_date)
        except (ValueError, AttributeError):
            pass  # Ignore invalid date format
    
    if published_to:
        from datetime import datetime
        try:
            # Try ISO format first (with time)
            try:
                published_to_date = datetime.fromisoformat(published_to.replace('Z', '+00:00'))
            except ValueError:
                # Fall back to date-only format (YYYY-MM-DD)
                published_to_date = datetime.strptime(published_to, '%Y-%m-%d')
            # For published_to, we want to include the entire day, so set time to end of day
            if published_to_date.hour == 0 and published_to_date.minute == 0 and published_to_date.second == 0:
                from datetime import timedelta
                published_to_date = published_to_date + timedelta(days=1) - timedelta(seconds=1)
            query = query.filter(Vulnerability.published_date <= published_to_date)
        except (ValueError, AttributeError):
            pass  # Ignore invalid date format
    
    # CVSS score filters
    if cvss_min is not None:
        # Use cvss_v3_score if available, otherwise cvss_v2_score
        query = query.filter(
            or_(
                Vulnerability.cvss_v3_score >= cvss_min,
                and_(
                    Vulnerability.cvss_v3_score.is_(None),
                    Vulnerability.cvss_v2_score >= cvss_min
                )
            )
        )
    
    if cvss_max is not None:
        # Use cvss_v3_score if available, otherwise cvss_v2_score
        query = query.filter(
            or_(
                Vulnerability.cvss_v3_score <= cvss_max,
                and_(
                    Vulnerability.cvss_v3_score.is_(None),
                    Vulnerability.cvss_v2_score <= cvss_max
                )
            )
        )
    
    # Global search across CVE ID, title, and description
    if search:
        search_filter = or_(
            Vulnerability.cve_id.ilike(f"%{search}%"),
            Vulnerability.title.ilike(f"%{search}%"),
            Vulnerability.description.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    # Apply sorting
    from sqlalchemy import desc, asc
    order_by_clause = None
    
    if sort_field:
        # Map frontend field names to model attributes
        # Special handling for affected_assets_count (must be in GROUP BY)
        if sort_field == 'affected_assets_count':
            count_expr = func.count(AssetVulnerability.id)
            if sort_order and sort_order.lower() == 'asc':
                order_by_clause = asc(count_expr)
            else:
                order_by_clause = desc(count_expr)
        else:
            field_mapping = {
                'cve_id': Vulnerability.cve_id,
                'title': Vulnerability.title,
                'severity': Vulnerability.severity,
                'cvss_v3_score': Vulnerability.cvss_v3_score,
                'published_date': Vulnerability.published_date
            }
            
            if sort_field in field_mapping:
                sort_column = field_mapping[sort_field]
                if sort_order and sort_order.lower() == 'asc':
                    order_by_clause = asc(sort_column)
                else:
                    order_by_clause = desc(sort_column)
    
    # Default ordering by published_date desc if no sort specified
    if order_by_clause is None:
        order_by_clause = desc(Vulnerability.published_date)
    
    query = query.group_by(Vulnerability.id).order_by(order_by_clause).offset(skip).limit(limit)
    
    results = query.all()
    
    # Convert to dict format with affected_assets_count
    from datetime import datetime
    vulnerabilities = []
    for vuln, count in results:
        # Convert datetime objects to ISO strings for JSON serialization
        published_date_str = vuln.published_date.isoformat() if vuln.published_date else None
        modified_date_str = vuln.modified_date.isoformat() if vuln.modified_date else None
        created_at_str = vuln.created_at.isoformat() if vuln.created_at else None
        updated_at_str = vuln.updated_at.isoformat() if vuln.updated_at else None
        
        vuln_dict = {
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
            'published_date': published_date_str,
            'modified_date': modified_date_str,
            'references': vuln.references,
            'vendor_advisory_url': vuln.vendor_advisory_url,
            'patch_url': vuln.patch_url,
            'source': vuln.source,
            'source_url': vuln.source_url,
            'created_at': created_at_str,
            'updated_at': updated_at_str,
            'affected_assets_count': int(count) if count else 0
        }
        vulnerabilities.append(vuln_dict)
    
    return {
        'items': vulnerabilities,
        'total': total
    }


def create_vulnerability(
    db: Session,
    vulnerability: VulnerabilityCreate
) -> Vulnerability:
    """Create a new vulnerability"""
    db_vulnerability = Vulnerability(**vulnerability.dict())
    db.add(db_vulnerability)
    db.commit()
    db.refresh(db_vulnerability)
    return db_vulnerability


def update_vulnerability(
    db: Session,
    vulnerability_id: uuid.UUID,
    vulnerability_update: VulnerabilityUpdate
) -> Optional[Vulnerability]:
    """Update an existing vulnerability"""
    db_vulnerability = get_vulnerability(db, vulnerability_id)
    if not db_vulnerability:
        return None
    
    update_data = vulnerability_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_vulnerability, field, value)
    
    db.commit()
    db.refresh(db_vulnerability)
    return db_vulnerability


def get_asset_vulnerabilities(
    db: Session,
    asset_id: uuid.UUID,
    tenant_id: uuid.UUID,
    status: Optional[str] = None
) -> List[AssetVulnerability]:
    """Get all vulnerabilities for an asset"""
    from sqlalchemy.orm import joinedload
    
    query = db.query(AssetVulnerability).options(
        joinedload(AssetVulnerability.vulnerability),
        joinedload(AssetVulnerability.asset)
    ).filter(
        AssetVulnerability.asset_id == asset_id,
        AssetVulnerability.tenant_id == tenant_id
    )
    
    if status:
        query = query.filter(AssetVulnerability.status == status)
    
    return query.all()


def get_vulnerability_affected_assets(
    db: Session,
    vulnerability_id: uuid.UUID,
    tenant_id: uuid.UUID,
    status: Optional[str] = None
) -> List[AssetVulnerability]:
    """Get all assets affected by a vulnerability"""
    query = (
        db.query(AssetVulnerability)
        .join(Asset, AssetVulnerability.asset_id == Asset.id)
        .filter(
            AssetVulnerability.vulnerability_id == vulnerability_id,
            AssetVulnerability.tenant_id == tenant_id,
            Asset.deleted_at.is_(None)
        )
    )
    
    if status:
        query = query.filter(AssetVulnerability.status == status)
    
    return query.all()


def create_asset_vulnerability(
    db: Session,
    asset_vulnerability: AssetVulnerabilityCreate,
    asset_id: uuid.UUID,
    tenant_id: uuid.UUID
) -> AssetVulnerability:
    """Create a new asset-vulnerability link"""
    # Check if already exists
    existing = db.query(AssetVulnerability).filter(
        AssetVulnerability.asset_id == asset_id,
        AssetVulnerability.vulnerability_id == asset_vulnerability.vulnerability_id,
        AssetVulnerability.tenant_id == tenant_id
    ).first()
    
    if existing:
        raise ValueError("Asset vulnerability already exists")
    
    db_asset_vuln = AssetVulnerability(
        **asset_vulnerability.dict(),
        asset_id=asset_id,
        tenant_id=tenant_id
    )
    db.add(db_asset_vuln)
    db.commit()
    db.refresh(db_asset_vuln)
    return db_asset_vuln


def update_asset_vulnerability(
    db: Session,
    asset_vulnerability_id: uuid.UUID,
    tenant_id: uuid.UUID,
    asset_vulnerability_update: AssetVulnerabilityUpdate
) -> Optional[AssetVulnerability]:
    """Update an existing asset-vulnerability"""
    db_asset_vuln = db.query(AssetVulnerability).filter(
        AssetVulnerability.id == asset_vulnerability_id,
        AssetVulnerability.tenant_id == tenant_id
    ).first()
    
    if not db_asset_vuln:
        return None
    
    update_data = asset_vulnerability_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_asset_vuln, field, value)
    
    db.commit()
    db.refresh(db_asset_vuln)
    return db_asset_vuln


def delete_asset_vulnerability(
    db: Session,
    asset_vulnerability_id: uuid.UUID,
    tenant_id: uuid.UUID
) -> bool:
    """Delete an asset-vulnerability link"""
    db_asset_vuln = db.query(AssetVulnerability).filter(
        AssetVulnerability.id == asset_vulnerability_id,
        AssetVulnerability.tenant_id == tenant_id
    ).first()
    
    if not db_asset_vuln:
        return False
    
    db.delete(db_asset_vuln)
    db.commit()
    return True


def get_unpatched_vulnerabilities(
    db: Session,
    asset_id: uuid.UUID,
    tenant_id: uuid.UUID
) -> List[AssetVulnerability]:
    """Get unpatched vulnerabilities for an asset.
    
    Only includes vulnerabilities with status 'unreviewed' or 'acknowledged'.
    Explicitly excludes: 'patched', 'mitigated', 'not_applicable' (and any NULL/other states).
    """
    return db.query(AssetVulnerability).filter(
        AssetVulnerability.asset_id == asset_id,
        AssetVulnerability.tenant_id == tenant_id,
        AssetVulnerability.status.in_(["unreviewed", "acknowledged"])
        # Only include unreviewed and acknowledged - exclude patched, mitigated, not_applicable
    ).all()


def get_vulnerability_feed_source(
    db: Session,
    feed_source_id: uuid.UUID,
    tenant_id: Optional[uuid.UUID] = None
) -> Optional[VulnerabilityFeedSource]:
    """Get a vulnerability feed source"""
    query = db.query(VulnerabilityFeedSource).filter(
        VulnerabilityFeedSource.id == feed_source_id
    )
    
    if tenant_id is not None:
        query = query.filter(
            or_(
                VulnerabilityFeedSource.tenant_id == tenant_id,
                VulnerabilityFeedSource.tenant_id == None  # system-wide
            )
        )
    
    return query.first()


def get_vulnerability_feed_sources(
    db: Session,
    tenant_id: Optional[uuid.UUID] = None,
    sync_enabled: Optional[bool] = None
) -> List[VulnerabilityFeedSource]:
    """Get list of vulnerability feed sources"""
    query = db.query(VulnerabilityFeedSource)
    
    if tenant_id is not None:
        query = query.filter(
            or_(
                VulnerabilityFeedSource.tenant_id == tenant_id,
                VulnerabilityFeedSource.tenant_id == None  # system-wide
            )
        )
    
    if sync_enabled is not None:
        query = query.filter(VulnerabilityFeedSource.sync_enabled == sync_enabled)
    
    return query.all()


def create_vulnerability_feed_source(
    db: Session,
    feed_source: VulnerabilityFeedSourceCreate
) -> VulnerabilityFeedSource:
    """Create a new vulnerability feed source"""
    db_feed = VulnerabilityFeedSource(**feed_source.dict())
    db.add(db_feed)
    db.commit()
    db.refresh(db_feed)
    return db_feed


def update_vulnerability_feed_source(
    db: Session,
    feed_source_id: uuid.UUID,
    tenant_id: uuid.UUID,
    feed_source_update: VulnerabilityFeedSourceUpdate
) -> Optional[VulnerabilityFeedSource]:
    """Update an existing vulnerability feed source"""
    db_feed = db.query(VulnerabilityFeedSource).filter(
        VulnerabilityFeedSource.id == feed_source_id,
        (VulnerabilityFeedSource.tenant_id == tenant_id) | (VulnerabilityFeedSource.tenant_id.is_(None))
    ).first()
    
    if not db_feed:
        return None
    
    update_data = feed_source_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_feed, field, value)
    
    db.commit()
    db.refresh(db_feed)
    return db_feed


def delete_vulnerability_feed_source(
    db: Session,
    feed_source_id: uuid.UUID,
    tenant_id: uuid.UUID
) -> bool:
    """Delete a vulnerability feed source"""
    db_feed = db.query(VulnerabilityFeedSource).filter(
        VulnerabilityFeedSource.id == feed_source_id,
        or_(
            VulnerabilityFeedSource.tenant_id == tenant_id,
            VulnerabilityFeedSource.tenant_id.is_(None)
        )
    ).first()

    if not db_feed:
        return False

    db.delete(db_feed)
    db.commit()
    return True


def get_assets_with_vulnerabilities(
    db: Session,
    tenant_id: uuid.UUID,
    severity_min: Optional[str] = None,
    status: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get assets with vulnerabilities, optionally filtered"""
    query = db.query(
        Asset.id,
        Asset.name,
        func.count(AssetVulnerability.id).label('vuln_count')
    ).join(
        AssetVulnerability,
        Asset.id == AssetVulnerability.asset_id
    ).filter(
        Asset.tenant_id == tenant_id,
        Asset.deleted_at == None
    )
    
    if status:
        query = query.filter(AssetVulnerability.status == status)
    
    if severity_min:
        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        min_order = severity_order.get(severity_min, 0)
        query = query.join(
            Vulnerability,
            AssetVulnerability.vulnerability_id == Vulnerability.id
        ).filter(
            func.cast(
                func.replace(
                    func.replace(
                        func.replace(
                            func.replace(Vulnerability.severity, 'critical', '4'),
                            'high', '3'
                        ),
                        'medium', '2'
                    ),
                    'low', '1'
                ),
                sa.Integer
            ) >= min_order
        )
    
    return query.group_by(Asset.id, Asset.name).all()

