# backend/app/routers/asset_reviews.py
import uuid
from typing import List, Optional
from datetime import datetime
from app.models import Tenant

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.database import get_db
from app.models import User, Asset
from app.services.auth import get_current_user
from app.services.audit_decorator import audit_log_action
from app.services.asset_review_service import AssetReviewService
from app.errors.exceptions import ErrorCodeException
from app.errors.error_codes import ErrorCode
from app.schemas.asset import AssetRead as AssetSchema

router = APIRouter(prefix="/assets", tags=["Asset Reviews"])


class AssetReviewStatusResponse(BaseModel):
    """Response for asset review status"""
    asset_id: uuid.UUID
    last_review_date: Optional[datetime]
    next_review_date: Optional[datetime]
    review_status: str
    review_notes: Optional[str]
    review_interval_months: int
    days_until_review: Optional[int] = None
    days_overdue: Optional[int] = None
    
    class Config:
        from_attributes = True


class AssetReviewRequest(BaseModel):
    """Request to mark asset as reviewed"""
    notes: Optional[str] = Field(None, max_length=5000, description="Review notes")
    next_review_override: Optional[datetime] = Field(None, description="Override next review date")


class AssetReviewSkipRequest(BaseModel):
    """Request to skip asset review"""
    reason: str = Field(..., max_length=500, description="Reason for skipping review")
    next_review_date: datetime = Field(..., description="Next review date after skip")


class BulkReviewRequest(BaseModel):
    """Request for bulk review"""
    asset_ids: List[uuid.UUID] = Field(..., description="List of asset IDs to mark as reviewed")
    notes: Optional[str] = Field(None, max_length=5000, description="Review notes")


@router.get("/{asset_id}/review-status", response_model=AssetReviewStatusResponse)
def get_asset_review_status(
    asset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get review status for an asset"""
    asset = (
        db.query(Asset)
        .filter(Asset.id == asset_id, Asset.tenant_id == current_user.tenant_id)
        .first()
    )
    if not asset:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)
    
    # Calculate days until review or days overdue
    days_until_review = None
    days_overdue = None
    if asset.next_review_date:
        today = datetime.utcnow()
        delta = (asset.next_review_date - today).days
        if delta < 0:
            days_overdue = abs(delta)
        else:
            days_until_review = delta
    
    # Get review interval
    review_interval = AssetReviewService.get_review_interval_months(asset, db)
    
    return AssetReviewStatusResponse(
        asset_id=asset.id,
        last_review_date=asset.last_review_date,
        next_review_date=asset.next_review_date,
        review_status=asset.review_status,
        review_notes=asset.review_notes,
        review_interval_months=review_interval,
        days_until_review=days_until_review,
        days_overdue=days_overdue
    )


@router.post("/{asset_id}/review", response_model=AssetSchema)
@audit_log_action("mark_asset_reviewed", "Asset", model_class=Asset)
def mark_asset_as_reviewed(
    asset_id: uuid.UUID,
    review_data: AssetReviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark an asset as reviewed"""
    asset = (
        db.query(Asset)
        .filter(Asset.id == asset_id, Asset.tenant_id == current_user.tenant_id)
        .first()
    )
    if not asset:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)
    
    updated_asset = AssetReviewService.mark_as_reviewed(
        db,
        asset_id,
        current_user.id,
        review_data.notes,
        review_data.next_review_override
    )
    
    return AssetSchema.from_orm(updated_asset)


