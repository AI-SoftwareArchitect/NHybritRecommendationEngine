"""
External API Service
Handles authentication and data fetching from the external note API.
"""
import httpx
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from config.settings import get_settings


class ExternalAPIService:
    """Service for interacting with external note API."""
    
    _instance: Optional['ExternalAPIService'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.settings = get_settings()
        self._access_token: Optional[str] = None
        self._token_expiration: Optional[datetime] = None
        self._user_id: Optional[str] = None
        self._initialized = True
    
    @property
    def base_url(self) -> str:
        return self.settings.external_api_base_url
    
    def _is_token_valid(self) -> bool:
        """Check if current token is still valid."""
        if not self._access_token or not self._token_expiration:
            return False
        
        # Add 5 minute buffer for safety
        now = datetime.now(timezone.utc)
        return now < self._token_expiration
    
    def login(self) -> bool:
        """
        Login to external API and store access token.
        Returns True if login successful.
        """
        try:
            login_url = f"{self.base_url}/api/auth/login"
            payload = {
                "email": self.settings.external_api_email,
                "password": self.settings.external_api_password
            }
            
            with httpx.Client(timeout=30.0, verify=False) as client:
                response = client.post(login_url, json=payload)
                response.raise_for_status()
                
                data = response.json()
                
                if data.get("meta", {}).get("isSuccess"):
                    entity = data.get("entity", {})
                    self._access_token = entity.get("accessToken")
                    self._user_id = entity.get("userId")
                    
                    # Parse expiration date
                    exp_str = entity.get("accessTokenExpiration", "")
                    if exp_str:
                        # Handle ISO format with Z suffix
                        exp_str = exp_str.replace("Z", "+00:00")
                        self._token_expiration = datetime.fromisoformat(exp_str)
                    
                    print(f"✓ External API login successful (User: {entity.get('username')})")
                    return True
                else:
                    print(f"✗ External API login failed: {data.get('meta', {}).get('message')}")
                    return False
                    
        except httpx.HTTPStatusError as e:
            print(f"✗ External API login HTTP error: {e.response.status_code}")
            return False
        except Exception as e:
            print(f"✗ External API login error: {e}")
            return False
    
    def get_access_token(self) -> Optional[str]:
        """Get current access token, refreshing if necessary."""
        if not self._is_token_valid():
            if not self.login():
                return None
        return self._access_token
    
    def get_current_user_id(self) -> Optional[str]:
        """Get the user ID of the logged-in user."""
        if not self._is_token_valid():
            self.login()
        return self._user_id
    
    def get_all_notes(self) -> List[Dict[str, Any]]:
        """
        Fetch all notes from external API using getPage endpoint.
        Returns list of note dictionaries.
        """
        token = self.get_access_token()
        if not token:
            print("✗ Cannot fetch notes: No valid token")
            return []
        
        try:
            url = f"{self.base_url}/api/note/getPage"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            payload = {
                "pagingRequest": {
                    "pageNumber": 1,
                    "pageSize": 2048
                },
                "minRating": 0,
                "sortBy": 1,
                "searchText": None,
                "tagIds": [],
                "lectureIds": [],
                "languageIds": [],
                "universityIds": []
            }
            
            with httpx.Client(timeout=60.0, verify=False) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                
                if data.get("meta", {}).get("isSuccess"):
                    entities = data.get("entities", [])
                    page_info = data.get("pageInfo", {})
                    total_count = page_info.get("totalRowCount", len(entities))
                    
                    print(f"✓ Fetched {len(entities)} notes (total: {total_count})")
                    return entities
                else:
                    print(f"✗ Failed to fetch notes: {data.get('meta', {}).get('message')}")
                    return []
                    
        except httpx.HTTPStatusError as e:
            print(f"✗ HTTP error fetching notes: {e.response.status_code}")
            return []
        except Exception as e:
            print(f"✗ Error fetching notes: {e}")
            return []


# Singleton accessor
_service_instance: Optional[ExternalAPIService] = None


def get_external_api_service() -> ExternalAPIService:
    """Get or create the external API service singleton."""
    global _service_instance
    if _service_instance is None:
        _service_instance = ExternalAPIService()
    return _service_instance
