"""
TokenManager — owns the single stravalib Client instance for the process.

On startup it seeds from .env values.  After a successful OAuth code exchange
or refresh, the Client's access_token is updated so all subsequent API calls
use the new token without restarting.

The Client auto-refresh approach:
  - We store expires_at ourselves and refresh ~5 min early.
  - After refreshing we update client.access_token in place so callers that
    hold a reference to `token_manager.client` still work.
"""

import time
from stravalib import Client
from auth import refresh_access_token
from config import settings


class TokenManager:
    def __init__(self) -> None:
        self._refresh_token: str = settings.STRAVA_REFRESH_TOKEN
        # expires_at = 0 forces a refresh on first use if .env tokens are absent
        self._expires_at: int = 0

        # Single Client instance — reused for all API calls
        self.client = Client(access_token=settings.STRAVA_ACCESS_TOKEN or None)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def access_token(self) -> str:
        """Return a valid access token, refreshing first if needed."""
        if self._is_expired():
            self._do_refresh()
        return self.client.access_token

    def update_from_token_response(self, token_response) -> None:
        """
        Store tokens from a stravalib TokenResponse (or any dict-like object
        with access_token, refresh_token, expires_at keys).

        Called after `exchange_code` or `refresh_access_token`.
        """
        self.client.access_token = token_response["access_token"]
        self._refresh_token = token_response["refresh_token"]
        self._expires_at = int(token_response.get("expires_at", 0))

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _is_expired(self) -> bool:
        # Refresh 5 minutes before actual expiry to avoid races
        return time.time() > (self._expires_at - 300)

    def _do_refresh(self) -> None:
        if not self._refresh_token:
            raise RuntimeError(
                "No refresh token available.  Run the OAuth flow first:\n"
                "  1. Call `get_strava_auth_url` and visit the returned URL.\n"
                "  2. Call `exchange_strava_code` with the `code` from the redirect."
            )
        token_response = refresh_access_token(self._refresh_token)
        self.update_from_token_response(token_response)


# Singleton used by the rest of the application
token_manager = TokenManager()
