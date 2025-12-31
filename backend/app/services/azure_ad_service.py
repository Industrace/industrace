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
        
        logger.debug(f"Getting client credentials token for tenant: {tenant}")
        
        try:
            client_secret = decrypt_secret(config.client_secret_encrypted)
        except Exception as e:
            logger.error(f"Failed to decrypt client secret: {e}")
            raise ValueError("Failed to decrypt client secret. The client secret may have been encrypted with a different ENCRYPTION_KEY. Please reconfigure the SSO settings with a new client secret.")
        
        # Scopes per Microsoft Graph API
        requested_scopes = scopes or ["https://graph.microsoft.com/.default"]
        scope = " ".join(requested_scopes)
        
        data = {
            "client_id": config.client_id,
            "client_secret": client_secret,
            "scope": scope,
            "grant_type": "client_credentials"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    token_url,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    error_detail = response.text if response else "Unknown error"
                    logger.error(f"Token request failed: {response.status_code} - {error_detail}")
                    raise ValueError(f"Failed to get access token: {response.status_code} - {error_detail}")
                
                token_data = response.json()
                access_token = token_data.get("access_token")
                
                if not access_token:
                    error_description = token_data.get("error_description", "Unknown error")
                    logger.error(f"No access token in response: {error_description}")
                    raise ValueError(f"Failed to get access token: {error_description}")
                
                logger.debug("Successfully obtained access token")
                return access_token
                
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if e.response else str(e)
            logger.error(f"HTTP error getting access token: {e.response.status_code} - {error_detail}")
            raise ValueError(f"Failed to authenticate with Azure AD: {e.response.status_code} - {error_detail}")
        except httpx.RequestError as e:
            logger.error(f"Request error getting access token: {e}")
            raise ValueError(f"Network error authenticating with Azure AD: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error getting access token: {e}", exc_info=True)
            raise ValueError(f"Unexpected error authenticating with Azure AD: {str(e)}")
    
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
        logger.debug(f"Getting access token for Azure AD user listing")
        try:
            access_token = await AzureADService.get_client_credentials_token(
                config,
                scopes=["https://graph.microsoft.com/.default"]
            )
            if not access_token:
                raise ValueError("Failed to obtain access token from Azure AD")
            logger.debug("Successfully obtained access token")
        except Exception as e:
            logger.error(f"Failed to get access token: {e}", exc_info=True)
            raise ValueError(f"Failed to authenticate with Azure AD: {str(e)}")
        
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
        
        try:
            async with httpx.AsyncClient() as client:
                while True:
                    current_url = next_link or url
                    current_params = {} if next_link else params
                    
                    headers = {"Authorization": f"Bearer {access_token}"}
                    
                    logger.debug(f"Fetching Azure AD users from: {current_url}")
                    
                    response = await client.get(
                        current_url,
                        params=current_params,
                        headers=headers,
                        timeout=30.0
                    )
                    
                    if response.status_code != 200:
                        error_detail = response.text if response else "Unknown error"
                        logger.error(f"Azure AD API error: {response.status_code} - {error_detail}")
                        raise ValueError(f"Azure AD API returned error {response.status_code}: {error_detail}")
                    
                    data = response.json()
                    
                    users = data.get("value", [])
                    if not isinstance(users, list):
                        logger.warning(f"Expected list of users, got: {type(users)}")
                        users = []
                    
                    all_users.extend(users)
                    logger.debug(f"Retrieved {len(users)} users in this batch, total: {len(all_users)}")
                    
                    # Controlla se ci sono più pagine
                    next_link = data.get("@odata.nextLink")
                    if not next_link:
                        break
                    
                    # Safety limit to prevent infinite loops
                    if len(all_users) >= 1000:
                        logger.warning(f"Reached safety limit of 1000 users, stopping pagination")
                        break
            
            logger.info(f"Retrieved {len(all_users)} users from Azure AD")
            return all_users
            
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if e.response else str(e)
            logger.error(f"HTTP error fetching Azure AD users: {e.response.status_code} - {error_detail}")
            raise ValueError(f"Failed to fetch users from Azure AD: {e.response.status_code} - {error_detail}")
        except httpx.RequestError as e:
            logger.error(f"Request error fetching Azure AD users: {e}")
            raise ValueError(f"Network error fetching users from Azure AD: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error fetching Azure AD users: {e}", exc_info=True)
            raise ValueError(f"Unexpected error fetching users from Azure AD: {str(e)}")
    
    @staticmethod
    async def get_user_by_id(
        config: TenantSSOConfig,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Ottiene un singolo utente da Azure AD per ID.
        """
        logger.debug(f"Fetching Azure AD user by ID: {user_id}")
        
        try:
            access_token = await AzureADService.get_client_credentials_token(
                config,
                scopes=["https://graph.microsoft.com/.default"]
            )
        except Exception as e:
            logger.error(f"Failed to get access token for Azure AD user lookup: {e}")
            raise ValueError(f"Failed to authenticate with Azure AD: {str(e)}")
        
        url = f"{AzureADService.GRAPH_API_BASE}/users/{user_id}"
        headers = {"Authorization": f"Bearer {access_token}"}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=10.0)
                response.raise_for_status()
                user_data = response.json()
                logger.debug(f"Successfully fetched Azure AD user {user_id}")
                return user_data
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Azure AD user {user_id} not found")
                raise ValueError(f"User {user_id} not found in Azure AD")
            else:
                error_detail = e.response.text if e.response else str(e)
                logger.error(f"HTTP error fetching Azure AD user {user_id}: {e.response.status_code} - {error_detail}")
                raise ValueError(f"Failed to fetch user from Azure AD: {e.response.status_code} - {error_detail}")
        except httpx.RequestError as e:
            logger.error(f"Request error fetching Azure AD user {user_id}: {e}")
            raise ValueError(f"Network error fetching user from Azure AD: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error fetching Azure AD user {user_id}: {e}", exc_info=True)
            raise ValueError(f"Unexpected error fetching user from Azure AD: {str(e)}")
