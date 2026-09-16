import time
import base64
from typing import Optional, Dict, Any, Tuple
import httpx

from backend.config import settings
from backend.integrations.servicenow.exceptions import ServiceNowAuthError

def mask_secret(value: Optional[str], visible_chars: int = 4) -> str:
    """Safely masks a secret string for logging and UI presentation."""
    if not value:
        return "Not Configured"
    if len(value) <= visible_chars * 2:
        return "********"
    return f"{value[:visible_chars]}...{value[-visible_chars:]}"


def sanitize_url(url: Optional[str]) -> str:
    """Sanitizes instance URL by stripping trailing slashes."""
    if not url:
        return ""
    return url.strip().rstrip("/")


class ServiceNowAuthProvider:
    """
    Manages authentication headers, credentials, and OAuth2 token lifecycles
    for outbound ServiceNow Table API requests.
    """
    def __init__(
        self,
        instance_url: Optional[str] = None,
        auth_mode: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        token: Optional[str] = None
    ):
        self.instance_url = sanitize_url(instance_url or settings.SERVICE_NOW_INSTANCE_URL)
        self.auth_mode = (auth_mode or settings.SERVICE_NOW_AUTH_MODE or "basic").lower()
        self.client_id = client_id or settings.SERVICE_NOW_CLIENT_ID
        self.client_secret = client_secret or settings.SERVICE_NOW_CLIENT_SECRET
        self.username = username or settings.SERVICE_NOW_USERNAME
        self.password = password or settings.SERVICE_NOW_PASSWORD
        self.token = token or settings.SERVICE_NOW_TOKEN

        # Cached OAuth2 token state
        self._cached_access_token: Optional[str] = None
        self._token_expires_at: float = 0.0

    @property
    def is_configured(self) -> bool:
        """Determines if sufficient credentials exist to connect to ServiceNow."""
        if not self.instance_url:
            return False
        if self.auth_mode == "token" and self.token:
            return True
        if self.auth_mode == "basic" and self.username and self.password:
            return True
        if self.auth_mode == "oauth2":
            if self.client_id and self.client_secret and self.username and self.password:
                return True
            if self.client_id and self.client_secret:
                return True
        return False

    def get_status_summary(self) -> Dict[str, Any]:
        """Returns safe, non-sensitive configuration metadata for UI and status endpoints."""
        return {
            "is_configured": self.is_configured,
            "auth_mode": self.auth_mode,
            "instance_url": self.instance_url or "Not Configured",
            "username_configured": bool(self.username),
            "client_id_masked": mask_secret(self.client_id) if self.client_id else "Not Configured",
            "token_configured": bool(self.token),
        }

    def get_auth_headers(self, client: Optional[httpx.Client] = None) -> Dict[str, str]:
        """
        Generates HTTP request headers required for ServiceNow authentication.
        Raises ServiceNowAuthError if authentication is misconfigured or token exchange fails.
        """
        if not self.is_configured:
            raise ServiceNowAuthError("ServiceNow integration is not configured. Missing required instance URL or credentials.")

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        if self.auth_mode == "token":
            headers["Authorization"] = f"Bearer {self.token}"
            return headers

        if self.auth_mode == "basic":
            raw_cred = f"{self.username}:{self.password}".encode("utf-8")
            b64_cred = base64.b64encode(raw_cred).decode("utf-8")
            headers["Authorization"] = f"Basic {b64_cred}"
            return headers

        if self.auth_mode == "oauth2":
            access_token = self._get_or_refresh_oauth_token(client)
            headers["Authorization"] = f"Bearer {access_token}"
            return headers

        raise ServiceNowAuthError(f"Unsupported ServiceNow auth_mode: '{self.auth_mode}'")

    def _get_or_refresh_oauth_token(self, client: Optional[httpx.Client] = None) -> str:
        """Retrieves active OAuth2 access token or requests a new one from ServiceNow token endpoint."""
        now = time.time()
        # Return cached token if valid for at least 30 more seconds
        if self._cached_access_token and self._token_expires_at > (now + 30):
            return self._cached_access_token

        token_url = f"{self.instance_url}/oauth_token.do"
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        if self.username and self.password:
            data.update({
                "grant_type": "password",
                "username": self.username,
                "password": self.password
            })
        else:
            data.update({
                "grant_type": "client_credentials"
            })

        local_client = client or httpx.Client(timeout=15.0)
        try:
            resp = local_client.post(token_url, data=data)
            if resp.status_code != 200:
                raise ServiceNowAuthError(
                    f"OAuth2 token exchange failed with status {resp.status_code}: {resp.text}",
                    details={"status_code": resp.status_code}
                )
            token_data = resp.json()
            access_token = token_data.get("access_token")
            expires_in = token_data.get("expires_in", 1800)

            if not access_token:
                raise ServiceNowAuthError("OAuth2 token endpoint returned response without access_token.")

            self._cached_access_token = access_token
            self._token_expires_at = now + float(expires_in)
            return access_token
        except httpx.RequestError as exc:
            raise ServiceNowAuthError(f"Network error during OAuth2 token exchange: {str(exc)}") from exc
        finally:
            if client is None:
                local_client.close()
