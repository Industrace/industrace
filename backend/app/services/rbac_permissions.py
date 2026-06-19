"""
Definizione completa delle sezioni di permessi RBAC per Industrace

Questo modulo definisce tutte le sezioni di permessi disponibili nel sistema,
incluse quelle per le nuove funzionalità: vulnerabilità, review asset, dipendenze,
compliance ISA62443, security zones, notifiche e SSO.
"""

# Sezioni esistenti (mantenute per compatibilità)
EXISTING_SECTIONS = [
    "assets",
    "sites",
    "areas",
    "locations",
    "suppliers",
    "contacts",
    "manufacturers",
    "asset_types",
    "asset_statuses",
    "users",
    "roles",
    "audit_logs",
    "external_log",
    "utility",
    "asset_documents",
    "asset_photos",
    "locations_floormap",
    "reset_user_password",
]

# Nuove sezioni per le funzionalità aggiunte
NEW_SECTIONS = {
    "vulnerabilities": {
        "description": "Gestione vulnerabilità e CVE",
        "levels": {
            0: "Nessun accesso",
            1: "Visualizzare vulnerabilità e vulnerabilità asset",
            2: "Creare/modificare vulnerabilità, gestire status vulnerabilità asset",
            3: "Eliminare vulnerabilità, gestire feed di vulnerabilità",
            4: "Operazioni bulk su vulnerabilità"
        }
    },
    
    "asset_reviews": {
        "description": "Gestione review e manutenzione asset",
        "levels": {
            0: "Nessun accesso",
            1: "Visualizzare review status e asset in scadenza",
            2: "Marcare asset come reviewati, saltare review",
            3: "Ricalcolare tutte le date review, operazioni bulk",
            4: "Gestione completa review"
        }
    },
    
    "asset_dependencies": {
        "description": "Gestione dipendenze tra asset",
        "levels": {
            0: "Nessun accesso",
            1: "Visualizzare dipendenze tra asset",
            2: "Creare/modificare dipendenze",
            3: "Eliminare dipendenze",
            4: "Eseguire analisi avanzate (propagazione rischio, impact analysis)"
        }
    },
    
    "compliance": {
        "description": "Gestione compliance ISA/IEC 62443",
        "levels": {
            0: "Nessun accesso",
            1: "Visualizzare stato compliance, assessment SR",
            2: "Creare/modificare assessment SR, gestire evidence",
            3: "Gestire completamente compliance, zone, conduits, capabilities",
            4: "Amministrazione completa compliance"
        }
    },
    
    "security_zones": {
        "description": "Gestione security zones",
        "levels": {
            0: "Nessun accesso",
            1: "Visualizzare security zones e membership",
            2: "Creare/modificare zone, gestire membership asset",
            3: "Eliminare zone, calcolare security level",
            4: "Gestione completa zone e analisi rischio"
        }
    },
    
    "notifications": {
        "description": "Gestione notifiche e preferenze",
        "levels": {
            0: "Nessun accesso",
            1: "Visualizzare notifiche personali e log",
            2: "Gestire preferenze personali, inviare notifiche di test",
            3: "Gestire template notifiche, coda notifiche",
            4: "Amministrazione completa notifiche"
        }
    },
    
    "sso": {
        "description": "Gestione Single Sign-On",
        "levels": {
            0: "Nessun accesso",
            1: "Visualizzare configurazione SSO (solo se abilitato)",
            2: "Configurare SSO, testare connessione",
            3: "Importare utenti da provider SSO",
            4: "Amministrazione completa SSO"
        }
    },
    
    "api_keys": {
        "description": "Gestione API keys per integrazioni esterne",
        "levels": {
            0: "Nessun accesso",
            1: "Visualizzare API keys proprie",
            2: "Creare/modificare API keys proprie",
            3: "Eliminare API keys proprie, gestire tutte le API keys",
            4: "Amministrazione completa API keys"
        }
    },
    
    "evidence": {
        "description": "Gestione evidence per compliance",
        "levels": {
            0: "Nessun accesso",
            1: "Visualizzare evidence",
            2: "Creare/modificare evidence",
            3: "Eliminare evidence",
            4: "Gestione completa evidence"
        }
    },
    "external_log": {
        "description": "Configurazione inoltro audit log verso syslog esterno",
        "levels": {
            0: "Nessun accesso",
            1: "Visualizzare configurazione syslog",
            2: "Configurare server syslog, testare connessione",
            3: "Gestione completa external log",
            4: "Amministrazione completa"
        }
    },
    "network_probes": {
        "description": "Gestione sonde di rete e dispositivi scoperti",
        "levels": {
            0: "Nessun accesso",
            1: "Visualizzare sonde e dispositivi scoperti",
            2: "Modificare configurazione sonde",
            3: "Creare/eliminare/de-autorizzare sonde",
            4: "Amministrazione completa sonde"
        }
    }
}

