# backend/app/services/email_service.py
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from enum import Enum
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class EmailProvider(str, Enum):
    SENDGRID = "sendgrid"
    MAILGUN = "mailgun"
    AWS_SES = "aws_ses"
    GMAIL_OAUTH2 = "gmail_oauth2"
    OFFICE365_OAUTH2 = "office365_oauth2"
    SMTP = "smtp"  # Fallback


class EmailConfig(BaseModel):
    provider: EmailProvider
    api_key: Optional[str] = None
    domain: Optional[str] = None
    region: Optional[str] = None
    from_email: str
    credentials: Optional[Dict[str, Any]] = None
    # SMTP fallback
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True


class EmailService(ABC):
    @abstractmethod
    def send_email(self, to_email: str, subject: str, content: str, html_content: Optional[str] = None) -> bool:
        pass


class SendGridService(EmailService):
    def __init__(self, config: EmailConfig):
        self.api_key = config.api_key
        self.from_email = config.from_email
        
    def send_email(self, to_email: str, subject: str, content: str, html_content: Optional[str] = None) -> bool:
        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail, Email, To, Content
            
            sg = sendgrid.SendGridAPIClient(api_key=self.api_key)
            from_email = Email(self.from_email)
            to_email_obj = To(to_email)
            
            if html_content:
                mail = Mail(from_email, to_email_obj, subject, Content("text/plain", content))
                mail.add_content(Content("text/html", html_content))
            else:
                mail = Mail(from_email, to_email_obj, subject, Content("text/plain", content))
            
            response = sg.send(mail)
            return response.status_code == 202
        except Exception as e:
            logger.error(f"SendGrid error: {e}")
            return False


class MailgunService(EmailService):
    def __init__(self, config: EmailConfig):
        self.api_key = config.api_key
        self.domain = config.domain
        self.from_email = config.from_email
        
    def send_email(self, to_email: str, subject: str, content: str, html_content: Optional[str] = None) -> bool:
        try:
            import requests
            
            url = f"https://api.mailgun.net/v3/{self.domain}/messages"
            auth = ("api", self.api_key)
            data = {
                "from": self.from_email,
                "to": to_email,
                "subject": subject,
                "text": content
            }
            if html_content:
                data["html"] = html_content
            response = requests.post(url, auth=auth, data=data)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Mailgun error: {e}")
            return False


class AWSSESService(EmailService):
    def __init__(self, config: EmailConfig):
        self.region = config.region or 'us-east-1'
        self.from_email = config.from_email
        
    def send_email(self, to_email: str, subject: str, content: str, html_content: Optional[str] = None) -> bool:
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            ses = boto3.client('ses', region_name=self.region)
            message_body = {'Text': {'Data': content}}
            if html_content:
                message_body['Html'] = {'Data': html_content}
            
            response = ses.send_email(
                Source=self.from_email,
                Destination={'ToAddresses': [to_email]},
                Message={
                    'Subject': {'Data': subject},
                    'Body': message_body
                }
            )
            return True
        except Exception as e:
            logger.error(f"AWS SES error: {e}")
            return False


class GmailOAuth2Service(EmailService):
    def __init__(self, config: EmailConfig):
        self.credentials = config.credentials
        self.from_email = config.from_email
        
    def send_email(self, to_email: str, subject: str, content: str, html_content: Optional[str] = None) -> bool:
        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            import base64
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from googleapiclient.discovery import build
            
            creds = Credentials(**self.credentials)
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                
            service = build('gmail', 'v1', credentials=creds)
            
            if html_content:
                message = MIMEMultipart('alternative')
                message['to'] = to_email
                message['subject'] = subject
                message.attach(MIMEText(content, 'plain'))
                message.attach(MIMEText(html_content, 'html'))
            else:
                message = MIMEText(content)
                message['to'] = to_email
                message['subject'] = subject
            
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            service.users().messages().send(userId='me', body={'raw': raw}).execute()
            return True
        except Exception as e:
            logger.error(f"Gmail OAuth2 error: {e}")
            return False


class SMTPFallbackService(EmailService):
    def __init__(self, config: EmailConfig):
        self.host = config.smtp_host
        self.port = config.smtp_port
        self.username = config.smtp_username
        self.password = config.smtp_password
        self.use_tls = config.smtp_use_tls
        self.from_email = config.from_email
        
    def send_email(self, to_email: str, subject: str, content: str, html_content: Optional[str] = None) -> bool:
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            if html_content:
                msg = MIMEMultipart('alternative')
                msg["Subject"] = subject
                msg["From"] = self.from_email
                msg["To"] = to_email
                msg.attach(MIMEText(content, 'plain'))
                msg.attach(MIMEText(html_content, 'html'))
            else:
                msg = MIMEText(content)
                msg["Subject"] = subject
                msg["From"] = self.from_email
                msg["To"] = to_email
            
            with smtplib.SMTP(self.host, self.port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            return True
        except Exception as e:
            logger.error(f"SMTP error: {e}")
            return False


class EmailServiceFactory:
    @staticmethod
    def create_service(config: EmailConfig) -> EmailService:
        if config.provider == EmailProvider.SENDGRID:
            return SendGridService(config)
        elif config.provider == EmailProvider.MAILGUN:
            return MailgunService(config)
        elif config.provider == EmailProvider.AWS_SES:
            return AWSSESService(config)
        elif config.provider == EmailProvider.GMAIL_OAUTH2:
            return GmailOAuth2Service(config)
        elif config.provider == EmailProvider.SMTP:
            return SMTPFallbackService(config)
        else:
            raise ValueError(f"Unsupported email provider: {config.provider}")


# Funzione di utilità per inviare email
def send_email(to_email: str, subject: str, content: str, config: EmailConfig, html_content: Optional[str] = None) -> bool:
    """
    Invia email usando il provider configurato
    """
    try:
        service = EmailServiceFactory.create_service(config)
        return service.send_email(to_email, subject, content, html_content)
    except Exception as e:
        logger.error(f"Email service error: {e}")
        return False


# Funzione specifica per reset password
def send_password_reset_email(to_email: str, temp_password: str, config: EmailConfig) -> bool:
    """
    Invia email di reset password
    """
    subject = "Industrace - Password Reset"
    content = f"""
    La tua password è stata reimpostata.
    
    Password temporanea: {temp_password}
    
    Per favore accedi e cambia la password al primo accesso.
    
    Se non hai richiesto questo reset, contatta l'amministratore.
    """
    
    return send_email(to_email, subject, content, config) 