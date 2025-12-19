"""
Servizio di caching per i rischi da dipendenze
Ottimizza le performance evitando ricalcoli costosi
"""
from datetime import datetime, timedelta
from typing import Dict, Optional
from sqlalchemy.orm import Session
import uuid


class RiskCache:
    """Cache in-memory per i rischi da dipendenze"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, any]] = {}
        self._cache_ttl = 300  # 5 minuti
    
    def _get_cache_key(self, tenant_id: str, asset_id: str) -> str:
        """Genera una chiave di cache unica per asset e tenant"""
        return f"risk_deps_{tenant_id}_{asset_id}"
    
    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """Verifica se la cache è ancora valida"""
        if not cache_entry:
            return False
        
        cached_at = cache_entry.get('cached_at')
        if not cached_at:
            return False
        
        # Converti stringa ISO in datetime se necessario
        if isinstance(cached_at, str):
            cached_at = datetime.fromisoformat(cached_at.replace('Z', '+00:00'))
        
        return datetime.utcnow() - cached_at < timedelta(seconds=self._cache_ttl)
    
    def get_cached_risk(self, tenant_id: str, asset_id: str) -> Optional[float]:
        """Recupera il rischio da dipendenze dalla cache se valido"""
        cache_key = self._get_cache_key(tenant_id, asset_id)
        cache_entry = self._cache.get(cache_key)
        
        if self._is_cache_valid(cache_entry):
            return cache_entry.get('risk_from_deps')
        
        # Cache scaduta o inesistente
        if cache_key in self._cache:
            del self._cache[cache_key]
        
        return None
    
    def set_cached_risk(self, tenant_id: str, asset_id: str, risk_from_deps: float) -> None:
        """Salva il rischio da dipendenze nella cache"""
        cache_key = self._get_cache_key(tenant_id, asset_id)
        self._cache[cache_key] = {
            'risk_from_deps': risk_from_deps,
            'cached_at': datetime.utcnow().isoformat()
        }
    
    def invalidate_asset(self, tenant_id: str, asset_id: str) -> None:
        """Invalida la cache per un asset specifico"""
        cache_key = self._get_cache_key(tenant_id, asset_id)
        if cache_key in self._cache:
            del self._cache[cache_key]
    
    def invalidate_tenant(self, tenant_id: str) -> None:
        """Invalida tutta la cache per un tenant"""
        keys_to_delete = [
            key for key in self._cache.keys()
            if key.startswith(f"risk_deps_{tenant_id}_")
        ]
        for key in keys_to_delete:
            del self._cache[key]
    
    def clear_all_cache(self) -> None:
        """Pulisce tutta la cache"""
        self._cache.clear()


# Istanza globale del cache
risk_cache = RiskCache()

