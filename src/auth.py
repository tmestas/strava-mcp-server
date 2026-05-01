"""
Strava OAuth helpers using the stravalib Client.

Flow:
  1. Call `get_authorization_url()` → redirect user to Strava
  2. User approves → Strava redirects to REDIRECT_URI with ?code=...&scope=...
  3. Call `exchange_code(code)` → returns a TokenResponse with access/refresh tokens
  4. TokenManager stores the result and auto-refreshes from then on.
"""

from stravalib import Client
from config import settings
from typing import Literal
from pathlib import Path

ScopeType = Literal["read", "read_all", "profile:read_all", "profile:write", "activity:read", "activity:read_all", "activity:write"]

STRAVA_SCOPES: list[ScopeType] = ["read", "activity:read_all", "profile:read_all"]


def get_authorization_url(scope: list[ScopeType] | None = None) -> str:
    if scope is None:
        scope = STRAVA_SCOPES

    client = Client()
    result = client.authorization_url(
        client_id=settings.STRAVA_CLIENT_ID,
        redirect_uri=settings.STRAVA_REDIRECT_URI,
        scope=scope,
    )

    return result


def exchange_code(code: str) -> dict:
    client = Client()
    token_response = client.exchange_code_for_token(
        client_id=settings.STRAVA_CLIENT_ID,
        client_secret=settings.STRAVA_CLIENT_SECRET,
        code=code,
    )

    access_token = token_response["access_token"]
    refresh_token = token_response["refresh_token"]
    expires_at = token_response["expires_at"]

    # Write tokens back to .env file
    env_path = Path(__file__).parent.parent / ".env"

    # Read existing .env content
    lines = env_path.read_text().splitlines()

    # Update or append each token
    updates = {
        "STRAVA_ACCESS_TOKEN": access_token,
        "STRAVA_REFRESH_TOKEN": refresh_token,
    }

    for key, value in updates.items():
        found = False
        for i, line in enumerate(lines):
            if line.startswith(f"{key}="):
                lines[i] = f"{key}={value}"
                found = True
                break
        if not found:
            lines.append(f"{key}={value}")

    env_path.write_text("\n".join(lines) + "\n")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_at": expires_at,
        "athlete": token_response.get("athlete") if hasattr(token_response, "get") else None,
    }


def refresh_access_token(refresh_token: str):
    """
    Use a refresh token to get a new access token.

    Returns the same TokenResponse shape as `exchange_code`.
    """
    client = Client()
    return client.refresh_access_token(
        client_id=settings.STRAVA_CLIENT_ID,
        client_secret=settings.STRAVA_CLIENT_SECRET,
        refresh_token=refresh_token,
    )


def deauthorize(access_token: str) -> None:
    """Revoke access — invalidates the current access token."""
    client = Client(access_token=access_token)
    client.deauthorize()
