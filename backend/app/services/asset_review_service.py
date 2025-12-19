# backend/app/services/asset_review_service.py
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models import Asset, Tenant, Site
import uuid
import logging

logger = logging.getLogger(__name__)


class AssetReviewService:
    """Service for managing asset review and maintenance reminders"""
    
    @staticmethod
    def get_review_interval_months(asset: Asset, db: Session) -> int:
        """
        Get review interval for an asset.
        Priority: Asset > Site > Tenant > Default (6)
        """
        # Check asset-specific interval
        if asset.review_interval_months and asset.review_interval_months > 0:
            return asset.review_interval_months
        
        # Check site-specific interval
        if asset.site_id:
            site = db.query(Site).filter(Site.id == asset.site_id).first()
            if site and site.review_interval_months and site.review_interval_months > 0:
                return site.review_interval_months
        
        # Check tenant default
        tenant = db.query(Tenant).filter(Tenant.id == asset.tenant_id).first()
        if tenant and tenant.default_review_interval_months and tenant.default_review_interval_months > 0:
            return tenant.default_review_interval_months
        
        # Default
        return 6
    
    @staticmethod
    def calculate_next_review_date(asset: Asset, db: Session) -> Optional[datetime]:
        """
        Calculate next review date for an asset.
        Logic:
        1. If last_review_date exists → next_review_date = last_review_date + interval
        2. If last_review_date is None → use created_at as base (first review)
        3. If created_at is None (anomaly) → use current date as base
        """
        interval_months = AssetReviewService.get_review_interval_months(asset, db)
        
        # Base date for calculation
        base_date = None
        
        if asset.last_review_date:
            # Asset has been reviewed before: next review = last review + interval
            base_date = asset.last_review_date
            logger.info(f"Asset {asset.id}: Using last_review_date {base_date} as base")
        elif asset.created_at:
            # Asset never reviewed: use creation date as base (first review)
            base_date = asset.created_at
            logger.info(f"Asset {asset.id}: Using created_at {base_date} as base (first review)")
        elif asset.updated_at:
            # Fallback: use updated_at if created_at is missing
            base_date = asset.updated_at
            logger.warning(f"Asset {asset.id}: created_at missing, using updated_at {base_date} as base")
        else:
            # Last resort: use current date (shouldn't happen normally)
            base_date = datetime.utcnow()
            logger.warning(f"Asset {asset.id}: No date fields found, using current date {base_date} as base")
        
        # Calculate next review date
        # Approximate: 30 days per month
        days_to_add = interval_months * 30
        next_review = base_date + timedelta(days=days_to_add)
        
        logger.info(f"Asset {asset.id}: Calculated next_review_date = {next_review} (interval = {interval_months} months, base = {base_date})")
        
        return next_review
    
    @staticmethod
    def update_review_status(asset: Asset, db: Session) -> Asset:
        """
        Update review status based on next_review_date.
        Status: 'pending', 'reviewed', 'overdue', 'skipped'
        """
        if not asset.next_review_date:
            # Calculate if not set
            asset.next_review_date = AssetReviewService.calculate_next_review_date(asset, db)
        
        if asset.next_review_date:
            today = datetime.utcnow()
            if asset.next_review_date < today:
                # Only set to overdue if not already reviewed or skipped
                if asset.review_status not in ['reviewed', 'skipped']:
                    asset.review_status = 'overdue'
            elif asset.review_status == 'reviewed':
                # Keep reviewed status if already reviewed
                pass
            elif asset.review_status != 'skipped':
                # Set to pending if not reviewed or skipped
                asset.review_status = 'pending'
        else:
            # If we can't calculate next_review_date, set status to pending
            if asset.review_status not in ['reviewed', 'skipped']:
                asset.review_status = 'pending'
        
        return asset
    
    @staticmethod
    def get_assets_due_for_review(
        db: Session,
        tenant_id: uuid.UUID,
        days_ahead: Optional[int] = None
    ) -> List[Asset]:
        """
        Get assets that need review within the next 'days_ahead' days.
        Includes overdue assets.
        If days_ahead is None, uses tenant configuration.
        """
        # Get tenant configuration if days_ahead not provided
        if days_ahead is None:
            tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
            days_ahead = tenant.review_due_days_ahead if tenant and tenant.review_due_days_ahead else 30
        
        today = datetime.utcnow()
        future_date = today + timedelta(days=days_ahead)
        
        logger.info(f"Getting assets due for review: days_ahead={days_ahead}, today={today}, future_date={future_date}")
        
        # Get all assets for tenant
        assets = (
            db.query(Asset)
            .filter(
                Asset.tenant_id == tenant_id,
                Asset.deleted_at.is_(None)
            )
            .all()
        )
        
        logger.info(f"Found {len(assets)} total assets for tenant {tenant_id}")
        
        due_assets = []
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
            
            # Check if due (includes overdue)
            if asset.next_review_date:
                if asset.next_review_date <= future_date:
                    # Include if due in next N days or overdue
                    if asset.next_review_date < today:
                        # Overdue
                        if asset.review_status in ['pending', 'overdue', None]:
                            logger.info(f"Asset {asset.id} ({asset.name}): ADDED to due list (overdue)")
                            due_assets.append(asset)
                    else:
                        # Due in future
                        if asset.review_status in ['pending', None]:
                            logger.info(f"Asset {asset.id} ({asset.name}): ADDED to due list (future)")
                            due_assets.append(asset)
        
        # Commit all changes at once
        if needs_commit:
            db.commit()
        
        logger.info(f"Returning {len(due_assets)} assets due for review")
        return due_assets
    
    @staticmethod
    def get_overdue_assets(
        db: Session,
        tenant_id: uuid.UUID
    ) -> List[Asset]:
        """Get assets with overdue reviews"""
        today = datetime.utcnow()
        
        # Get all assets for tenant
        assets = (
            db.query(Asset)
            .filter(
                Asset.tenant_id == tenant_id,
                Asset.deleted_at.is_(None)
            )
            .all()
        )
        
        logger.info(f"Found {len(assets)} total assets for tenant {tenant_id}")
        
        overdue = []
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
                    logger.warning(f"Asset {asset.id} ({asset.name}): could not calculate next_review_date (no base date)")
            
            # Check if overdue
            if asset.next_review_date:
                logger.info(f"Asset {asset.id} ({asset.name}): next_review_date = {asset.next_review_date}, status = {asset.review_status}")
                if asset.next_review_date < today:
                    if asset.review_status in ['pending', 'overdue', None]:
                        logger.info(f"Asset {asset.id} ({asset.name}): ADDED to overdue list")
                        overdue.append(asset)
                    else:
                        logger.info(f"Asset {asset.id} ({asset.name}): NOT added (status = {asset.review_status})")
                else:
                    logger.info(f"Asset {asset.id} ({asset.name}): NOT overdue (next_review_date >= today)")
            else:
                logger.warning(f"Asset {asset.id} ({asset.name}): no next_review_date after calculation")
        
        # Commit all changes at once
        if needs_commit:
            db.commit()
        
        logger.info(f"Returning {len(overdue)} overdue assets")
        return overdue
    
    @staticmethod
    def mark_as_reviewed(
        db: Session,
        asset_id: uuid.UUID,
        reviewed_by: uuid.UUID,
        notes: Optional[str] = None,
        next_review_override: Optional[datetime] = None,
        send_notification: bool = False
    ) -> Asset:
        """
        Mark asset as reviewed.
        Updates last_review_date, calculates next_review_date, updates status.
        Optionally sends notification to owners/points-of-contact.
        """
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            raise ValueError(f"Asset {asset_id} not found")
        
        # Update review information
        asset.last_review_date = datetime.utcnow()
        asset.review_status = 'reviewed'
        
        if notes:
            asset.review_notes = notes
        
        # Calculate or use override for next review date
        if next_review_override:
            asset.next_review_date = next_review_override
        else:
            asset.next_review_date = AssetReviewService.calculate_next_review_date(asset, db)
        
        db.commit()
        db.refresh(asset)
        
        # Send notification if requested (future: notify about next review date)
        if send_notification:
            try:
                # Import here to avoid circular dependency
                from app.services.notification_service import NotificationService
                # Calculate days until next review
                if asset.next_review_date:
                    days_until = (asset.next_review_date - datetime.utcnow()).days
                    NotificationService.send_asset_review_reminder(db, asset_id, days_until)
            except Exception as e:
                logger.error(f"Error sending review notification: {e}")
        
        return asset
    
    @staticmethod
    def skip_review(
        db: Session,
        asset_id: uuid.UUID,
        skipped_by: uuid.UUID,
        reason: str,
        next_review_date: datetime
    ) -> Asset:
        """
        Skip review for an asset (e.g., asset in maintenance).
        Sets review_status to 'skipped' and updates next_review_date.
        """
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            raise ValueError(f"Asset {asset_id} not found")
        
        asset.review_status = 'skipped'
        asset.next_review_date = next_review_date
        if reason:
            asset.review_notes = f"Skipped: {reason}"
        
        db.commit()
        db.refresh(asset)
        
        return asset
    
    @staticmethod
    def bulk_mark_as_reviewed(
        db: Session,
        asset_ids: List[uuid.UUID],
        reviewed_by: uuid.UUID,
        notes: Optional[str] = None
    ) -> List[Asset]:
        """Mark multiple assets as reviewed"""
        assets = db.query(Asset).filter(Asset.id.in_(asset_ids)).all()
        
        reviewed_assets = []
        for asset in assets:
            reviewed = AssetReviewService.mark_as_reviewed(
                db, asset.id, reviewed_by, notes
            )
            reviewed_assets.append(reviewed)
        
        return reviewed_assets
    
    @staticmethod
    def recalculate_all_next_review_dates(
        db: Session,
        tenant_id: uuid.UUID
    ) -> int:
        """
        Recalculate next_review_date for all assets in a tenant.
        Useful after changing review intervals.
        Returns count of updated assets.
        Ensures all assets have a next_review_date, even if they've never been reviewed.
        """
        assets = (
            db.query(Asset)
            .filter(
                Asset.tenant_id == tenant_id,
                Asset.deleted_at.is_(None)
            )
            .all()
        )
        
        logger.info(f"Recalculating review dates for {len(assets)} assets")
        
        updated_count = 0
        for asset in assets:
            old_next = asset.next_review_date
            
            # Always calculate next_review_date, even if asset has never been reviewed
            calculated_date = AssetReviewService.calculate_next_review_date(asset, db)
            if calculated_date:
                asset.next_review_date = calculated_date
                AssetReviewService.update_review_status(asset, db)
                
                if old_next != asset.next_review_date:
                    updated_count += 1
                    logger.info(f"Asset {asset.id} ({asset.name}): Updated next_review_date from {old_next} to {calculated_date}")
            else:
                logger.warning(f"Asset {asset.id} ({asset.name}): Could not calculate next_review_date")
        
        db.commit()
        logger.info(f"Updated {updated_count} assets")
        return updated_count

