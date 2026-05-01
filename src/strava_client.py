"""
StravaClient — wraps the stravalib Client held by TokenManager.

Each method ensures the access token is fresh (via token_manager.access_token),
then delegates to the appropriate stravalib method and returns plain Python
dicts/lists so FastMCP can serialise them to JSON easily.
"""

from token_manager import token_manager


def _client():
    """Return the stravalib Client with a guaranteed-valid access token."""
    _ = token_manager.access_token  # triggers refresh if needed
    return token_manager.client


class StravaClient:

    # ------------------------------------------------------------------
    # Athlete
    # ------------------------------------------------------------------

    def get_athlete(self) -> dict:
        """Authenticated athlete's full profile."""
        athlete = _client().get_athlete()
        return {
            "id": athlete.id,
            "username": athlete.username,
            "firstname": athlete.firstname,
            "lastname": athlete.lastname,
            "city": athlete.city,
            "state": athlete.state,
            "country": athlete.country,
            "sex": athlete.sex,
            "premium": athlete.premium,
            "created_at": str(athlete.created_at),
            "updated_at": str(athlete.updated_at),
            "follower_count": athlete.follower_count,
            "friend_count": athlete.friend_count,
            "measurement_preference": athlete.measurement_preference,
            "weight": float(athlete.weight) if athlete.weight else None,
        }

    def get_athlete_stats(self, athlete_id: int) -> dict:
        """Totals and stats for the given athlete."""
        return vars(_client().get_athlete_stats(athlete_id))

    def get_athlete_zones(self) -> dict:
        """Heart-rate and power zones for the authenticated athlete."""
        return vars(_client().get_athlete_zones())

    # ------------------------------------------------------------------
    # Activities
    # ------------------------------------------------------------------

    def list_activities(
            self,
            before=None,
            after=None,
            limit: int = 30,
    ) -> list:
        activities = _client().get_activities(before=before, after=after, limit=limit)
        return [dict(vars(a)) for a in activities]

    def get_activity(self, activity_id: int, include_all_efforts: bool = False) -> dict:
        """Detailed representation of a single activity."""
        return dict(vars(_client().get_activity(activity_id, include_all_efforts=include_all_efforts)))

    def get_activity_streams(self, activity_id: int, types: list[str] | None = None) -> dict:
        types = types or ["time", "distance", "heartrate", "watts", "cadence", "velocity_smooth"]
        streams = _client().get_activity_streams(activity_id, types=types, resolution="high")
        return {k: dict(vars(v)) for k, v in streams.items()}

    def get_activity_laps(self, activity_id: int) -> list:
        """Laps for the given activity."""
        return [dict(vars(lap)) for lap in _client().get_activity_laps(activity_id)]

    # ------------------------------------------------------------------
    # Segments
    # ------------------------------------------------------------------

    def get_segment(self, segment_id: int) -> dict:
        """Detailed representation of a segment."""
        return dict(vars(_client().get_segment(segment_id)))

    def get_starred_segments(self, limit: int = 30) -> list:
        """Segments starred by the authenticated athlete."""
        return [dict(vars(s)) for s in _client().get_starred_segments(limit=limit)]

    def get_segment_leaderboard(
            self,
            segment_id: int,
            gender: str | None = None,
            age_group: str | None = None,
            top_results_limit: int = 10,
    ) -> dict:
        board = _client().get_segment_leaderboard(
            segment_id,
            gender=gender,
            age_group=age_group,
            top_results_limit=top_results_limit,
        )
        return dict(vars(board))

    # ------------------------------------------------------------------
    # Gear
    # ------------------------------------------------------------------

    def get_gear(self, gear_id: str) -> dict:
        """Equipment details (shoes, bikes). gear_id starts with 'b' or 'g'."""
        return dict(vars(_client().get_gear(gear_id)))


# Singleton
strava_client = StravaClient()
