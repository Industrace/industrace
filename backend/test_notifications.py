#!/usr/bin/env python3
"""
Script di test per verificare il sistema di notifiche end-to-end.
Verifica:
1. Template disponibili
2. Configurazione SMTP
3. Creazione di una notifica nella queue
4. Processamento della queue
5. Invio email
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import (
    NotificationTemplate,
    NotificationPreference,
    NotificationQueue,
    NotificationLog,
    TenantSMTPConfig,
    User,
    Tenant,
    Asset
)
from app.services.notification_service import NotificationService
from app.services.email_queue_processor import EmailQueueProcessor
import uuid
from datetime import datetime

def test_notification_system():
    """Test completo del sistema di notifiche"""
    db: Session = SessionLocal()
    
    try:
        print("=" * 60)
        print("TEST SISTEMA DI NOTIFICHE")
        print("=" * 60)
        
        # 1. Verifica tenant e utente
        print("\n1. Verifica tenant e utente...")
        tenant = db.query(Tenant).first()
        if not tenant:
            print("   ❌ Nessun tenant trovato!")
            return False
        print(f"   ✅ Tenant trovato: {tenant.name} (ID: {tenant.id})")
        
        user = db.query(User).filter(User.tenant_id == tenant.id).first()
        if not user:
            print("   ❌ Nessun utente trovato!")
            return False
        print(f"   ✅ Utente trovato: {user.email} (ID: {user.id})")
        
        # 2. Verifica template
        print("\n2. Verifica template di notifica...")
        templates = (
            db.query(NotificationTemplate)
            .filter(
                NotificationTemplate.enabled == True,
                (NotificationTemplate.tenant_id == tenant.id) | 
                (NotificationTemplate.tenant_id.is_(None))
            )
            .all()
        )
        if not templates:
            print("   ❌ Nessun template trovato!")
            print("   💡 Esegui l'inizializzazione dei template (init_notification_templates)")
            return False
        print(f"   ✅ Trovati {len(templates)} template:")
        for t in templates:
            print(f"      - {t.template_code}: {t.name}")
        
        # 3. Verifica configurazione SMTP
        print("\n3. Verifica configurazione SMTP...")
        smtp_config = (
            db.query(TenantSMTPConfig)
            .filter(TenantSMTPConfig.tenant_id == tenant.id)
            .first()
        )
        if not smtp_config:
            print("   ❌ Nessuna configurazione SMTP trovata!")
            print("\n   📋 PER CONFIGURARE SMTP:")
            print("      1. Vai alla pagina Setup (/setup)")
            print("      2. Clicca su 'Configura SMTP'")
            print("      3. Inserisci i dati del tuo server SMTP:")
            print("         - Host: es. smtp.gmail.com, smtp.office365.com")
            print("         - Porta: es. 587 (TLS) o 465 (SSL)")
            print("         - Username: la tua email")
            print("         - Password: password o app password")
            print("         - From Email: email mittente")
            print("      4. Clicca 'Testa Connessione' per verificare")
            print("      5. Salva la configurazione")
            print("\n   💡 Esempi di configurazione:")
            print("      Gmail: smtp.gmail.com:587 (usa App Password)")
            print("      Office365: smtp.office365.com:587")
            print("      SendGrid: smtp.sendgrid.net:587")
            return False
        if not smtp_config.host:
            print("   ❌ Configurazione SMTP incompleta (manca host)")
            print("   💡 Completa la configurazione nella pagina Setup")
            return False
        print(f"   ✅ SMTP configurato:")
        print(f"      - Host: {smtp_config.host}")
        print(f"      - Port: {smtp_config.port}")
        print(f"      - From: {smtp_config.from_email}")
        print(f"      - TLS: {smtp_config.use_tls}")
        print(f"      - Provider: {smtp_config.provider or 'smtp'}")
        
        # Test connessione SMTP
        print("\n   🔍 Test connessione SMTP...")
        try:
            from app.services.email_service import EmailConfig, EmailProvider, send_email
            email_config = EmailConfig(
                provider=EmailProvider(smtp_config.provider or "smtp"),
                smtp_host=smtp_config.host,
                smtp_port=smtp_config.port,
                smtp_username=smtp_config.username,
                smtp_password=smtp_config.password,
                smtp_use_tls=smtp_config.use_tls,
                from_email=smtp_config.from_email
            )
            # Test invio (senza inviare realmente, solo connessione)
            print("      ⚠️  Nota: Il test completo richiede l'invio di un'email")
            print("      💡 Usa il pulsante 'Testa Connessione' nella pagina Setup")
        except Exception as e:
            print(f"      ⚠️  Errore nella configurazione: {e}")
        
        # 4. Verifica preferenze utente
        print("\n4. Verifica preferenze utente...")
        preferences = (
            db.query(NotificationPreference)
            .filter(NotificationPreference.user_id == user.id)
            .all()
        )
        if not preferences:
            print("   ⚠️  Nessuna preferenza configurata per l'utente")
            print("   💡 Configura le preferenze nella pagina Notifiche")
        else:
            print(f"   ✅ Trovate {len(preferences)} preferenze:")
            for p in preferences:
                print(f"      - {p.notification_type}: email={p.email_enabled}, in_app={p.in_app_enabled}")
        
        # 5. Test creazione notifica nella queue
        print("\n5. Test creazione notifica nella queue...")
        test_template_code = templates[0].template_code
        context = {
            'user_name': user.name or 'Test User',
            'asset_name': 'Test Asset',
            'site_name': 'Test Site',
            'last_review_date': '2025-01-01',
            'days_until_review': 30,
            'days_overdue': 0,
            'risk_score': 8.5,
            'risk_level': 'high',
            'asset_url': '/assets/test-id'
        }
        
        try:
            queue_entry = NotificationService.send_notification(
                db, user.id, test_template_code, context
            )
            if queue_entry:
                print(f"   ✅ Notifica creata nella queue (ID: {queue_entry.id})")
                print(f"      - Tipo: {queue_entry.notification_type}")
                print(f"      - Destinatario: {queue_entry.email}")
                print(f"      - Oggetto: {queue_entry.subject[:50]}...")
                print(f"      - Stato: {queue_entry.status}")
            else:
                print("   ⚠️  Notifica non creata (probabilmente disabilitata nelle preferenze)")
        except Exception as e:
            print(f"   ❌ Errore nella creazione della notifica: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # 6. Test processamento queue
        print("\n6. Test processamento queue...")
        pending_count = (
            db.query(NotificationQueue)
            .filter(
                NotificationQueue.status == 'pending',
                NotificationQueue.tenant_id == tenant.id
            )
            .count()
        )
        print(f"   📊 Notifiche in attesa: {pending_count}")
        
        if pending_count > 0:
            try:
                stats = EmailQueueProcessor.process_queue(db, batch_size=10)
                print(f"   ✅ Queue processata:")
                print(f"      - Inviate: {stats.get('sent', 0)}")
                print(f"      - Fallite: {stats.get('failed', 0)}")
                print(f"      - Saltate: {stats.get('skipped', 0)}")
                
                # Verifica log
                recent_logs = (
                    db.query(NotificationLog)
                    .filter(NotificationLog.tenant_id == tenant.id)
                    .order_by(NotificationLog.created_at.desc())
                    .limit(5)
                    .all()
                )
                if recent_logs:
                    print(f"\n   📋 Ultimi {len(recent_logs)} log:")
                    for log in recent_logs:
                        status_icon = "✅" if log.status == 'sent' else "❌"
                        print(f"      {status_icon} {log.notification_type} - {log.status}")
                        if log.error_message:
                            print(f"         Errore: {log.error_message[:100]}")
            except Exception as e:
                print(f"   ❌ Errore nel processamento della queue: {e}")
                import traceback
                traceback.print_exc()
                return False
        else:
            print("   ⚠️  Nessuna notifica in attesa da processare")
        
        # 7. Verifica finale
        print("\n7. Verifica finale...")
        failed_count = (
            db.query(NotificationQueue)
            .filter(
                NotificationQueue.status == 'failed',
                NotificationQueue.tenant_id == tenant.id,
                NotificationQueue.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0)
            )
            .count()
        )
        
        if failed_count > 0:
            print(f"   ⚠️  {failed_count} notifiche fallite oggi")
            failed = (
                db.query(NotificationQueue)
                .filter(
                    NotificationQueue.status == 'failed',
                    NotificationQueue.tenant_id == tenant.id
                )
                .order_by(NotificationQueue.created_at.desc())
                .limit(3)
                .all()
            )
            for f in failed:
                print(f"      - {f.notification_type}: {f.error_message[:100] if f.error_message else 'Unknown error'}")
        else:
            print("   ✅ Nessuna notifica fallita oggi")
        
        print("\n" + "=" * 60)
        print("TEST COMPLETATO")
        print("=" * 60)
        print("\n💡 Se le notifiche non vengono inviate:")
        print("   1. Verifica la configurazione SMTP nella sezione Setup")
        print("   2. Verifica che l'SMTP sia verificato/testato")
        print("   3. Controlla i log del backend per errori dettagliati")
        print("   4. Verifica le preferenze utente nella pagina Notifiche")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Errore durante il test: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_notification_system()
    sys.exit(0 if success else 1)

