# backend/app/services/zone_risk_calculator.py
from typing import Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models import SecurityZone, Asset, Conduit
from app.services.isa62443_compliance_engine import ISA62443ComplianceEngine
import logging

logger = logging.getLogger(__name__)


class ZoneRiskCalculator:
    """Calculate aggregated risk for Security Zones"""
    
    @staticmethod
    def calculate_zone_risk(
        db: Session,
        zone: SecurityZone
    ) -> Dict:
        """
        Calculate aggregated risk for a Security Zone.
        
        Factors:
        - Security Level gap (SL-T vs SL-A)
        - Non-compliance percentage
        - Asset risk scores in the zone
        - Conduit security
        - Isolation violations
        """
        # Get SL gap
        sl_t = zone.security_level_target
        sl_a = zone.security_level_achieved or ISA62443ComplianceEngine.calculate_zone_security_level_achieved(db, zone)
        sl_gap = (sl_t - sl_a) if (sl_t and sl_a) else None
        
        # Get assets in zone
        assets = (
            db.query(Asset)
            .filter(
                Asset.security_zone_id == zone.id,
                Asset.deleted_at.is_(None)
            )
            .all()
        )
        
        # Calculate average asset risk
        asset_risks = [asset.risk_score for asset in assets if asset.risk_score]
        avg_asset_risk = sum(asset_risks) / len(asset_risks) if asset_risks else 0.0
        
        # Get conduits
        conduits = (
            db.query(Conduit)
            .filter(
                and_(
                    Conduit.deleted_at.is_(None),
                    or_(
                        Conduit.from_zone_id == zone.id,
                        Conduit.to_zone_id == zone.id
                    )
                )
            )
            .all()
        )
        
        # Check for insecure conduits
        insecure_conduits = [
            c for c in conduits
            if not c.is_encrypted or not c.authentication_required
        ]
        
        # Calculate zone risk score (0-100)
        zone_risk = 0.0
        
        # SL gap contributes to risk
        if sl_gap:
            zone_risk += sl_gap * 10  # Each SL gap = +10 points
        
        # Non-compliance contributes
        if zone.compliance_status == 'non_compliant':
            zone_risk += 20
        elif zone.compliance_status == 'partial':
            zone_risk += 10
        
        # Asset risk contributes (weighted average)
        zone_risk += avg_asset_risk * 0.3  # 30% weight
        
        # Insecure conduits contribute
        zone_risk += len(insecure_conduits) * 5
        
        # Cap at 100
        zone_risk = min(100.0, zone_risk)
        
        # Detect isolation violations
        isolation_violations = ZoneRiskCalculator.detect_isolation_violations(db, zone)
        
        return {
            'zone_id': str(zone.id),
            'zone_name': zone.name,
            'security_level_target': sl_t,
            'security_level_achieved': sl_a,
            'security_level_gap': sl_gap,
            'compliance_status': zone.compliance_status,
            'zone_risk_score': round(zone_risk, 2),
            'asset_count': len(assets),
            'average_asset_risk': round(avg_asset_risk, 2),
            'conduit_count': len(conduits),
            'insecure_conduits_count': len(insecure_conduits),
            'isolation_violations': isolation_violations,
            'risk_factors': {
                'sl_gap': sl_gap if sl_gap else 0,
                'non_compliance': 20 if zone.compliance_status == 'non_compliant' else (10 if zone.compliance_status == 'partial' else 0),
                'asset_risk_contribution': round(avg_asset_risk * 0.3, 2),
                'insecure_conduits': len(insecure_conduits) * 5
            }
        }
    
    @staticmethod
    def detect_isolation_violations(
        db: Session,
        zone: SecurityZone
    ) -> List[Dict]:
        """
        Detect isolation violations for a zone.
        
        Violations:
        - Direct connections to zones with different SL without proper conduit
        - Unencrypted conduits between zones with high SL difference
        - Assets in zone connected to assets in lower SL zones
        """
        violations = []
        
        # Get conduits from/to this zone
        conduits = (
            db.query(Conduit)
            .filter(
                and_(
                    Conduit.deleted_at.is_(None),
                    or_(
                        Conduit.from_zone_id == zone.id,
                        Conduit.to_zone_id == zone.id
                    )
                )
            )
            .all()
        )
        
        zone_sl_t = zone.security_level_target or 0
        
        for conduit in conduits:
            # Get other zone
            if conduit.from_zone_id == zone.id:
                other_zone_id = conduit.to_zone_id
            else:
                other_zone_id = conduit.from_zone_id
            
            other_zone = db.query(SecurityZone).filter(SecurityZone.id == other_zone_id).first()
            if not other_zone:
                continue
            
            other_zone_sl_t = other_zone.security_level_target or 0
            
            # Check for SL mismatch without proper security
            if abs(zone_sl_t - other_zone_sl_t) >= 2:
                if not conduit.is_encrypted or not conduit.authentication_required:
                    violations.append({
                        'type': 'insecure_conduit_high_sl_gap',
                        'conduit_id': str(conduit.id),
                        'conduit_name': conduit.name,
                        'other_zone_id': str(other_zone.id),
                        'other_zone_name': other_zone.name,
                        'sl_gap': abs(zone_sl_t - other_zone_sl_t),
                        'severity': 'high'
                    })
            
            # Check for unencrypted conduits between zones
            if zone_sl_t >= 3 and not conduit.is_encrypted:
                violations.append({
                    'type': 'unencrypted_conduit_high_sl',
                    'conduit_id': str(conduit.id),
                    'conduit_name': conduit.name,
                    'other_zone_id': str(other_zone.id),
                    'other_zone_name': other_zone.name,
                    'severity': 'medium'
                })
        
        # Check for assets in zone connected to assets in lower SL zones
        assets_in_zone = (
            db.query(Asset)
            .filter(
                Asset.security_zone_id == zone.id,
                Asset.deleted_at.is_(None)
            )
            .all()
        )
        
        for asset in assets_in_zone:
            # Get connections (simplified - would need to check actual connections)
            # This is a placeholder for more detailed analysis
            pass
        
        return violations

