# backend/app/services/risk_propagation.py
from typing import Dict, List, Optional, Any, Set
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import uuid
from app.models.asset import Asset
from app.models.asset_dependency import AssetDependency
from app.crud.asset_dependencies import (
    get_asset_dependencies_as_dependent,
    get_asset_dependencies_as_dependency,
    get_dependency_chain,
    get_reverse_dependency_chain
)
from app.services.risk_cache import risk_cache


class RiskPropagationService:
    """
    Service per calcolare la propagazione del rischio attraverso le dipendenze tra asset.
    
    Funzionalità:
    - Calcolo risk propagation: come il rischio di un asset si propaga ad altri
    - Impact analysis: cosa succede se un asset fallisce
    - Dependency chain analysis: analisi delle catene di dipendenza
    - Risk score adjustment: aggiustamento del risk score basato su dipendenze critiche
    """
    
    CRITICALITY_WEIGHTS = {
        "low": 0.25,
        "medium": 0.50,
        "high": 0.75,
        "critical": 1.0
    }
    
    DEPENDENCY_TYPE_WEIGHTS = {
        "logical": 0.3,
        "functional": 0.5,
        "data_flow": 0.7,
        "control_flow": 0.9
    }
    
    CONFIDENCE_WEIGHTS = {
        "low": 0.5,      # Dipendenze incerte pesano meno
        "medium": 0.75,   # Dipendenze probabili pesano standard
        "high": 1.0      # Dipendenze certe pesano completo
    }
    
    @staticmethod
    def calculate_risk_propagation(
        db: Session,
        asset_id: uuid.UUID,
        tenant_id: uuid.UUID,
        max_depth: int = 5
    ) -> Dict[str, Any]:
        """
        Calcola come il rischio di un asset si propaga ad altri asset attraverso le dipendenze.
        
        Returns:
        {
            "source_asset_id": str,
            "source_asset_name": str,
            "source_risk_score": float,
            "propagated_risks": [
                {
                    "asset_id": str,
                    "asset_name": str,
                    "risk_score": float,
                    "propagated_risk_adjustment": float,
                    "dependency_path": [...],
                    "criticality": str
                }
            ],
            "total_affected_assets": int,
            "max_propagation_depth": int
        }
        """
        asset = db.query(Asset).filter(
            Asset.id == asset_id,
            Asset.tenant_id == tenant_id,
            Asset.deleted_at == None
        ).first()
        
        if not asset:
            raise ValueError(f"Asset {asset_id} not found")
        
        source_risk = asset.risk_score or 0.0
        
        # Get reverse dependency chain (what depends on this asset)
        dependency_chain = get_reverse_dependency_chain(
            db, asset_id, tenant_id, max_depth
        )
        
        propagated_risks = []
        visited_assets: Set[uuid.UUID] = {asset_id}
        
        for dep_info in dependency_chain:
            # from_asset_id is the asset that depends (receives the risk)
            # to_asset_id is the asset being depended on (propagates the risk)
            dep_asset_id = uuid.UUID(dep_info["from_asset_id"])
            
            if dep_asset_id in visited_assets:
                continue
            
            visited_assets.add(dep_asset_id)
            
            dep_asset = db.query(Asset).filter(
                Asset.id == dep_asset_id,
                Asset.tenant_id == tenant_id,
                Asset.deleted_at == None
            ).first()
            
            if not dep_asset:
                continue
            
            # Calculate propagated risk adjustment
            criticality_weight = RiskPropagationService.CRITICALITY_WEIGHTS.get(
                dep_info["criticality"], 0.5
            )
            dependency_weight = RiskPropagationService.DEPENDENCY_TYPE_WEIGHTS.get(
                dep_info["dependency_type"], 0.5
            )
            # Get confidence weight (default to medium if not present for backward compatibility)
            confidence = dep_info.get("confidence", "medium")
            confidence_weight = RiskPropagationService.CONFIDENCE_WEIGHTS.get(
                confidence, 0.75
            )
            
            # Risk propagation formula:
            # propagated_risk = source_risk * criticality_weight * dependency_weight * confidence_weight * depth_decay
            depth = dep_info["depth"]
            depth_decay = 1.0 / (1.0 + (depth - 1) * 0.2)  # Decay with depth
            
            propagated_risk_adjustment = (
                source_risk * criticality_weight * dependency_weight * confidence_weight * depth_decay
            )
            
            propagated_risks.append({
                "asset_id": str(dep_asset_id),
                "asset_name": dep_asset.name,
                "current_risk_score": dep_asset.risk_score or 0.0,
                "propagated_risk_adjustment": round(propagated_risk_adjustment, 2),
                "adjusted_risk_score": round(
                    (dep_asset.risk_score or 0.0) + propagated_risk_adjustment, 2
                ),
                "dependency_path": dep_info,
                "criticality": dep_info["criticality"],
                "dependency_type": dep_info["dependency_type"],
                "depth": depth
            })
        
        return {
            "source_asset_id": str(asset_id),
            "source_asset_name": asset.name,
            "source_risk_score": source_risk,
            "propagated_risks": propagated_risks,
            "total_affected_assets": len(propagated_risks),
            "max_propagation_depth": max([r["depth"] for r in propagated_risks] if propagated_risks else [0])
        }
    
    @staticmethod
    def calculate_impact_analysis(
        db: Session,
        asset_id: uuid.UUID,
        tenant_id: uuid.UUID,
        max_depth: int = 5
    ) -> Dict[str, Any]:
        """
        Analizza l'impatto se un asset fallisce (cosa succede agli asset che dipendono da esso).
        
        Returns:
        {
            "asset_id": str,
            "asset_name": str,
            "direct_dependents": int,
            "total_affected_assets": int,
            "critical_dependencies": int,
            "dependency_chains": [...],
            "estimated_impact_score": float
        }
        """
        asset = db.query(Asset).filter(
            Asset.id == asset_id,
            Asset.tenant_id == tenant_id,
            Asset.deleted_at == None
        ).first()
        
        if not asset:
            raise ValueError(f"Asset {asset_id} not found")
        
        # Get reverse dependency chain
        dependency_chain = get_reverse_dependency_chain(
            db, asset_id, tenant_id, max_depth
        )
        
        # Group by depth and analyze
        direct_dependents = [
            d for d in dependency_chain if d["depth"] == 1
        ]
        
        critical_dependencies = [
            d for d in dependency_chain
            if d["criticality"] in ["high", "critical"]
        ]
        
        # Build dependency chains
        chains: Dict[str, List[Dict]] = {}
        for dep in dependency_chain:
            chain_key = dep.get("parent_dependency_id") or "root"
            if chain_key not in chains:
                chains[chain_key] = []
            chains[chain_key].append(dep)
        
        dependency_chains = []
        for chain_key, chain_items in chains.items():
            if chain_items:
                max_crit = max(
                    [RiskPropagationService.CRITICALITY_WEIGHTS.get(
                        d["criticality"], 0.5
                    ) for d in chain_items]
                )
                dependency_chains.append({
                    "chain": chain_items,
                    "total_depth": max([d["depth"] for d in chain_items]),
                    "max_criticality": max([d["criticality"] for d in chain_items]),
                    "affected_assets_count": len(set([
                        d["from_asset_id"] for d in chain_items
                    ]))
                })
        
        # Calculate impact score
        # Base: number of direct dependents
        # Multiplier: critical dependencies
        # Depth penalty: deeper chains have less impact
        base_impact = len(direct_dependents) * 2.0
        critical_multiplier = 1.0 + (len(critical_dependencies) * 0.3)
        depth_penalty = 1.0 / (1.0 + len(dependency_chain) * 0.1)
        
        estimated_impact_score = round(
            base_impact * critical_multiplier * depth_penalty, 2
        )
        
        return {
            "asset_id": str(asset_id),
            "asset_name": asset.name,
            "direct_dependents": len(direct_dependents),
            "total_affected_assets": len(set([d["from_asset_id"] for d in dependency_chain])),
            "critical_dependencies": len(critical_dependencies),
            "dependency_chains": dependency_chains,
            "estimated_impact_score": estimated_impact_score
        }
    
    @staticmethod
    def get_dependency_risk_adjustment(
        db: Session,
        asset_id: uuid.UUID,
        tenant_id: uuid.UUID,
        use_cache: bool = True
    ) -> float:
        """
        Calcola l'aggiustamento al risk score di un asset basato sulle sue dipendenze.
        
        Se un asset dipende da asset ad alto rischio, il suo risk score viene aumentato.
        
        Args:
            use_cache: Se True, usa la cache per evitare ricalcoli
        
        Returns:
        float: Adjustment value to add to base risk score
        """
        # Prova a recuperare dalla cache
        if use_cache:
            cached_risk = risk_cache.get_cached_risk(str(tenant_id), str(asset_id))
            if cached_risk is not None:
                return cached_risk
        
        # Get dependencies where this asset depends on others
        dependencies = get_asset_dependencies_as_dependent(
            db, asset_id, tenant_id
        )
        
        if not dependencies:
            risk_cache.set_cached_risk(str(tenant_id), str(asset_id), 0.0)
            return 0.0
        
        total_adjustment = 0.0
        
        for dep in dependencies:
            # Get the dependency asset
            dep_asset = db.query(Asset).filter(
                Asset.id == dep.dependency_asset_id,
                Asset.tenant_id == tenant_id,
                Asset.deleted_at == None
            ).first()
            
            if not dep_asset:
                continue
            
            dep_risk = dep_asset.risk_score or 0.0
            
            # Calculate adjustment based on dependency risk, criticality, and confidence
            criticality_weight = RiskPropagationService.CRITICALITY_WEIGHTS.get(
                dep.criticality, 0.5
            )
            dependency_weight = RiskPropagationService.DEPENDENCY_TYPE_WEIGHTS.get(
                dep.dependency_type, 0.5
            )
            # Get confidence weight (default to medium if not present for backward compatibility)
            confidence = getattr(dep, 'confidence', 'medium') or 'medium'
            confidence_weight = RiskPropagationService.CONFIDENCE_WEIGHTS.get(
                confidence, 0.75
            )
            
            # Adjustment formula (same as in calculate_risk_propagation for consistency)
            # Depth is always 1 for direct dependencies
            depth_decay = 1.0  # No decay for direct dependencies
            adjustment = (
                dep_risk * criticality_weight * dependency_weight * confidence_weight * depth_decay
            )
            
            # Cap at reasonable maximum (e.g., 50% of source risk)
            adjustment = min(adjustment, dep_risk * 0.5)
            
            total_adjustment += adjustment
        
        # Cap total adjustment so that total risk doesn't exceed 10.0
        # Get base risk score to cap relative to it
        asset = db.query(Asset).filter(
            Asset.id == asset_id,
            Asset.tenant_id == tenant_id,
            Asset.deleted_at == None
        ).first()
        base_risk = asset.risk_score or 0.0 if asset else 0.0
        max_allowed_adjustment = max(0.0, 10.0 - base_risk)
        result = min(total_adjustment, max_allowed_adjustment)
        
        # Salva nella cache
        if use_cache:
            risk_cache.set_cached_risk(str(tenant_id), str(asset_id), result)
        
        return result
    
    @staticmethod
    def get_dependency_risk_adjustments_batch(
        db: Session,
        asset_ids: List[uuid.UUID],
        tenant_id: uuid.UUID
    ) -> Dict[str, float]:
        """
        Calcola i rischi da dipendenze per più asset in batch.
        Ottimizza le performance evitando N+1 queries.
        
        Returns:
        Dict[str, float]: Mapping asset_id -> risk_adjustment
        """
        result = {}
        
        # Carica tutte le dipendenze in una query
        from app.models.asset_dependency import AssetDependency
        
        # Query batch per tutte le dipendenze degli asset richiesti
        dependencies = (
            db.query(AssetDependency)
            .filter(
                AssetDependency.tenant_id == tenant_id,
                AssetDependency.dependent_asset_id.in_(asset_ids)
            )
            .all()
        )
        
        # Carica tutti gli asset dipendenti in una query
        dependency_asset_ids = [dep.dependency_asset_id for dep in dependencies]
        dependency_assets = {}
        if dependency_asset_ids:
            dep_assets = db.query(Asset).filter(
                Asset.id.in_(dependency_asset_ids),
                Asset.tenant_id == tenant_id,
                Asset.deleted_at == None
            ).all()
            dependency_assets = {str(a.id): a for a in dep_assets}
        
        # Carica tutti gli asset base per calcolare i limiti
        base_assets = db.query(Asset).filter(
            Asset.id.in_(asset_ids),
            Asset.tenant_id == tenant_id,
            Asset.deleted_at == None
        ).all()
        base_risks = {str(a.id): a.risk_score or 0.0 for a in base_assets}
        
        # Raggruppa le dipendenze per asset
        deps_by_asset = {}
        for dep in dependencies:
            asset_id_str = str(dep.dependent_asset_id)
            if asset_id_str not in deps_by_asset:
                deps_by_asset[asset_id_str] = []
            deps_by_asset[asset_id_str].append(dep)
        
        # Calcola il rischio per ogni asset
        for asset_id in asset_ids:
            asset_id_str = str(asset_id)
            
            # Prova cache prima
            cached_risk = risk_cache.get_cached_risk(str(tenant_id), asset_id_str)
            if cached_risk is not None:
                result[asset_id_str] = cached_risk
                continue
            
            # Calcola rischio da dipendenze
            asset_deps = deps_by_asset.get(asset_id_str, [])
            if not asset_deps:
                result[asset_id_str] = 0.0
                risk_cache.set_cached_risk(str(tenant_id), asset_id_str, 0.0)
                continue
            
            total_adjustment = 0.0
            for dep in asset_deps:
                dep_asset = dependency_assets.get(str(dep.dependency_asset_id))
                if not dep_asset:
                    continue
                
                dep_risk = dep_asset.risk_score or 0.0
                criticality_weight = RiskPropagationService.CRITICALITY_WEIGHTS.get(
                    dep.criticality, 0.5
                )
                dependency_weight = RiskPropagationService.DEPENDENCY_TYPE_WEIGHTS.get(
                    dep.dependency_type, 0.5
                )
                # Get confidence weight (default to medium if not present for backward compatibility)
                confidence = getattr(dep, 'confidence', 'medium') or 'medium'
                confidence_weight = RiskPropagationService.CONFIDENCE_WEIGHTS.get(
                    confidence, 0.75
                )
                
                depth_decay = 1.0
                adjustment = dep_risk * criticality_weight * dependency_weight * confidence_weight * depth_decay
                adjustment = min(adjustment, dep_risk * 0.5)
                total_adjustment += adjustment
            
            # Cap al massimo consentito
            base_risk = base_risks.get(asset_id_str, 0.0)
            max_allowed_adjustment = max(0.0, 10.0 - base_risk)
            final_adjustment = min(total_adjustment, max_allowed_adjustment)
            
            result[asset_id_str] = final_adjustment
            risk_cache.set_cached_risk(str(tenant_id), asset_id_str, final_adjustment)
        
        return result
    
    @staticmethod
    def get_all_affected_assets(
        db: Session,
        asset_id: uuid.UUID,
        tenant_id: uuid.UUID,
        max_depth: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get all assets that would be affected if this asset fails.
        Returns list of asset IDs with their dependency information.
        """
        dependency_chain = get_reverse_dependency_chain(
            db, asset_id, tenant_id, max_depth
        )
        
        affected_assets = {}
        for dep in dependency_chain:
            asset_id_str = dep["from_asset_id"]
            if asset_id_str not in affected_assets:
                affected_assets[asset_id_str] = {
                    "asset_id": asset_id_str,
                    "dependency_paths": [],
                    "max_criticality": dep["criticality"],
                    "min_depth": dep["depth"]
                }
            
            affected_assets[asset_id_str]["dependency_paths"].append(dep)
            
            # Update max criticality
            current_crit = affected_assets[asset_id_str]["max_criticality"]
            crit_order = {"low": 1, "medium": 2, "high": 3, "critical": 4}
            if crit_order.get(dep["criticality"], 0) > crit_order.get(current_crit, 0):
                affected_assets[asset_id_str]["max_criticality"] = dep["criticality"]
            
            # Update min depth
            if dep["depth"] < affected_assets[asset_id_str]["min_depth"]:
                affected_assets[asset_id_str]["min_depth"] = dep["depth"]
        
        return list(affected_assets.values())

