#!/usr/bin/env python3
"""
Script per inizializzare manualmente i mapping SR-Capability.
Eseguire con: python init_sr_mappings.py
Oppure nel container Docker: docker-compose exec backend python /app/init_sr_mappings.py
"""
from app.database import SessionLocal
from app.init_data.init_sr_capability_mappings import init_sr_capability_mappings


def main():
    """Inizializza i mapping SR-Capability"""
    print("🔗 Inizializzazione SR-Capability mappings...")
    print("-" * 60)
    
    db = SessionLocal()
    try:
        count = init_sr_capability_mappings(db)
        print("-" * 60)
        if count > 0:
            print(f"✅ Inizializzazione completata! ({count} mapping creati)")
        else:
            print("ℹ️  Tutti i mapping erano già presenti nel database.")
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

