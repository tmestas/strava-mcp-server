import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

load_dotenv()

class Settings:
    def __init__(self):
        self.STRAVA_CLIENT_ID = os.environ.get("STRAVA_CLIENT_ID", "")
        self.STRAVA_CLIENT_SECRET = os.environ.get("STRAVA_CLIENT_SECRET", "")
        self.STRAVA_ACCESS_TOKEN = os.environ.get("STRAVA_ACCESS_TOKEN", "")
        self.STRAVA_REFRESH_TOKEN = os.environ.get("STRAVA_REFRESH_TOKEN", "")
        self.STRAVA_REDIRECT_URI = os.environ.get("STRAVA_REDIRECT_URI", "")
        self.PORT = os.environ.get("PORT", "10000")

        if not self.STRAVA_CLIENT_ID:
            raise ValueError("STRAVA_CLIENT_ID environment variable not set")
        if not self.STRAVA_CLIENT_SECRET:
            raise ValueError("STRAVA_CLIENT_SECRET environment variable not set")
        if not self.STRAVA_REDIRECT_URI:
            raise ValueError("STRAVA_REDIRECT_URI environment variable not set")

settings = Settings()