# Tutte le sezioni complete
ALL_SECTIONS = EXISTING_SECTIONS + list(NEW_SECTIONS.keys())

# Permessi di default per ruolo admin (tutti i permessi)
ADMIN_DEFAULT_PERMISSIONS = {
    # Esistenti
    "assets": 3,
    "sites": 3,
    "areas": 3,
    "locations": 3,
    "suppliers": 3,
    "contacts": 3,
    "manufacturers": 3,
    "asset_types": 3,
    "asset_statuses": 3,
    "users": 3,
    "roles": 3,
    "audit_logs": 3,
    "external_log": 3,
    "utility": 3,
    "asset_documents": 3,
    "asset_photos": 3,
    "locations_floormap": 3,
    "reset_user_password": 1,
    
    # Nuove funzionalità
    "vulnerabilities": 3,
    "asset_reviews": 3,
    "asset_dependencies": 3,
    "compliance": 3,
    "security_zones": 3,
    "notifications": 3,
    "sso": 3,
    "api_keys": 3,
    "evidence": 3,
    "network_probes": 3,
}

# Permessi di default per ruolo editor
EDITOR_DEFAULT_PERMISSIONS = {
    # Esistenti
    "assets": 2,
    "sites": 2,
    "areas": 2,
    "locations": 2,
    "suppliers": 2,
    "contacts": 2,
    "manufacturers": 2,
    "asset_types": 2,
    "asset_statuses": 2,
    "users": 1,
    "roles": 1,
    "audit_logs": 1,
    "external_log": 1,
    "utility": 2,
    "asset_documents": 2,
    "asset_photos": 2,
    "locations_floormap": 2,
    
    # Nuove funzionalità - Editor può gestire operativamente ma non configurare
    "vulnerabilities": 2,  # Può gestire vulnerabilità asset ma non feed
    "asset_reviews": 2,  # Può marcare review ma non ricalcolare tutte
    "asset_dependencies": 2,  # Può gestire dipendenze
    "compliance": 1,  # Può visualizzare ma non creare assessment
    "security_zones": 1,  # Può visualizzare ma non modificare zone
    "notifications": 1,  # Può vedere e gestire preferenze personali
    "sso": 0,  # Non può configurare SSO
    "api_keys": 0,  # Non può gestire API keys
    "evidence": 2,  # Può gestire evidence
    "network_probes": 1,
}

# Permessi di default per ruolo viewer (solo lettura)
VIEWER_DEFAULT_PERMISSIONS = {
    # Esistenti
    "assets": 1,
    "sites": 1,
    "areas": 1,
    "locations": 1,
    "suppliers": 1,
    "contacts": 1,
    "manufacturers": 1,
    "asset_types": 1,
    "asset_statuses": 1,
    "users": 0,
    "roles": 1,
    "audit_logs": 1,
    "external_log": 0,
    "utility": 1,
    "asset_documents": 1,
    "asset_photos": 1,
    "locations_floormap": 1,
    
    # Nuove funzionalità - Viewer solo lettura
    "vulnerabilities": 1,
    "asset_reviews": 1,
    "asset_dependencies": 1,
    "compliance": 1,
    "security_zones": 1,
    "notifications": 1,  # Può vedere notifiche personali
    "sso": 0,
    "api_keys": 0,
    "evidence": 1,
    "network_probes": 1,
}
