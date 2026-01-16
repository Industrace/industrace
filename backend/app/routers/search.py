import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, String

from app.database import get_db
from app.models import User, Asset, Contact, Supplier, Manufacturer, Site, Location
from app.services.auth import get_current_user
from app.errors.exceptions import ErrorCodeException
from app.errors.error_codes import ErrorCode

router = APIRouter(
    prefix="/search",
    tags=["search"],
)


def sanitize_search_query(query: str, max_length: int = 100) -> str:
    """
    Sanitizes search query to prevent ReDoS and performance issues.
    
    Args:
        query: Raw search query from user
        max_length: Maximum allowed length (default 100)
        
    Returns:
        Sanitized query safe for ILIKE operations
    """
    # Limit query length
    if len(query) > max_length:
        query = query[:max_length]
    
    # Escape special characters for LIKE/ILIKE operations
    # % and _ are wildcards in SQL LIKE, so we escape them
    query = query.replace("\\", "\\\\")  # Escape backslashes first
    query = query.replace("%", "\\%")
    query = query.replace("_", "\\_")
    
    return query


@router.get("/global")
def global_search(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(
        5, ge=1, le=20, description="Maximum number of results per category"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Global search across all system entities.
    Returns results grouped by type, respecting RBAC permissions.
    """
    if not q.strip():
        return {"results": []}

    # Sanitize query to prevent ReDoS and performance issues
    query = sanitize_search_query(q.strip().lower())
    results = []

    # Search Assets
    assets = (
        db.query(Asset)
        .join(Manufacturer, Asset.manufacturer_id == Manufacturer.id, isouter=True)
        .filter(
            and_(
                Asset.tenant_id == current_user.tenant_id,
                Asset.deleted_at == None,
                or_(
                    Asset.name.ilike(f"%{query}%"),
                    Asset.tag.ilike(f"%{query}%"),
                    Asset.serial_number.ilike(f"%{query}%"),
                    Asset.model.ilike(f"%{query}%"),
                    Manufacturer.name.ilike(f"%{query}%"),
                ),
            )
        )
        .limit(limit)
        .all()
    )

    for asset in assets:
        results.append(
            {
                "id": str(asset.id),
                "type": "asset",
                "title": asset.name,
                "desc": (
                    f"serial: {asset.serial_number}"
                    if asset.serial_number
                    else asset.tag
                ),
                "url": f"/assets/{asset.id}",
            }
        )

    # Search Contacts
    contacts = (
        db.query(Contact)
        .filter(
            and_(
                Contact.tenant_id == current_user.tenant_id,
                Contact.deleted_at == None,
                or_(
                    Contact.first_name.ilike(f"%{query}%"),
                    Contact.last_name.ilike(f"%{query}%"),
                    Contact.email.ilike(f"%{query}%"),
                    Contact.phone1.ilike(f"%{query}%"),
                ),
            )
        )
        .limit(limit)
        .all()
    )

    for contact in contacts:
        results.append(
            {
                "id": str(contact.id),
                "type": "contact",
                "title": f"{contact.first_name} {contact.last_name}",
                "desc": contact.email,
                "url": f"/contacts/{contact.id}",
            }
        )

    # Search Suppliers
    suppliers = (
        db.query(Supplier)
        .filter(
            and_(
                Supplier.tenant_id == current_user.tenant_id,
                Supplier.deleted_at == None,
                or_(
                    Supplier.name.ilike(f"%{query}%"),
                    Supplier.vat_number.ilike(f"%{query}%"),
                    Supplier.email.ilike(f"%{query}%"),
                ),
            )
        )
        .limit(limit)
        .all()
    )

    for supplier in suppliers:
        results.append(
            {
                "id": str(supplier.id),
                "type": "supplier",
                "title": supplier.name,
                "desc": (
                    f"P.IVA: {supplier.vat_number}"
                    if supplier.vat_number
                    else supplier.email
                ),
                "url": f"/suppliers/{supplier.id}",
            }
        )

    # Search Manufacturers
    manufacturers = (
        db.query(Manufacturer)
        .filter(
            and_(
                Manufacturer.tenant_id == current_user.tenant_id,
                or_(
                    Manufacturer.name.ilike(f"%{query}%"),
                    Manufacturer.description.ilike(f"%{query}%"),
                ),
            )
        )
        .limit(limit)
        .all()
    )

    for manufacturer in manufacturers:
        results.append(
            {
                "id": str(manufacturer.id),
                "type": "manufacturer",
                "title": manufacturer.name,
                "desc": manufacturer.description,
                "url": f"/manufacturers/{manufacturer.id}",
            }
        )

    # Search Sites
    sites = (
        db.query(Site)
        .filter(
            and_(
                Site.tenant_id == current_user.tenant_id,
                Site.deleted_at == None,
                or_(
                    Site.name.ilike(f"%{query}%"),
                    Site.code.ilike(f"%{query}%"),
                    Site.address.ilike(f"%{query}%"),
                ),
            )
        )
        .limit(limit)
        .all()
    )

    for site in sites:
        results.append(
            {
                "id": str(site.id),
                "type": "site",
                "title": site.name,
                "desc": site.address,
                "url": f"/sites/{site.id}",
            }
        )

    # Search Locations
    from app.models.area import Area
    from sqlalchemy.orm import joinedload
    locations = (
        db.query(Location)
        .options(joinedload(Location.area))
        .join(Area, Location.area_id == Area.id, isouter=True)
        .filter(
            and_(
                Location.tenant_id == current_user.tenant_id,
                Location.deleted_at == None,
                or_(
                    Location.name.ilike(f"%{query}%"),
                    Location.code.ilike(f"%{query}%"),
                    Area.name.ilike(f"%{query}%"),
                    Area.code.ilike(f"%{query}%"),
                ),
            )
        )
        .limit(limit)
        .all()
    )

    for location in locations:
        area_name = location.area.name if location.area else None
        results.append(
            {
                "id": str(location.id),
                "type": "location",
                "title": location.name,
                "desc": area_name or location.code or "",
                "url": f"/locations/{location.id}",
            }
        )

    return {"results": results}
