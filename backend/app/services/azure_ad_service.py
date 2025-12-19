# backend/app/services/azure_ad_service.py
"""
Service per interagire con Azure AD (Entra ID) tramite Microsoft Graph API.
Gestisce l'ottenimento di access token e la lettura degli utenti.
"""
from typing import List, Dict, Optional, Any
import httpx
import logging
from app.models import TenantSSOConfig
from app.services.sso_encryption import decrypt_secret

logger = logging.getLogger(__name__)


class AzureADService:
    """Service per interagire con Azure AD tramite Microsoft Graph API"""
    
    GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"
    
    @staticmethod
    async def get_client_credentials_token(
        config: TenantSSOConfig,
        scopes: Optional[List[str]] = None
    ) -> str:
        """
        Ottiene un access token usando client credentials flow (app-only).
        Necessario per leggere gli utenti senza interazione dell'utente.
        """
        if config.provider_type != "azure_ad":
            raise ValueError("This service is only for Azure AD")
        
        tenant = config.tenant_domain or "common"
        token_url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
        
        client_secret = decrypt_secret(config.client_secret_encrypted)
        
        # Scopes per Microsoft Graph API
        requested_scopes = scopes or ["https://graph.microsoft.com/.default"]
        scope = " ".join(requested_scopes)
        
        data = {
            "client_id": config.client_id,
            "client_secret": client_secret,
            "scope": scope,
            "grant_type": "client_credentials"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10.0
            )
            response.raise_for_status()
            token_data = response.json()
            return token_data.get("access_token")
    
    @staticmethod
    async def list_users(
        config: TenantSSOConfig,
        filter_query: Optional[str] = None,
        select_fields: Optional[List[str]] = None,
        top: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Lista tutti gli utenti da Azure AD usando Microsoft Graph API.
        
        Args:
            config: Configurazione SSO del tenant
            filter_query: Query filter OData (es: "startswith(displayName,'A')")
            select_fields: Campi da selezionare (default: id, displayName, mail, userPrincipalName)
            top: Numero massimo di risultati (default: 100, max: 999)
        
        Returns:
            Lista di utenti da Azure AD
        """
        access_token = await AzureADService.get_client_credentials_token(
            config,
            scopes=["https://graph.microsoft.com/.default"]
        )
        
        # Campi di default da selezionare
        default_fields = ["id", "displayName", "mail", "userPrincipalName", "accountEnabled", "jobTitle", "department"]
        select = ",".join(select_fields or default_fields)
        
        # Costruisci URL
        url = f"{AzureADService.GRAPH_API_BASE}/users"
        params = {
            "$select": select,
            "$top": min(top, 999)  # Max 999 per richiesta
        }
        
        if filter_query:
            params["$filter"] = filter_query
        
        all_users = []
        next_link = None
        
        async with httpx.AsyncClient() as client:
            while True:
                current_url = next_link or url
                current_params = {} if next_link else params
                
                headers = {"Authorization": f"Bearer {access_token}"}
                
                response = await client.get(
                    current_url,
                    params=current_params,
                    headers=headers,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                users = data.get("value", [])
                all_users.extend(users)
                
                # Controlla se ci sono più pagine
                next_link = data.get("@odata.nextLink")
                if not next_link:
                    break
        
        logger.info(f"Retrieved {len(all_users)} users from Azure AD")
        return all_users
    
    @staticmethod
    async def get_user_by_id(
        config: TenantSSOConfig,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Ottiene un singolo utente da Azure AD per ID.
        """
        access_token = await AzureADService.get_client_credentials_token(
            config,
            scopes=["https://graph.microsoft.com/.default"]
        )
        
        url = f"{AzureADService.GRAPH_API_BASE}/users/{user_id}"
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=10.0)
            response.raise_for_status()
            return response.json()
