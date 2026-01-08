"""
Servizio per calcolare l'Overall Exposure Score
Calcola un punteggio composito (0-10) basato su:
- Assets at Risk
- Critical Assets
- High-Risk Vulnerabilities
- Missing Critical Dependencies
"""
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_


class ExposureCalculator:
    """Calcola l'Overall Exposure Score per un tenant"""
    
    @staticmethod
    def calculate_exposure_score(
        db: Session,
        tenant_id
    ) -> Dict[str, Any]:
        """
        Calcola l'Overall Exposure Score e le metriche aggregate
        
        Returns:
            Dict con:
            - overall_exposure_score: float (0-10)
            - assets_at_risk: int
            - critical_assets: int
            - high_risk_vulnerabilities: int (Critical + High unpatched)
            - missing_critical_dependencies: int
        """
        from app.models import Asset, Vulnerability, AssetVulnerability
        from app.models.asset_connection import AssetConnection
        from app.services.connection_dependency_analyzer import ConnectionDependencyAnalyzer
        
        # 1. Assets at Risk (risk_score >= 5)
        assets_at_risk = (
            db.query(func.count(Asset.id))
            .filter(
                and_(
                    Asset.tenant_id == tenant_id,
                    Asset.deleted_at == None,
                    Asset.risk_score >= 5
                )
            )
            .scalar()
        ) or 0
        
        # 2. Critical Assets
        critical_assets = (
            db.query(func.count(Asset.id))
            .filter(
                and_(
                    Asset.tenant_id == tenant_id,
                    Asset.deleted_at == None,
                    Asset.business_criticality.in_(['critical', 'high'])
                )
            )
            .scalar()
        ) or 0
        
        # 3. High-Risk Vulnerabilities (Critical + High unpatched - only unreviewed and acknowledged)
        high_risk_vulnerabilities = (
            db.query(func.count(AssetVulnerability.id))
            .join(Vulnerability, AssetVulnerability.vulnerability_id == Vulnerability.id)
            .filter(
                and_(
                    AssetVulnerability.tenant_id == tenant_id,
                    AssetVulnerability.status.in_(["unreviewed", "acknowledged"]),  # Only active vulnerabilities
                    Vulnerability.severity.in_(["critical", "high"])
                )
            )
            .scalar()
        ) or 0
        
        # 3b. Assets with Critical/High Vulnerabilities (distinct count)
        assets_with_critical_vulns = (
            db.query(func.count(func.distinct(AssetVulnerability.asset_id)))
            .join(Vulnerability, AssetVulnerability.vulnerability_id == Vulnerability.id)
            .filter(
                and_(
                    AssetVulnerability.tenant_id == tenant_id,
                    AssetVulnerability.status.in_(["unreviewed", "acknowledged"]),
                    Vulnerability.severity.in_(["critical", "high"])
                )
            )
            .scalar()
        ) or 0
        
        # 4. Missing Critical Dependencies
        connections = (
            db.query(AssetConnection)
            .filter(AssetConnection.tenant_id == tenant_id)
            .all()
        )
        
        missing_critical_dependencies = 0
        for conn in connections:
            status = ConnectionDependencyAnalyzer.get_connection_dependency_status(db, conn)
            if status.get('status') == 'missing' and status.get('severity') == 'critical':
                missing_critical_dependencies += 1
        
        # 5. Total Assets (per normalizzazione)
        total_assets = (
            db.query(func.count(Asset.id))
            .filter(
                and_(
                    Asset.tenant_id == tenant_id,
                    Asset.deleted_at == None
                )
            )
            .scalar()
        ) or 1  # Evita divisione per zero
        
        # Calcola Overall Exposure Score (0-10)
        # Media pesata normalizzata
        weights = {
            'assets_at_risk': 0.3,
            'critical_assets': 0.3,
            'high_risk_vulnerabilities': 0.2,
            'missing_critical_dependencies': 0.2
        }
        
        # Normalizza i valori rispetto al total_assets
        normalized_assets_at_risk = min((assets_at_risk / total_assets) * 10, 10)
        normalized_critical_assets = min((critical_assets / total_assets) * 10, 10)
        # Per le vulnerabilità, usiamo un limite ragionevole (es. 100 = 10 punti)
        normalized_vulnerabilities = min((high_risk_vulnerabilities / 100) * 10, 10)
        # Per le dipendenze critiche, usiamo un limite ragionevole (es. 50 = 10 punti)
        normalized_dependencies = min((missing_critical_dependencies / 50) * 10, 10)
        
        # Calcola media pesata
        overall_exposure_score = (
            normalized_assets_at_risk * weights['assets_at_risk'] +
            normalized_critical_assets * weights['critical_assets'] +
            normalized_vulnerabilities * weights['high_risk_vulnerabilities'] +
            normalized_dependencies * weights['missing_critical_dependencies']
        )
        
        # Arrotonda a 1 decimale
        overall_exposure_score = round(overall_exposure_score, 1)
        
        return {
            "overall_exposure_score": overall_exposure_score,
            "assets_at_risk": assets_at_risk,
            "critical_assets": critical_assets,
            "high_risk_vulnerabilities": high_risk_vulnerabilities,
            "assets_with_critical_vulns": assets_with_critical_vulns,
            "missing_critical_dependencies": missing_critical_dependencies,
            "total_assets": total_assets
        }

