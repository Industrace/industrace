# backend/app/init_data/init_notification_templates.py
"""
Initialize default notification templates for the system.
These templates are system-wide (tenant_id = NULL).
"""
from sqlalchemy.orm import Session
from app.models import NotificationTemplate
import uuid


def init_notification_templates(db: Session):
    """Create default notification templates"""
    
    templates = [
        {
            'template_code': 'asset_review_due',
            'name': 'Asset Review Due',
            'description': 'Notification when asset review is due',
            'subject_template': 'Asset Review Due: {{asset_name}}',
            'body_template_html': '''
            <html>
            <body>
                <p>Dear {{user_name}},</p>
                <p>The following asset requires review:</p>
                <ul>
                    <li><strong>Asset:</strong> {{asset_name}}</li>
                    <li><strong>Site:</strong> {{site_name}}</li>
                    <li><strong>Last Review:</strong> {{last_review_date}}</li>
                    <li><strong>Days Until Review:</strong> {{days_until_review}}</li>
                </ul>
                <p><a href="{{asset_url}}">Review Asset</a></p>
                <p>Best regards,<br>Industrace</p>
            </body>
            </html>
            ''',
            'body_template_text': '''
            Dear {{user_name}},
            
            The following asset requires review:
            - Asset: {{asset_name}}
            - Site: {{site_name}}
            - Last Review: {{last_review_date}}
            - Days Until Review: {{days_until_review}}
            
            Review Asset: {{asset_url}}
            
            Best regards,
            Industrace
            ''',
            'variables': ['user_name', 'asset_name', 'site_name', 'last_review_date', 'days_until_review', 'asset_url']
        },
        {
            'template_code': 'asset_review_overdue',
            'name': 'Asset Review Overdue',
            'description': 'Notification when asset review is overdue',
            'subject_template': 'Asset Review Overdue: {{asset_name}}',
            'body_template_html': '''
            <html>
            <body>
                <p>Dear {{user_name}},</p>
                <p><strong>URGENT:</strong> The following asset has an overdue review:</p>
                <ul>
                    <li><strong>Asset:</strong> {{asset_name}}</li>
                    <li><strong>Site:</strong> {{site_name}}</li>
                    <li><strong>Last Review:</strong> {{last_review_date}}</li>
                    <li><strong>Days Overdue:</strong> {{days_overdue}}</li>
                </ul>
                <p><a href="{{asset_url}}">Review Asset Now</a></p>
                <p>Best regards,<br>Industrace</p>
            </body>
            </html>
            ''',
            'body_template_text': '''
            Dear {{user_name}},
            
            URGENT: The following asset has an overdue review:
            - Asset: {{asset_name}}
            - Site: {{site_name}}
            - Last Review: {{last_review_date}}
            - Days Overdue: {{days_overdue}}
            
            Review Asset Now: {{asset_url}}
            
            Best regards,
            Industrace
            ''',
            'variables': ['user_name', 'asset_name', 'site_name', 'last_review_date', 'days_overdue', 'asset_url']
        },
        {
            'template_code': 'risk_alert',
            'name': 'High Risk Alert',
            'description': 'Notification when asset has high risk score',
            'subject_template': 'High Risk Alert: {{asset_name}} (Risk Score: {{risk_score}})',
            'body_template_html': '''
            <html>
            <body>
                <p>Dear {{user_name}},</p>
                <p>The following asset has a high risk score:</p>
                <ul>
                    <li><strong>Asset:</strong> {{asset_name}}</li>
                    <li><strong>Risk Score:</strong> {{risk_score}} ({{risk_level}})</li>
                    <li><strong>Site:</strong> {{site_name}}</li>
                </ul>
                <p><a href="{{asset_url}}">View Asset Details</a></p>
                <p>Best regards,<br>Industrace</p>
            </body>
            </html>
            ''',
            'body_template_text': '''
            Dear {{user_name}},
            
            The following asset has a high risk score:
            - Asset: {{asset_name}}
            - Risk Score: {{risk_score}} ({{risk_level}})
            - Site: {{site_name}}
            
            View Asset Details: {{asset_url}}
            
            Best regards,
            Industrace
            ''',
            'variables': ['user_name', 'asset_name', 'risk_score', 'risk_level', 'site_name', 'asset_url']
        }
    ]
    
    created_count = 0
    for template_data in templates:
        # Check if template already exists
        existing = (
            db.query(NotificationTemplate)
            .filter(NotificationTemplate.template_code == template_data['template_code'])
            .first()
        )
        
        if not existing:
            template = NotificationTemplate(
                id=uuid.uuid4(),
                tenant_id=None,  # System-wide
                **template_data
            )
            db.add(template)
            created_count += 1
        else:
            # Update existing template
            for key, value in template_data.items():
                setattr(existing, key, value)
    
    db.commit()
    return created_count


if __name__ == "__main__":
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        count = init_notification_templates(db)
        print(f"Created {count} notification templates")
    finally:
        db.close()

