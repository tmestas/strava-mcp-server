import os
import json
import logging
from pathlib import Path
from dotenv import set_key
import boto3

class TokenStore:
    """
    Abstracts token storage so the same code works locally and on AWS.
    Set TOKEN_STORE=aws in your environment to use Secrets Manager.
    """

    def __init__(self):
        self.backend = os.environ.get("TOKEN_STORE", "env")
        self.secret_name = os.environ.get("AWS_SECRET_NAME", "strava-mcp-tokens")
        self.env_path = Path(__file__).parent.parent / ".env"

    def get_tokens(self) -> dict:
        if self.backend == "aws":
            return self._get_from_secrets_manager()
        return self._get_from_env()

    def save_tokens(self, access_token: str, refresh_token: str, expires_at: int):
        if self.backend == "aws":
            self._save_to_secrets_manager(access_token, refresh_token, expires_at)
        else:
            self._save_to_env(access_token, refresh_token, expires_at)

    def _get_from_env(self) -> dict:
        return {
            "access_token": os.environ.get("STRAVA_ACCESS_TOKEN", ""),
            "refresh_token": os.environ.get("STRAVA_REFRESH_TOKEN", ""),
            "expires_at": int(os.environ.get("STRAVA_TOKEN_EXPIRES_AT", "0")),
        }

    def _save_to_env(self, access_token, refresh_token, expires_at):
        set_key(self.env_path, "STRAVA_ACCESS_TOKEN", access_token)
        set_key(self.env_path, "STRAVA_REFRESH_TOKEN", refresh_token)
        set_key(self.env_path, "STRAVA_TOKEN_EXPIRES_AT", str(expires_at))
        # Also update the live environment
        os.environ["STRAVA_ACCESS_TOKEN"] = access_token
        os.environ["STRAVA_REFRESH_TOKEN"] = refresh_token
        logging.debug("Tokens saved to .env")

    def _get_from_secrets_manager(self) -> dict:

        client = boto3.client("secretsmanager")
        response = client.get_secret_value(SecretId=self.secret_name)
        return json.loads(response["SecretString"])

    def _save_to_secrets_manager(self, access_token, refresh_token, expires_at):

        client = boto3.client("secretsmanager")
        client.put_secret_value(
            SecretId=self.secret_name,
            SecretString=json.dumps({
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_at": expires_at,
            })
        )
        logging.debug("Tokens saved to Secrets Manager")

token_store = TokenStore()