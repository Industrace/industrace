#!/usr/bin/env python3
"""
Script per inizializzare manualmente le Security Capabilities.
Può essere eseguito direttamente o tramite Docker.
"""
import sys
import os

# Aggiungi il path del backend al PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
        print(f"✅ Inizializzazione completata! ({count} capability create)")
    except Exception as e:
        print(f"❌ Errore durante l'inizializzazione: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

