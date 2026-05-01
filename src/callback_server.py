import webbrowser
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from auth import get_authorization_url, exchange_code
from token_manager import token_manager


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/auth":
            # Redirect to Strava
            url = get_authorization_url()
            self.send_response(302)
            self.send_header("Location", url)
            self.end_headers()

        elif parsed.path == "/callback":
            params = parse_qs(parsed.query)

            if "error" in params:
                self._respond(400, "Authorization denied by user.")
                return

            code = params.get("code", [None])[0]
            if not code:
                self._respond(400, "No code in callback.")
                return

            # Exchange the code for tokens
            token_response = exchange_code(code)
            token_manager.update_from_token_response(token_response)

            self._respond(200, "✅ Authenticated with Strava! You can close this tab.")

            # Shut the server down after successful auth
            threading.Thread(target=self.server.shutdown).start()

        else:
            self._respond(404, "Not found.")

    def _respond(self, status, message):
        self.send_response(status)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(f"<h2>{message}</h2>".encode())

    def log_message(self, format, *args):
        pass  # Suppress request logs


def run_oauth_flow(port: int = 8000):
    """Start the callback server and open the browser to kick off the OAuth flow."""
    server = HTTPServer(("localhost", port), CallbackHandler)
    print(f"Starting OAuth flow at http://localhost:{port}/auth")
    webbrowser.open(f"http://localhost:{port}/auth")
    server.serve_forever()
    print("OAuth flow complete — tokens saved.")


if __name__ == "__main__":
    run_oauth_flow()