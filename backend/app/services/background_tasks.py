# backend/app/services/background_tasks.py
"""
Background tasks for notification system.
Processes email queue and checks for asset reviews.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.services.email_queue_processor import EmailQueueProcessor
from app.services.asset_review_service import AssetReviewService
from app.services.notification_service import NotificationService
from app.models import Tenant, Asset

logger = logging.getLogger(__name__)


class BackgroundTaskManager:
    """Manages background tasks for notifications"""
    
    _running = False
    _tasks = []
    
    @classmethod
    def start(cls):
        """Start background tasks"""
        if cls._running:
            logger.warning("Background tasks already running")
            return
        
        cls._running = True
        logger.info("Starting background tasks...")
        
        # Start email queue processor task
        email_task = asyncio.create_task(cls._process_email_queue_loop())
        cls._tasks.append(email_task)
        
        # Start asset review checker task
        review_task = asyncio.create_task(cls._check_asset_reviews_loop())
        cls._tasks.append(review_task)
        
        logger.info("Background tasks started")
    
    @classmethod
    def stop(cls):
        """Stop background tasks"""
        if not cls._running:
            return
        
        logger.info("Stopping background tasks...")
        cls._running = False
        
        # Cancel all tasks
        for task in cls._tasks:
            task.cancel()
        
        cls._tasks = []
        logger.info("Background tasks stopped")
    
    @classmethod
    async def _process_email_queue_loop(cls):
        """Process email queue every 60 seconds"""
        while cls._running:
            try:
                db = SessionLocal()
                try:
                    stats = EmailQueueProcessor.process_queue(db, batch_size=50)
                    if stats['sent'] > 0 or stats['failed'] > 0:
                        logger.info(f"Email queue processed: {stats}")
                except Exception as e:
                    logger.error(f"Error processing email queue: {e}", exc_info=True)
                finally:
                    db.close()
            except Exception as e:
                logger.error(f"Error in email queue loop: {e}", exc_info=True)
            
            # Wait 60 seconds before next run
            await asyncio.sleep(60)
    
    @classmethod
    async def _check_asset_reviews_loop(cls):
        """Check for asset reviews due and send notifications every 24 hours"""
        # Wait 1 minute on startup before first check
        await asyncio.sleep(60)
        
        while cls._running:
            try:
                db = SessionLocal()
                try:
                    # Get all tenants
                    tenants = db.query(Tenant).all()
                    
                    for tenant in tenants:
                        try:
                            # Get assets due for review (within next 30 days or overdue)
                            due_assets = AssetReviewService.get_assets_due_for_review(
                                db, tenant.id, days_ahead=30
                            )
                            
                            logger.info(f"Tenant {tenant.id}: Found {len(due_assets)} assets due for review")
                            
                            for asset in due_assets:
                                try:
                                    # Calculate days until review
                                    if asset.next_review_date:
                                        days_until = (asset.next_review_date - datetime.utcnow()).days
                                        
                                        # Send notification if due within 7 days or overdue
                                        if days_until <= 7:
                                            logger.info(
                                                f"Asset {asset.id} ({asset.name}): "
                                                f"Review due in {days_until} days, sending notification"
                                            )
                                            NotificationService.send_asset_review_reminder(
                                                db, asset.id, days_until
                                            )
                                except Exception as e:
                                    logger.error(
                                        f"Error sending review reminder for asset {asset.id}: {e}",
                                        exc_info=True
                                    )
                            
                            # Commit changes
                            db.commit()
                        except Exception as e:
                            logger.error(
                                f"Error processing reviews for tenant {tenant.id}: {e}",
                                exc_info=True
                            )
                            db.rollback()
                except Exception as e:
                    logger.error(f"Error in asset review check loop: {e}", exc_info=True)
                finally:
                    db.close()
            except Exception as e:
                logger.error(f"Error in review check loop: {e}", exc_info=True)
            
            # Wait 24 hours before next check
            await asyncio.sleep(24 * 60 * 60)  # 24 hours


# Convenience functions for manual triggering
def process_email_queue_manual(batch_size: int = 50) -> dict:
    """Manually process email queue (for testing or manual triggers)"""
    db = SessionLocal()
    try:
        return EmailQueueProcessor.process_queue(db, batch_size=batch_size)
    finally:
        db.close()


def check_asset_reviews_manual(tenant_id=None) -> dict:
    """Manually check asset reviews and send notifications (for testing)"""
    db = SessionLocal()
    try:
        if tenant_id:
            tenants = [db.query(Tenant).filter(Tenant.id == tenant_id).first()]
        else:
            tenants = db.query(Tenant).all()
        
        results = {}
        for tenant in tenants:
            if not tenant:
                continue
            
            due_assets = AssetReviewService.get_assets_due_for_review(
                db, tenant.id, days_ahead=30
            )
            
            notifications_sent = 0
            for asset in due_assets:
                if asset.next_review_date:
                    days_until = (asset.next_review_date - datetime.utcnow()).days
                    if days_until <= 7:
                        try:
                            NotificationService.send_asset_review_reminder(
                                db, asset.id, days_until
                            )
                            notifications_sent += 1
                        except Exception as e:
                            logger.error(f"Error sending reminder for asset {asset.id}: {e}")
            
            results[str(tenant.id)] = {
                'assets_due': len(due_assets),
                'notifications_sent': notifications_sent
            }
        
        db.commit()
        return results
    finally:
        db.close()

