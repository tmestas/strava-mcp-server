import logging
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse
from auth import get_authorization_url, exchange_code
from token_manager import token_manager
from token_store import token_store

app = FastAPI()

@app.get("/auth")
def auth():
    """Kick off the Strava OAuth flow."""
    url = get_authorization_url()
    logging.debug(f"Redirecting to Strava auth: {url}")
    return RedirectResponse(url)

@app.get("/callback")
def callback(code: str = None, error: str = None):
    """Handle the Strava OAuth callback."""
    if error or not code:
        return HTMLResponse("<h2>❌ Authorization denied.</h2>", status_code=400)

    token_response = exchange_code(code)
    token_manager.update_from_token_response(token_response)
    token_store.save_tokens(
        access_token=token_response["access_token"],
        refresh_token=token_response["refresh_token"],
        expires_at=token_response["expires_at"],
    )
    logging.debug("OAuth flow complete, tokens saved")
    return HTMLResponse("<h2>✅ Authenticated with Strava! You can close this tab.</h2>")

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)