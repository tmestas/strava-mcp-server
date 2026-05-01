# Strava MCP Server

A FastMCP server that exposes Strava API data as tools for Claude (or any MCP client), built on top of the [`stravalib`](https://stravalib.readthedocs.io) Python client.

## File structure

```
strava_mcp/
├── main.py           # FastMCP server + all tool definitions
├── auth.py           # OAuth 2.0 helpers using stravalib.Client
├── token_manager.py  # Holds the live stravalib Client, auto-refreshes tokens
├── strava_client.py  # Thin wrapper that delegates to token_manager.client
├── config.py         # Settings loaded from .env
└── .env              # Your secrets (never commit this)
```

## Setup

### 1. Create your `.env`

```env
STRAVA_CLIENT_ID=your_client_id
STRAVA_CLIENT_SECRET=your_client_secret
STRAVA_REDIRECT_URI=http://localhost:10000/callback   # must match your Strava app settings
STRAVA_ACCESS_TOKEN=                                  # leave blank until after OAuth
STRAVA_REFRESH_TOKEN=                                 # leave blank until after OAuth
PORT=10000
```

### 2. Install dependencies

```bash
uv add mcp stravalib python-dotenv
# or: pip install mcp stravalib python-dotenv
```

### 3. Run the server

```bash
uv run main.py
# or: python main.py
```

---

## First-time OAuth flow

Because Strava uses OAuth 2.0, you need to authorise the app once. Do this by calling the MCP tools in order:

**Step 1** — call `get_strava_auth_url`
→ visit the returned URL in your browser and click "Authorise"

**Step 2** — Strava redirects to your `REDIRECT_URI` with `?code=abc123...` in the URL
→ copy that `code` value

**Step 3** — call `exchange_strava_code` with that code
→ tokens are stored in the live `stravalib.Client` instance and used automatically from here on

If you already have valid tokens from a previous run, set them in `.env` as `STRAVA_ACCESS_TOKEN` and `STRAVA_REFRESH_TOKEN`. The server will seed the client with those values on startup and auto-refresh whenever they expire (tokens are refreshed 5 minutes before expiry).

To revoke access, call `deauthorize_strava`. The athlete will need to re-authorise before the server can make API calls again.

---

## Available tools

### Auth

| Tool | Description |
|------|-------------|
| `get_strava_auth_url` | Generate the OAuth authorisation URL to send the user to |
| `exchange_strava_code` | Exchange the auth code from the redirect for access + refresh tokens |
| `deauthorize_strava` | Revoke this app's access to the athlete's account |

### Athlete

| Tool | Description |
|------|-------------|
| `get_athlete_profile` | Full profile for the authenticated athlete |
| `get_athlete_stats` | All-time and recent totals by sport |
| `get_athlete_zones` | Heart-rate and power training zones |

### Activities

| Tool | Description |
|------|-------------|
| `list_activities` | Recent activities, filterable by `before`/`after` Unix timestamps and `limit` |
| `get_activity` | Detailed data for a single activity |
| `get_activity_streams` | Time-series streams (HR, power, distance, cadence, altitude…) |
| `get_activity_laps` | Lap splits for an activity |

### Segments

| Tool | Description |
|------|-------------|
| `get_segment` | Details for a segment |
| `get_starred_segments` | Segments starred by the authenticated athlete |
| `get_segment_leaderboard` | Leaderboard for a segment, filterable by gender and age group |

### Gear

| Tool | Description |
|------|-------------|
| `get_gear` | Details for a bike or pair of shoes (IDs start with `b` or `g`) |

---

## Adding more tools

`stravalib.Client` covers most of the Strava v3 API. To add a new tool:

1. Add a method to `StravaClient` in `strava_client.py` that calls `_client().<stravalib_method>()` and returns `.to_dict()`.
2. Expose it with a `@mcp.tool()` decorated function in `main.py`.

The full stravalib API reference is at <https://stravalib.readthedocs.io> and the underlying Strava REST API reference is at <https://developers.strava.com/docs/reference/>.
