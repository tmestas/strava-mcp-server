"""
Strava MCP server.

Run:
    uv run main.py
or:
    python main.py

The server exposes tools that Claude (or any MCP client) can call to
interact with the Strava API on behalf of the authenticated athlete.

--- First-time OAuth setup ---
If you don't already have valid tokens in .env, call these two tools in order:

  1. get_strava_auth_url   → visit the returned URL in your browser
  2. exchange_strava_code  → paste the `code` query param from the redirect URL

After that, tokens are managed automatically.
"""
import logging


from mcp.server.fastmcp import FastMCP

from auth import get_authorization_url, exchange_code
from strava_client import strava_client
from token_manager import token_manager
from config import settings  # noqa: F401 — imported to validate .env on startup

logging.basicConfig(
    filename=r"C:\Users\tanne\Code\projects\strava-mcp-server\debug.log",
    level=logging.DEBUG,
    format="%(asctime)s %(message)s"
)

mcp = FastMCP("Strava MCP", json_response=True)


# -----------------------------------------------------------------------
# Auth tools
# -----------------------------------------------------------------------

@mcp.tool()
def get_strava_auth_url() -> dict:
    """
    Generate the Strava OAuth authorisation URL.

    Visit the returned URL in a browser.  After approving access Strava
    redirects to your REDIRECT_URI with a `code` query parameter.
    Pass that code to `exchange_strava_code`.
    """
    url = get_authorization_url()
    return {"authorization_url": url}


@mcp.tool()
def exchange_strava_code(code: str) -> dict:
    """
    Exchange an OAuth authorisation code for access + refresh tokens.

    `code` is the value of the `code` query parameter in the redirect URL
    after the user approves access on the Strava auth page.

    On success the tokens are stored in memory and used automatically for
    all subsequent API calls.
    """
    token_response = exchange_code(code)
    token_manager.update_from_token_response(token_response)
    athlete = token_response.get("athlete") or {}
    return {
        "status": "authenticated",
        "athlete_id": athlete.get("id"),
        "athlete_name": f"{athlete.get('firstname', '')} {athlete.get('lastname', '')}".strip(),
        "expires_at": token_response.get("expires_at"),
    }


@mcp.tool()
def deauthorize_strava() -> dict:
    """
    Revoke this application's access to the athlete's Strava account.

    The current access token is invalidated immediately.  The athlete will
    need to re-authorise via `get_strava_auth_url` to use this server again.
    """
    from auth import deauthorize
    deauthorize(token_manager.access_token)
    return {"status": "deauthorized"}


# -----------------------------------------------------------------------
# Athlete tools
# -----------------------------------------------------------------------

@mcp.tool()
def get_athlete_profile() -> dict:
    """Get the authenticated athlete's full profile."""
    return strava_client.get_athlete()


@mcp.tool()
def get_athlete_stats(athlete_id: int) -> dict:
    """
    Get totals and stats for an athlete.

    Retrieve the athlete_id from `get_athlete_profile` (the `id` field).
    """
    return strava_client.get_athlete_stats(athlete_id)


@mcp.tool()
def get_athlete_zones() -> dict:
    """Get heart-rate and power training zones for the authenticated athlete."""
    return strava_client.get_athlete_zones()


# -----------------------------------------------------------------------
# Activity tools
# -----------------------------------------------------------------------

@mcp.tool()
def list_activities(
    before: int | None = None,
    after: int | None = None,
    limit: int = 30,
) -> list:
    """
    List recent activities for the authenticated athlete.

    Args:
        before: Unix timestamp — return activities before this time.
        after:  Unix timestamp — return activities after this time.
        limit:  Maximum number of activities to return (default 30).
    """
    return strava_client.list_activities(before=before, after=after, limit=limit)


@mcp.tool()
def get_activity(activity_id: int, include_all_efforts: bool = False) -> dict:
    """
    Get detailed information about a single activity.

    Args:
        activity_id:         Strava activity ID.
        include_all_efforts: Include all segment efforts (default False).
    """
    return strava_client.get_activity(activity_id, include_all_efforts=include_all_efforts)


@mcp.tool()
def get_activity_streams(activity_id: int, types: list[str] | None = None) -> dict:
    """
    Get time-series data streams for an activity.

    Args:
        activity_id: Strava activity ID.
        types:       Stream types to include. Defaults to
                     [time, distance, heartrate, watts, cadence, velocity_smooth].
                     Available: time, distance, latlng, altitude, velocity_smooth,
                     heartrate, cadence, watts, temp, moving, grade_smooth.
    """
    return strava_client.get_activity_streams(activity_id, types=types)


@mcp.tool()
def get_activity_laps(activity_id: int) -> list:
    """
    Get lap data for an activity.

    Args:
        activity_id: Strava activity ID.
    """
    return strava_client.get_activity_laps(activity_id)


# -----------------------------------------------------------------------
# Segment tools
# -----------------------------------------------------------------------

@mcp.tool()
def get_segment(segment_id: int) -> dict:
    """
    Get detailed information about a Strava segment.

    Args:
        segment_id: Strava segment ID.
    """
    return strava_client.get_segment(segment_id)


@mcp.tool()
def get_starred_segments(page: int = 1, per_page: int = 30) -> list:
    """
    List segments starred by the authenticated athlete.

    Args:
        page:     Page number (default 1).
        per_page: Results per page (default 30).
    """
    return strava_client.get_starred_segments(page=page, per_page=per_page)


@mcp.tool()
def get_segment_leaderboard(
    segment_id: int,
    gender: str | None = None,
    age_group: str | None = None,
    per_page: int = 10,
) -> dict:
    """
    Get the leaderboard for a segment.

    Args:
        segment_id: Strava segment ID.
        gender:     Filter by 'M' or 'F'.
        age_group:  Filter by age group, e.g. '0_24', '25_34', '35_44',
                    '45_54', '55_64', '65_74', '75_plus'.
        per_page:   Number of entries to return (default 10).
    """
    return strava_client.get_segment_leaderboard(
        segment_id, gender=gender, age_group=age_group, per_page=per_page
    )


# -----------------------------------------------------------------------
# Gear tools
# -----------------------------------------------------------------------

@mcp.tool()
def get_gear(gear_id: str) -> dict:
    """
    Get details for a piece of gear (bike or shoes).

    Args:
        gear_id: The gear ID from an activity or athlete profile.
                 Bike IDs start with 'b', shoe IDs with 'g'.
    """
    return strava_client.get_gear(gear_id)


# -----------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
