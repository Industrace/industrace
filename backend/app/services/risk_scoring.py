# backend/app/services/risk_scoring.py
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session


class CompositeRiskScoringEngine:
    """
    Calcolo risk score composito per asset industriali:
    - Vulnerabilità (35%)
    - Impatto (40%)
    - Operativo (25%)
    Breakdown dettagliato, gestione dati mancanti, suggerimenti punti deboli.
    """

    VULN_WEIGHT = 0.35
    IMPACT_WEIGHT = 0.40
    OPER_WEIGHT = 0.25

    TRANSLATIONS = {
        "en": {
            "remote_access_enabled": "Remote access enabled (+2)",
            "remote_access_unattended": "Unattended remote access (+2)",
            "physical_access_easy": "Easy physical access (+3)",
            "physical_access_medium": "Medium physical access (+1)",
            "purdue_low_high_connection": "Low Purdue level connected to high levels (+3)",
            "connections_count": "{n} connections (+{add})",
            "business_criticality": "Business criticality: {crit} ({score})",
            "purdue_low": "Low Purdue (+2)",
            "missing_business_criticality": "Missing business criticality: cannot calculate risk.",
            "suggest_disable_remote": "Disable remote access if not needed.",
            "suggest_avoid_unattended": "Avoid unattended remote access.",
            "suggest_harden_physical": "Make physical access harder.",
            "suggest_isolate_purdue": "Isolate low Purdue level assets from high levels.",
            "suggest_reduce_connections": "Reduce unnecessary connections.",
            "suggest_set_criticality": "Set business criticality for accurate calculation.",
            "critical_dependencies": "Critical dependencies (+{adj})",
            "isa62443_sl_gap": "Security Level gap: SL-T{sl_t} vs SL-A{sl_a} (+{penalty})",
            "isa62443_non_compliant": "ISA/IEC 62443 non-compliant (+2.0)",
            "isa62443_partial": "ISA/IEC 62443 partially compliant (+1.0)",
            "suggest_improve_compliance": "Improve ISA/IEC 62443 compliance to reduce risk.",
            "suggest_reach_target_sl": "Reach target Security Level to reduce risk.",
            "critical_vulnerabilities": "{n} critical vulnerabilities (+3)",
            "high_vulnerabilities": "{n} high severity vulnerabilities (+2)",
            "high_cvss_score": "High CVSS score ({score}) (+2)",
            "medium_cvss_score": "Medium CVSS score ({score}) (+1)",
        },
        "it": {
            "remote_access_enabled": "Accesso remoto abilitato (+2)",
            "remote_access_unattended": "Accesso remoto unattended (+2)",
            "physical_access_easy": "Accesso fisico facile (+3)",
            "physical_access_medium": "Accesso fisico medio (+1)",
            "purdue_low_high_connection": "Livello Purdue basso connesso a livelli alti (+3)",
            "connections_count": "{n} connessioni (+{add})",
            "business_criticality": "Criticità business: {crit} ({score})",
            "purdue_low": "Purdue basso (+2)",
            "missing_business_criticality": "Criticità business mancante: impossibile calcolare il rischio.",
            "suggest_disable_remote": "Disabilita l’accesso remoto se non necessario.",
            "suggest_avoid_unattended": "Evita accesso remoto unattended.",
            "suggest_harden_physical": "Rendi più difficile l’accesso fisico.",
            "suggest_isolate_purdue": "Isola asset di livello Purdue basso da livelli alti.",
            "suggest_reduce_connections": "Riduci il numero di connessioni non necessarie.",
            "suggest_set_criticality": "Imposta la criticità business per un calcolo accurato.",
            "critical_dependencies": "Dipendenze critiche (+{adj})",
            "isa62443_sl_gap": "Gap Security Level: SL-T{sl_t} vs SL-A{sl_a} (+{penalty})",
            "isa62443_non_compliant": "ISA/IEC 62443 non conforme (+2.0)",
            "isa62443_partial": "ISA/IEC 62443 parzialmente conforme (+1.0)",
            "suggest_improve_compliance": "Migliora la conformità ISA/IEC 62443 per ridurre il rischio.",
            "suggest_reach_target_sl": "Raggiungi il Security Level target per ridurre il rischio.",
            "critical_vulnerabilities": "{n} vulnerabilità critiche (+3)",
            "high_vulnerabilities": "{n} vulnerabilità ad alta severità (+2)",
            "high_cvss_score": "CVSS score alto ({score}) (+2)",
            "medium_cvss_score": "CVSS score medio ({score}) (+1)",
        },
    }

    CRIT_MAP = {"low": 2, "medium": 5, "high": 8, "critical": 10}
    CRIT_TRANSLATIONS = {
        "en": {
            "low": "low",
            "medium": "medium",
            "high": "high",
            "critical": "critical",
        },
        "it": {
            "low": "bassa",
            "medium": "media",
            "high": "alta",
            "critical": "critica",
        },
    }

    def calculate(self, asset, language="en") -> Dict[str, Any]:
        translations = self.TRANSLATIONS.get(language, self.TRANSLATIONS["en"])
        crit_trans = self.CRIT_TRANSLATIONS.get(language, self.CRIT_TRANSLATIONS["en"])
        missing = []
        suggestions = []
        # --- Vulnerabilities ---
        vuln_score = 1
        vuln_break = []
        # Accesso remoto
        if getattr(asset, "remote_access", None):
            vuln_score += 2
            vuln_break.append(translations["remote_access_enabled"])
            if getattr(asset, "remote_access_type", None) == "unattended":
                vuln_score += 2
                vuln_break.append(translations["remote_access_unattended"])
        # Physical access ease
        phys = getattr(asset, "physical_access_ease", None)
        if phys == "easy":
            vuln_score += 3
            vuln_break.append(translations["physical_access_easy"])
        elif phys == "medium":
            vuln_score += 1
            vuln_break.append(translations["physical_access_medium"])
        elif phys is None:
            missing.append("physical_access_ease")
        # Purdue "inappropriato"
        purdue = getattr(asset, "purdue_level", None)
        if purdue is not None:
            if purdue in [0, 1] and self._has_direct_high_level_connection(asset):
                vuln_score += 3
                vuln_break.append(translations["purdue_low_high_connection"])
        else:
            missing.append("purdue_level")
        # Numero connessioni
        n_conn = len(getattr(asset, "connections", []) or [])
        if n_conn:
            add_conn = n_conn // 5
            vuln_score += add_conn
            if add_conn:
                vuln_break.append(
                    translations["connections_count"].format(n=n_conn, add=add_conn)
                )
        
        # NOTE: Dipendenze critiche NON vengono aggiunte qui al rischio base
        # perché vengono calcolate e mostrate separatamente nell'endpoint /risk-from-dependencies
        # Questo evita doppia contabilizzazione e permette di vedere chiaramente:
        # - Rischio Base (senza dipendenze)
        # - Rischio da Dipendenze (aggiunto separatamente)
        # - Rischio Totale (limitato a 10.0)
        
        # Vulnerabilità (da vulnerability intelligence)
        vulnerability_adjustment = 0.0
        vulnerability_break = []
        if hasattr(asset, 'tenant_id') and hasattr(asset, 'id'):
            try:
                from app.crud import vulnerabilities as crud_vulns
                from app.database import SessionLocal
                db = SessionLocal()
                try:
                    unpatched_vulns = crud_vulns.get_unpatched_vulnerabilities(
                        db, asset.id, asset.tenant_id
                    )
                    if unpatched_vulns:
                        critical_vulns = [
                            v for v in unpatched_vulns
                            if v.vulnerability and v.vulnerability.severity == 'critical'
                        ]
                        high_vulns = [
                            v for v in unpatched_vulns
                            if v.vulnerability and v.vulnerability.severity == 'high'
                        ]
                        
                        if critical_vulns:
                            vulnerability_adjustment += 3
                            vulnerability_break.append(
                                translations.get("critical_vulnerabilities",
                                    f"{len(critical_vulns)} critical vulnerabilities (+3)"
                                ).format(n=len(critical_vulns))
                            )
                        
                        if high_vulns:
                            vulnerability_adjustment += 2
                            vulnerability_break.append(
                                translations.get("high_vulnerabilities",
                                    f"{len(high_vulns)} high severity vulnerabilities (+2)"
                                ).format(n=len(high_vulns))
                            )
                        
                        # CVSS score impact
                        cvss_scores = [
                            v.vulnerability.cvss_v3_score or v.vulnerability.cvss_v2_score or 0.0
                            for v in unpatched_vulns
                            if v.vulnerability
                        ]
                        if cvss_scores:
                            max_cvss = max(cvss_scores)
                            if max_cvss >= 9.0:
                                vulnerability_adjustment += 2
                                vulnerability_break.append(
                                translations.get("high_cvss_score",
                                    f"High CVSS score ({max_cvss:.1f}) (+2)"
                                ).format(score=f"{max_cvss:.1f}")
                                )
                            elif max_cvss >= 7.0:
                                vulnerability_adjustment += 1
                                vulnerability_break.append(
                                translations.get("medium_cvss_score",
                                    f"Medium CVSS score ({max_cvss:.1f}) (+1)"
                                ).format(score=f"{max_cvss:.1f}")
                                )
                        
                        vuln_score += vulnerability_adjustment
                        vuln_break.extend(vulnerability_break)
                finally:
                    db.close()
            except Exception:
                # Silently fail if vulnerabilities not available
                pass
        
        # ISA/IEC 62443 Compliance Penalties
        isa62443_adjustment = 0.0
        isa62443_break = []
        sl_gap = None
        
        # Check Security Level gap (SL-T vs SL-A)
        sl_t = getattr(asset, "security_level_target", None)
        sl_a = getattr(asset, "security_level_achieved", None)
        if sl_t is not None and sl_a is not None:
            sl_gap = sl_t - sl_a
            if sl_gap > 0:
                # Penalty: +1.5 per ogni livello di gap
                penalty = sl_gap * 1.5
                isa62443_adjustment += penalty
                isa62443_break.append(
                    translations.get("isa62443_sl_gap",
                        f"Security Level gap: SL-T{sl_t} vs SL-A{sl_a} (+{penalty:.1f})"
                    ).format(sl_t=sl_t, sl_a=sl_a, penalty=f"{penalty:.1f}")
                )
        
        # Check compliance status
        compliance_status = getattr(asset, "isa62443_compliance_status", None)
        if compliance_status:
            if compliance_status == "non_compliant":
                isa62443_adjustment += 2.0
                isa62443_break.append(
                    translations.get("isa62443_non_compliant",
                        "ISA/IEC 62443 non-compliant (+2.0)"
                    )
                )
            elif compliance_status == "partial":
                isa62443_adjustment += 1.0
                isa62443_break.append(
                    translations.get("isa62443_partial",
                        "ISA/IEC 62443 partially compliant (+1.0)"
                    )
                )
        
        # Apply ISA 62443 adjustment to vulnerability score
        if isa62443_adjustment > 0:
            vuln_score += isa62443_adjustment
            vuln_break.extend(isa62443_break)
        
        # TODO: connessioni a asset critici
        # --- Impatto ---
        imp_score = None
        imp_break = []
        crit = getattr(asset, "business_criticality", None)
        crit_map = self.CRIT_MAP
        crit_key = None
        if crit:
            crit_lower = str(crit).lower()
            for k in crit_map:
                if crit_lower == k or crit_lower == self.CRIT_TRANSLATIONS["it"].get(k):
                    crit_key = k
                    break
        if crit_key in crit_map:
            imp_score = crit_map[crit_key]
            imp_break.append(
                translations["business_criticality"].format(
                    crit=crit_trans[crit_key], score=imp_score
                )
            )
        else:
            missing.append("business_criticality")
        # Modifica per Purdue
        if purdue is not None and imp_score is not None:
            if purdue in [0, 1, 2]:
                imp_score += 2
                imp_break.append(translations["purdue_low"])
        # Dipendenze critiche (placeholder: nessuna logica, da implementare)
        # --- Operativo ---
        oper_score = imp_score
        oper_break = [*imp_break]
        # (puoi differenziare la logica operativa in futuro)
        # --- Normalizzazione ---
        vuln_score = min(10, max(1, vuln_score))
        if imp_score is not None:
            imp_score = min(10, max(1, imp_score))
        if oper_score is not None:
            oper_score = min(10, max(1, oper_score))
        # --- Calcolo finale ---
        if imp_score is None or oper_score is None:
            final_score = None
            suggestions.append(translations["missing_business_criticality"])
        else:
            final_score = round(
                self.VULN_WEIGHT * vuln_score
                + self.IMPACT_WEIGHT * imp_score
                + self.OPER_WEIGHT * oper_score,
                2,
            )
            # Cap final score at 10.0 (risk scale is 0-10)
            final_score = min(10.0, max(0.0, final_score))
        # --- Suggerimenti punti deboli ---
        if getattr(asset, "remote_access", None):
            suggestions.append(translations["suggest_disable_remote"])
        if getattr(asset, "remote_access_type", None) == "unattended":
            suggestions.append(translations["suggest_avoid_unattended"])
        if phys == "easy":
            suggestions.append(translations["suggest_harden_physical"])
        if purdue in [0, 1] and self._has_direct_high_level_connection(asset):
            suggestions.append(translations["suggest_isolate_purdue"])
        if n_conn > 10:
            suggestions.append(translations["suggest_reduce_connections"])
        if "business_criticality" in missing:
            suggestions.append(translations["suggest_set_criticality"])
        # ISA/IEC 62443 suggestions
        if isa62443_adjustment > 0:
            if compliance_status == "non_compliant":
                suggestions.append(translations.get("suggest_improve_compliance", "Improve ISA/IEC 62443 compliance to reduce risk."))
            if sl_gap and sl_gap > 0:
                suggestions.append(translations.get("suggest_reach_target_sl", "Reach target Security Level to reduce risk."))
        # --- Breakdown ---
        breakdown = {
            "vulnerability": {"score": vuln_score, "breakdown": vuln_break},
            "impact": {"score": imp_score, "breakdown": imp_break},
            "operational": {"score": oper_score, "breakdown": oper_break},
            "weights": {
                "vulnerability": self.VULN_WEIGHT,
                "impact": self.IMPACT_WEIGHT,
                "operational": self.OPER_WEIGHT,
            },
            "final_score": final_score,
            "missing_data": missing,
            "suggestions": suggestions,
        }
        return breakdown

    def _has_direct_high_level_connection(self, asset) -> bool:
        # Placeholder: implementa logica reale se hai info sulle connessioni
        # Es: controlla se asset.connections contiene asset con purdue_level >= 4
        return False
