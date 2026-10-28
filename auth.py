"""One-time OAuth flow.

Opens the Webflow consent screen, catches the redirect on localhost, exchanges
the code for an access token, and saves it to .env. The token is never printed.

    python3 auth.py
"""
import json
import secrets
import sys
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

from common import USER_AGENT, load_env, require, set_env_value

AUTHORIZE_URL = "https://webflow.com/oauth/authorize"
TOKEN_URL = "https://api.webflow.com/oauth/access_token"
SCOPES = "sites:read sites:write workspace:read workspace:write"


def main():
    env = load_env()
    require(env, "WEBFLOW_CLIENT_ID", "WEBFLOW_CLIENT_SECRET", "WEBFLOW_REDIRECT_URI")
    redirect = urllib.parse.urlparse(env["WEBFLOW_REDIRECT_URI"])
    state = secrets.token_urlsafe(16)
    result = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            url = urllib.parse.urlparse(self.path)
            if url.path != redirect.path:
                self.send_response(404)
                self.end_headers()
                return
            params = urllib.parse.parse_qs(url.query)
            result["code"] = params.get("code", [None])[0]
            result["state"] = params.get("state", [None])[0]
            result["error"] = params.get("error_description", params.get("error", [None]))[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Done. You can close this tab and return to the terminal.")

        def log_message(self, *args):
            pass

    query = urllib.parse.urlencode({
        "response_type": "code",
        "client_id": env["WEBFLOW_CLIENT_ID"],
        "redirect_uri": env["WEBFLOW_REDIRECT_URI"],
        "scope": SCOPES,
        "state": state,
    })
    auth_url = f"{AUTHORIZE_URL}?{query}"

    server = HTTPServer((redirect.hostname, redirect.port or 80), Handler)
    print("Opening the Webflow consent screen. Choose the workspace, not individual sites.")
    print(f"If the browser does not open, visit:\n{auth_url}\n")
    webbrowser.open(auth_url)
    while not result:
        server.handle_request()
    server.server_close()

    if result.get("error") or not result.get("code"):
        sys.exit(f"Authorization failed: {result.get('error') or 'no code returned'}")
    if result.get("state") != state:
        sys.exit("State mismatch, aborting.")

    body = urllib.parse.urlencode({
        "client_id": env["WEBFLOW_CLIENT_ID"],
        "client_secret": env["WEBFLOW_CLIENT_SECRET"],
        "code": result["code"],
        "grant_type": "authorization_code",
        "redirect_uri": env["WEBFLOW_REDIRECT_URI"],
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=body, method="POST", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req) as resp:
            token = json.loads(resp.read()).get("access_token")
    except urllib.error.HTTPError as e:
        sys.exit(f"Token exchange failed: {e.code}")
    if not token:
        sys.exit("Token exchange returned no access_token.")

    set_env_value("WEBFLOW_ACCESS_TOKEN", token)
    print("Access token saved to .env.")


if __name__ == "__main__":
    main()
