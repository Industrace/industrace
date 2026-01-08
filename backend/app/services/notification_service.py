# backend/app/services/notification_service.py
import uuid
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models import (
    NotificationTemplate,
    NotificationPreference,
    NotificationQueue,
    NotificationLog,
    User,
    TenantSMTPConfig,
    Asset
)
from app.services.email_service import EmailConfig, EmailProvider, send_email
from app.crud.assets import get_asset_contacts_by_role
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing notifications"""
    
    @staticmethod
    def render_template(template: NotificationTemplate, context: Dict) -> Dict[str, str]:
        """
        Render email template with context variables.
        Returns: {'subject': str, 'body_html': str, 'body_text': str}
        """
        subject = template.subject_template
        body_html = template.body_template_html
        body_text = template.body_template_text or ""
        
        # Simple template rendering (replace {{variable}} with context values)
        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            subject = subject.replace(placeholder, str(value))
            body_html = body_html.replace(placeholder, str(value))
            body_text = body_text.replace(placeholder, str(value))
        
        return {
            'subject': subject,
            'body_html': body_html,
            'body_text': body_text
        }
    
    @staticmethod
    def get_user_preference(
        db: Session,
        user_id: uuid.UUID,
        notification_type: str
    ) -> Optional[NotificationPreference]:
        """Get user preference for a notification type"""
        return (
            db.query(NotificationPreference)
            .filter(
                NotificationPreference.user_id == user_id,
                NotificationPreference.notification_type == notification_type
            )
            .first()
        )
    
    @staticmethod
    def should_send_notification(
        db: Session,
        user_id: uuid.UUID,
        notification_type: str,
        context: Dict
    ) -> bool:
        """
        Check if notification should be sent based on user preferences.
        Returns True if should send, False otherwise.
        """
        # First check global notification setting
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"User {user_id} not found when checking notification preferences")
            return False
        
        # Check if notifications_enabled field exists and is False
        # If field doesn't exist (None), default to True for backward compatibility
        notifications_enabled = getattr(user, 'notifications_enabled', True)
        if notifications_enabled is False:
            logger.info(f"Global notifications disabled for user {user_id}, skipping notification {notification_type}")
            return False
        
        preference = NotificationService.get_user_preference(db, user_id, notification_type)
        
        # If no preference, default to enabled
        if not preference:
            logger.debug(f"No preference found for user {user_id}, notification type {notification_type}, defaulting to enabled")
            return True
        
        # Check if email is enabled
        if not preference.email_enabled:
            logger.debug(f"Email disabled for user {user_id}, notification type {notification_type}")
            return False
        
        # Check severity filter if applicable
        if preference.severity_min is not None:
            severity = context.get('severity', 0)
            logger.debug(f"Checking severity: {severity} >= {preference.severity_min} for user {user_id}, notification type {notification_type}")
            if severity < preference.severity_min:
                logger.info(f"Severity {severity} below minimum {preference.severity_min} for user {user_id}, notification type {notification_type}. Skipping notification.")
                return False
        
        # Check custom filters
        if preference.filters:
            # Example: filter by site_id
            if 'site_id' in preference.filters:
                context_site_id = context.get('site_id')
                if context_site_id and str(context_site_id) not in preference.filters['site_id']:
                    logger.debug(f"Site filter mismatch for user {user_id}, notification type {notification_type}")
                    return False
        
        logger.debug(f"All checks passed for user {user_id}, notification type {notification_type}. Notification will be sent.")
        return True
    
    @staticmethod
    def send_notification(
        db: Session,
        user_id: uuid.UUID,
        notification_type: str,
        context_data: Dict,
        scheduled_for: Optional[datetime] = None
    ) -> NotificationQueue:
        """
        Create and queue a notification.
        - Verifies user preferences
        - Renders template
        - Adds to queue
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Check if should send
        if not NotificationService.should_send_notification(db, user_id, notification_type, context_data):
            logger.info(f"Skipping notification {notification_type} for user {user_id} (preferences)")
            return None
        
        # Get template (prioritize tenant-specific override over system-wide)
        template = (
            db.query(NotificationTemplate)
            .filter(
                NotificationTemplate.template_code == notification_type,
                or_(
                    NotificationTemplate.tenant_id == user.tenant_id,
                    NotificationTemplate.tenant_id.is_(None)  # system-wide
                ),
                NotificationTemplate.enabled == True
            )
            .order_by(
                # Prioritize tenant-specific templates over system-wide (NULL tenant_id)
                NotificationTemplate.tenant_id.desc().nulls_last()
            )
            .first()
        )
        
        if not template:
            logger.warning(f"Template {notification_type} not found or not enabled for tenant {user.tenant_id}")
            return None
        
        logger.debug(f"Using template {template.id} ({'tenant-specific' if template.tenant_id else 'system-wide'}) for notification type {notification_type}")
        
        # Render template
        rendered = NotificationService.render_template(template, context_data)
        
        # Create queue entry
        queue_entry = NotificationQueue(
            tenant_id=user.tenant_id,
            user_id=user_id,
            email=user.email,
            notification_type=notification_type,
            template_id=template.id,
            subject=rendered['subject'],
            body_html=rendered['body_html'],
            body_text=rendered['body_text'],
            context_data=context_data,
            scheduled_for=scheduled_for or datetime.utcnow()
        )
        
        db.add(queue_entry)
        db.commit()
        db.refresh(queue_entry)
        
        return queue_entry
    
    @staticmethod
    def send_asset_review_reminder(
        db: Session,
        asset_id: uuid.UUID,
        days_until_review: int = 0
    ) -> List[NotificationQueue]:
        """
        Send reminder for asset review.
        Finds owners and points-of-contact and sends notification to each.
        """
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            raise ValueError(f"Asset {asset_id} not found")
        
        # Get owners and points-of-contact
        owners = get_asset_contacts_by_role(db, asset_id, 'owner')
        points_of_contact = get_asset_contacts_by_role(db, asset_id, 'point_of_contact')
        
        # Get user IDs from contacts (assuming contact.email matches user.email)
        user_ids = []
        for contact in owners + points_of_contact:
            if contact.email:
                user = db.query(User).filter(
                    User.email == contact.email,
                    User.tenant_id == asset.tenant_id
                ).first()
                if user:
                    user_ids.append(user.id)
        
        # Send notification to each user
        notifications = []
        for user_id in user_ids:
            context = {
                'asset_name': asset.name,
                'asset_id': str(asset.id),
                'site_name': asset.site.name if asset.site else 'Unknown',
                'last_review_date': asset.last_review_date.isoformat() if asset.last_review_date else 'Never',
                'days_overdue': abs(days_until_review) if days_until_review < 0 else 0,
                'days_until_review': days_until_review if days_until_review >= 0 else 0,
                'asset_url': f"/assets/{asset.id}"  # Frontend URL
            }
            
            notification_type = 'asset_review_overdue' if days_until_review < 0 else 'asset_review_due'
            
            try:
                queue_entry = NotificationService.send_notification(
                    db, user_id, notification_type, context
                )
                if queue_entry:
                    notifications.append(queue_entry)
            except Exception as e:
                logger.error(f"Error sending review reminder to user {user_id}: {e}")
        
        return notifications
    
    @staticmethod
    def send_risk_alert(
        db: Session,
        asset_id: uuid.UUID,
        risk_score: float,
        risk_level: str
    ) -> List[NotificationQueue]:
        """Send alert for asset with high risk score"""
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            logger.warning(f"Asset {asset_id} not found for risk alert")
            raise ValueError(f"Asset {asset_id} not found")
        
        logger.info(f"Sending risk alert for asset {asset_id} (name: {asset.name}), risk_score: {risk_score}, risk_level: {risk_level}")
        
        user_ids = set()  # Use set to avoid duplicates
        
        # Strategy 1: Try to get owners with associated users
        owners = get_asset_contacts_by_role(db, asset_id, 'owner')
        logger.info(f"Found {len(owners)} owners for asset {asset_id}")
        
        for contact in owners:
            if contact.email:
                user = db.query(User).filter(
                    User.email == contact.email,
                    User.tenant_id == asset.tenant_id,
                    User.is_active == True,
                    User.deleted_at.is_(None)
                ).first()
                if user:
                    user_ids.add(user.id)
                    logger.info(f"Found user {user.id} ({user.email}) for owner contact {contact.email}")
                else:
                    logger.debug(f"No user found for owner contact email {contact.email} in tenant {asset.tenant_id}")
        
        # Strategy 2: If no owners with users, get all users with active preference for risk_alert
        if not user_ids:
            logger.info(f"No owners with users found, checking users with risk_alert preference")
            preferences = (
                db.query(NotificationPreference)
                .join(User)
                .filter(
                    NotificationPreference.notification_type == 'risk_alert',
                    NotificationPreference.email_enabled == True,
                    User.tenant_id == asset.tenant_id,
                    User.is_active == True,
                    User.deleted_at.is_(None)
                )
                .all()
            )
            
            for preference in preferences:
                # Check if severity threshold is met
                if preference.severity_min is not None:
                    if risk_score >= preference.severity_min:
                        user_ids.add(preference.user_id)
                        logger.info(f"User {preference.user_id} has active preference for risk_alert (severity_min={preference.severity_min}, risk_score={risk_score})")
                else:
                    # No severity threshold, include user
                    user_ids.add(preference.user_id)
                    logger.info(f"User {preference.user_id} has active preference for risk_alert (no severity threshold)")
        
        # Strategy 3: Fallback to admins if still no users
        if not user_ids:
            logger.info(f"No users found with preferences, falling back to admin users")
            from app.models import Role
            admin_role = (
                db.query(Role)
                .filter(
                    Role.name == 'admin',
                    Role.tenant_id == asset.tenant_id,
                    Role.is_active == True
                )
                .first()
            )
            
            if admin_role:
                admin_users = (
                    db.query(User)
                    .filter(
                        User.role_id == admin_role.id,
                        User.tenant_id == asset.tenant_id,
                        User.is_active == True,
                        User.deleted_at.is_(None)
                    )
                    .all()
                )
                
                for admin_user in admin_users:
                    user_ids.add(admin_user.id)
                    logger.info(f"Added admin user {admin_user.id} ({admin_user.email}) as fallback")
        
        if not user_ids:
            logger.warning(f"No users found to send risk alert for asset {asset_id}")
            return []
        
        # Send notifications to all collected users
        notifications = []
        for user_id in user_ids:
            context = {
                'asset_name': asset.name,
                'asset_id': str(asset.id),
                'risk_score': risk_score,
                'risk_level': risk_level,
                'severity': risk_score,  # Use risk_score as severity for preference filtering
                'site_name': asset.site.name if asset.site else 'Unknown',
                'asset_url': f"/assets/{asset.id}"
            }
            
            logger.info(f"Attempting to send risk alert to user {user_id} with severity {risk_score}")
            try:
                queue_entry = NotificationService.send_notification(
                    db, user_id, 'risk_alert', context
                )
                if queue_entry:
                    notifications.append(queue_entry)
                    logger.info(f"Risk alert queued for user {user_id}, queue entry ID: {queue_entry.id}")
                else:
                    logger.info(f"Risk alert skipped for user {user_id} (preferences or template check failed)")
            except Exception as e:
                logger.error(f"Error sending risk alert to user {user_id}: {e}", exc_info=True)
        
        logger.info(f"Risk alert process completed for asset {asset_id}. {len(notifications)} notifications queued.")
        return notifications