@router.post("/{asset_id}/review/skip", response_model=AssetSchema)
@audit_log_action("skip_asset_review", "Asset", model_class=Asset)
def skip_asset_review(
    asset_id: uuid.UUID,
    skip_data: AssetReviewSkipRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Skip review for an asset"""
    asset = (
        db.query(Asset)
        .filter(Asset.id == asset_id, Asset.tenant_id == current_user.tenant_id)
        .first()
    )
    if not asset:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)
    
    updated_asset = AssetReviewService.skip_review(
        db,
        asset_id,
        current_user.id,
        skip_data.reason,
        skip_data.next_review_date
    )
    
    return AssetSchema.from_orm(updated_asset)


@router.get("/review/due", response_model=List[AssetSchema])
def get_assets_due_for_review(
    days_ahead: Optional[int] = Query(None, ge=0, le=365, description="Days ahead to check (uses tenant default if not provided)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get assets that need review within the next N days (includes overdue).
    If days_ahead is not provided, uses tenant configuration."""
    assets = AssetReviewService.get_assets_due_for_review(
        db,
        current_user.tenant_id,
        days_ahead
    )
    
    return [AssetSchema.from_orm(asset) for asset in assets]


@router.get("/review/overdue", response_model=List[AssetSchema])
def get_overdue_assets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get assets with overdue reviews"""
    assets = AssetReviewService.get_overdue_assets(
        db,
        current_user.tenant_id
    )
    
    return [AssetSchema.from_orm(asset) for asset in assets]


@router.get("/review/upcoming", response_model=List[AssetSchema])
def get_upcoming_reviews(
    days: Optional[int] = Query(None, ge=1, le=365, description="Days to look ahead (uses tenant default if not provided)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get assets with reviews coming up in the next N days.
    If days is not provided, uses tenant configuration."""
    from datetime import timedelta
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Get tenant configuration if days not provided
    if days is None:
        from app.models import Tenant
        tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
        days = tenant.review_upcoming_days_ahead if tenant and tenant.review_upcoming_days_ahead else 30
    
    logger.info(f"Getting upcoming reviews: days={days}, tenant_id={current_user.tenant_id}")
    
    # Get all assets for tenant
    assets = (
        db.query(Asset)
        .filter(
            Asset.tenant_id == current_user.tenant_id,
            Asset.deleted_at.is_(None)
        )
        .all()
    )
    
    logger.info(f"Found {len(assets)} total assets")
    
    # Calculate next_review_date if not set and filter upcoming
    today = datetime.utcnow()
    future_date = today + timedelta(days=days)
    upcoming = []
    needs_commit = False
    
    for asset in assets:
        # Calculate next_review_date if not set
        if not asset.next_review_date:
            calculated_date = AssetReviewService.calculate_next_review_date(asset, db)
            logger.info(f"Asset {asset.id} ({asset.name}): calculated next_review_date = {calculated_date}")
            if calculated_date:
                asset.next_review_date = calculated_date
                AssetReviewService.update_review_status(asset, db)
                needs_commit = True
            else:
                logger.warning(f"Asset {asset.id} ({asset.name}): could not calculate next_review_date")
        
        # Include if upcoming (not overdue)
        # Note: We include assets regardless of review_status for upcoming reviews
        # Only exclude 'reviewed' status if the review date has already passed
        if asset.next_review_date:
            logger.info(f"Asset {asset.id} ({asset.name}): next_review_date = {asset.next_review_date}, status = {asset.review_status}, today = {today}, future_date = {future_date}")
            if asset.next_review_date >= today and asset.next_review_date <= future_date:
                # Include all assets with upcoming review dates, regardless of status
                # (except 'skipped' which should be excluded)
                if asset.review_status != 'skipped':
                    logger.info(f"Asset {asset.id} ({asset.name}): ADDED to upcoming list")
                    upcoming.append(asset)
                else:
                    logger.info(f"Asset {asset.id} ({asset.name}): NOT added (status = skipped)")
            else:
                logger.info(f"Asset {asset.id} ({asset.name}): NOT in date range")
        else:
            logger.warning(f"Asset {asset.id} ({asset.name}): no next_review_date after calculation")
    
    # Commit all changes at once
    if needs_commit:
        db.commit()
    
    logger.info(f"Returning {len(upcoming)} upcoming assets")
    return [AssetSchema.from_orm(asset) for asset in upcoming]


@router.post("/review/bulk", response_model=List[AssetSchema])
@audit_log_action("bulk_mark_assets_reviewed", "Asset", model_class=Asset)
def bulk_mark_as_reviewed(
    bulk_data: BulkReviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark multiple assets as reviewed"""
    # Verify all assets belong to tenant
    assets = (
        db.query(Asset)
        .filter(
            Asset.id.in_(bulk_data.asset_ids),
            Asset.tenant_id == current_user.tenant_id
        )
        .all()
    )
    
    if len(assets) != len(bulk_data.asset_ids):
        raise ErrorCodeException(
            status_code=404,
            error_code=ErrorCode.ASSET_NOT_FOUND,
            detail="One or more assets not found"
        )
    
    reviewed_assets = AssetReviewService.bulk_mark_as_reviewed(
        db,
        bulk_data.asset_ids,
        current_user.id,
        bulk_data.notes
    )
    
    return [AssetSchema.from_orm(asset) for asset in reviewed_assets]


@router.post("/review/recalculate-all")
@audit_log_action("recalculate_all_review_dates", "Asset", model_class=Asset)
def recalculate_all_review_dates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Recalculate next_review_date for all assets in tenant"""
    updated_count = AssetReviewService.recalculate_all_next_review_dates(
        db,
        current_user.tenant_id
    )
    
    return {
        "message": f"Recalculated review dates for {updated_count} assets",
        "updated_count": updated_count
    }

