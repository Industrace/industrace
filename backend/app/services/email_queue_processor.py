# backend/app/services/email_queue_processor.py
import uuid
from typing import Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models import NotificationQueue, NotificationLog, TenantSMTPConfig
from app.services.email_service import EmailConfig, EmailProvider, send_email
import logging

logger = logging.getLogger(__name__)


class EmailQueueProcessor:
    """Process notification queue and send emails"""
    
    @staticmethod
    def get_smtp_config(db: Session, tenant_id: uuid.UUID) -> Optional[EmailConfig]:
        """Get SMTP configuration for tenant"""
        smtp_config = (
            db.query(TenantSMTPConfig)
            .filter(TenantSMTPConfig.tenant_id == tenant_id)
            .first()
        )
        
        if not smtp_config or not smtp_config.host:
            logger.warning(f"No verified SMTP config for tenant {tenant_id}")
            return None
        
        return EmailConfig(
            provider=EmailProvider.SMTP,
            smtp_host=smtp_config.host,
            smtp_port=smtp_config.port,
            smtp_username=smtp_config.username,
            smtp_password=smtp_config.password,
            smtp_use_tls=smtp_config.use_tls,
            from_email=smtp_config.from_email
        )
    
    @staticmethod
    def process_queue(db: Session, batch_size: int = 50) -> Dict[str, int]:
        """
        Process notification queue.
        Returns: {'sent': int, 'failed': int, 'skipped': int}
        """
        stats = {'sent': 0, 'failed': 0, 'skipped': 0}
        
        try:
            now = datetime.utcnow()
            
            # Get pending notifications scheduled for now or earlier
            try:
                pending = (
                    db.query(NotificationQueue)
                    .filter(
                        NotificationQueue.status == 'pending',
                        NotificationQueue.scheduled_for <= now
                    )
                    .limit(batch_size)
                    .all()
                )
            except Exception as e:
                logger.error(f"Error querying notification queue: {e}", exc_info=True)
                db.rollback()
                return stats
            
            for notification in pending:
                try:
                    # Get SMTP config
                    email_config = EmailQueueProcessor.get_smtp_config(db, notification.tenant_id)
                    
                    if not email_config:
                        # Skip if no SMTP config
                        notification.status = 'cancelled'
                        notification.error_message = 'No SMTP configuration'
                        stats['skipped'] += 1
                        db.commit()
                        continue
                    
                    # Send email
                    notification.attempts += 1
                    notification.last_attempt_at = now
                    
                    success = send_email(
                        notification.email,
                        notification.subject,
                        notification.body_text or '',
                        email_config,
                        notification.body_html
                    )
                    
                    if success:
                        notification.status = 'sent'
                        notification.sent_at = now
                        stats['sent'] += 1
                        
                        # Create log entry
                        log_entry = NotificationLog(
                            tenant_id=notification.tenant_id,
                            user_id=notification.user_id,
                            notification_type=notification.notification_type,
                            status='sent',
                            sent_at=now,
                            context_data=notification.context_data
                        )
                        db.add(log_entry)
                    else:
                        notification.status = 'failed'
                        notification.error_message = 'Email send failed'
                        stats['failed'] += 1
                        
                        # Create log entry
                        log_entry = NotificationLog(
                            tenant_id=notification.tenant_id,
                            user_id=notification.user_id,
                            notification_type=notification.notification_type,
                            status='failed',
                            error_message='Email send failed',
                            context_data=notification.context_data
                        )
                        db.add(log_entry)
                    
                    db.commit()
                    
                except Exception as e:
                    logger.error(f"Error processing notification {notification.id}: {e}", exc_info=True)
                    try:
                        notification.status = 'failed'
                        notification.error_message = str(e)[:500]  # Limit error message length
                        notification.attempts += 1
                        notification.last_attempt_at = now
                        stats['failed'] += 1
                        db.commit()
                    except Exception as commit_error:
                        logger.error(f"Error committing failed notification {notification.id}: {commit_error}", exc_info=True)
                        db.rollback()
                        
        except Exception as e:
            logger.error(f"Unexpected error in process_queue: {e}", exc_info=True)
            try:
                db.rollback()
            except Exception as rollback_error:
                logger.error(f"Error during rollback: {rollback_error}", exc_info=True)
        
        return stats

