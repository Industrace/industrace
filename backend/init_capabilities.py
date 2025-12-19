#!/usr/bin/env python3
"""
Script per inizializzare manualmente le Security Capabilities.
Eseguire con: python init_capabilities.py
Oppure nel container Docker: docker-compose exec backend python /app/init_capabilities.py
"""
from app.database import SessionLocal
from app.init_data.init_security_capabilities import init_security_capabilities


def main():
    """Inizializza le Security Capabilities"""
    print("🔐 Inizializzazione Security Capabilities...")
    print("-" * 60)
    
    db = SessionLocal()
    try:
        count = init_security_capabilities(db)
        print("-" * 60)
        if count > 0:
            print(f"✅ Inizializzazione completata! ({count} capability create)")
        else:
            print("ℹ️  Tutte le capability erano già presenti nel database.")
    except Exception as e:
        print(f"❌ Errore durante l'inizializzazione: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()
    
    return 0


if __name__ == "__main__":
    exit(main())

