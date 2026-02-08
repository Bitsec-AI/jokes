#!/usr/bin/env python3
"""Basilica login script — replicates `basilica login` and `basilica login --device-code`."""

import argparse
import http.server
import json
import os
import secrets
import sys
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
from hashlib import sha256
from base64 import urlsafe_b64encode
from pathlib import Path

AUTH0_DOMAIN = os.environ.get(
    "BASILICA_AUTH0_DOMAIN", "auth.basilica.ai"
)
AUTH0_CLIENT_ID = os.environ.get(
    "BASILICA_AUTH0_CLIENT_ID", "KXOhOXiQiLdD3JUfHWesdlNqBlXBDQ0E"
)
AUTH0_BASE = f"https://{AUTH0_DOMAIN}"
TOKEN_URL = f"{AUTH0_BASE}/oauth/token"
AUTHORIZE_URL = f"{AUTH0_BASE}/authorize"
DEVICE_CODE_URL = f"{AUTH0_BASE}/oauth/device/code"
AUDIENCE = "https://api.basilica.ai/"

AUTH_DIR = Path(
    os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")
) / "basilica"
AUTH_FILE = AUTH_DIR / "auth.json"

REDIRECT_PORT = 8249
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}/callback"


def save_tokens(token_data: dict) -> None:
    AUTH_DIR.mkdir(parents=True, exist_ok=True)
    AUTH_FILE.write_text(json.dumps(token_data, indent=2))
    AUTH_FILE.chmod(0o600)
    print(f"Credentials saved to {AUTH_FILE}")


def _post(url: str, data: dict) -> dict:
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()
        print(f"HTTP {e.code}: {err_body}", file=sys.stderr)
        raise


# ── Browser-based PKCE login ──────────────────────────────────────────────


def login_browser() -> None:
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = (
        urlsafe_b64encode(sha256(code_verifier.encode()).digest())
        .rstrip(b"=")
        .decode()
    )
    state = secrets.token_urlsafe(32)

    params = urllib.parse.urlencode(
        {
            "response_type": "code",
            "client_id": AUTH0_CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "scope": "openid profile email offline_access rentals:* nodes:list keys:create keys:list keys:revoke secure_cloud",
            "audience": AUDIENCE,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
    )
    auth_url = f"{AUTHORIZE_URL}?{params}"

    result = {}

    class CallbackHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if qs.get("state", [None])[0] != state:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"State mismatch")
                return
            if "error" in qs:
                result["error"] = qs["error"][0]
            else:
                result["code"] = qs["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<html><body><h2>Login successful! You can close this tab.</h2></body></html>"
            )

        def log_message(self, *_):
            pass

    server = http.server.HTTPServer(("127.0.0.1", REDIRECT_PORT), CallbackHandler)
    server.timeout = 120

    print("Opening browser for login...")
    webbrowser.open(auth_url)

    server.handle_request()
    server.server_close()

    if "error" in result:
        print(f"Auth error: {result['error']}", file=sys.stderr)
        sys.exit(1)
    if "code" not in result:
        print("No authorization code received.", file=sys.stderr)
        sys.exit(1)

    token_data = _post(
        TOKEN_URL,
        {
            "grant_type": "authorization_code",
            "client_id": AUTH0_CLIENT_ID,
            "code": result["code"],
            "redirect_uri": REDIRECT_URI,
            "code_verifier": code_verifier,
        },
    )
    save_tokens(token_data)
    print("Logged in successfully.")


# ── Device-code login ─────────────────────────────────────────────────────


def login_device_code() -> None:
    resp = _post(
        DEVICE_CODE_URL,
        {
            "client_id": AUTH0_CLIENT_ID,
            "scope": "openid profile email offline_access rentals:* nodes:list keys:create keys:list keys:revoke secure_cloud",
            "audience": AUDIENCE,
        },
    )

    print(f"\n  Open:  {resp['verification_uri_complete']}", flush=True)
    print(f"  Code:  {resp['user_code']}\n", flush=True)
    print("Waiting for authorization...", flush=True)

    device_code = resp["device_code"]
    interval = resp.get("interval", 5)
    expires_at = time.time() + resp.get("expires_in", 900)

    poll_data = {
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        "client_id": AUTH0_CLIENT_ID,
        "device_code": device_code,
    }

    while time.time() < expires_at:
        time.sleep(interval)
        body = urllib.parse.urlencode(poll_data).encode()
        req = urllib.request.Request(
            TOKEN_URL, data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        try:
            with urllib.request.urlopen(req) as resp:
                token_data = json.loads(resp.read())
            save_tokens(token_data)
            print("Logged in successfully.")
            return
        except urllib.error.HTTPError as e:
            err_body = e.read().decode()
            try:
                err_json = json.loads(err_body)
            except json.JSONDecodeError:
                print(f"HTTP {e.code}: {err_body}", file=sys.stderr)
                sys.exit(1)
            err = err_json.get("error")
            if err == "authorization_pending":
                continue
            elif err == "slow_down":
                interval += 5
                continue
            else:
                print(f"Auth error: {err} — {err_json.get('error_description', '')}", file=sys.stderr)
                sys.exit(1)

    print("Device code expired. Please try again.", file=sys.stderr)
    sys.exit(1)


# ── Logout ────────────────────────────────────────────────────────────────


def logout() -> None:
    if AUTH_FILE.exists():
        AUTH_FILE.unlink()
        print("Logged out. Credentials removed.")
    else:
        print("No stored credentials found.")


# ── Token creation ────────────────────────────────────────────────────────

API_BASE = "https://api.basilica.ai"
API_TOKEN_FILE = Path("basilica_api_token.json")


def _get_access_token() -> str:
    """Load access token from auth.json, refreshing if needed."""
    if not AUTH_FILE.exists():
        print("Not logged in. Run: python basilica_login.py login", file=sys.stderr)
        sys.exit(1)
    data = json.loads(AUTH_FILE.read_text())
    access_token = data.get("access_token")
    refresh_token = data.get("refresh_token")
    if not access_token:
        print("No access token in auth file. Please login again.", file=sys.stderr)
        sys.exit(1)
    if refresh_token:
        try:
            refreshed = _post(
                TOKEN_URL,
                {
                    "grant_type": "refresh_token",
                    "client_id": AUTH0_CLIENT_ID,
                    "refresh_token": refresh_token,
                },
            )
            save_tokens(refreshed)
            return refreshed["access_token"]
        except Exception:
            pass
    return access_token


def tokens_create(name: str | None = None) -> None:
    """Create an API token and save it to basilica_api_token.json."""
    token = _get_access_token()
    if not name:
        name = "cli-token"

    url = f"{API_BASE}/api-keys"
    data = json.dumps({"name": name}).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            API_TOKEN_FILE.write_text(json.dumps(result, indent=2))
            API_TOKEN_FILE.chmod(0o600)
            print(f"API token created and saved to {API_TOKEN_FILE}")
            print("IMPORTANT: Keep this file safe. The token won't be shown again.")
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()
        print(f"API error ({e.code}): {err_body}", file=sys.stderr)
        sys.exit(1)


# ── Token management ────────────────────────────────────────────────────────


def show_status() -> None:
    if AUTH_FILE.exists():
        data = json.loads(AUTH_FILE.read_text())
        print(f"Auth file: {AUTH_FILE}")
        print(f"Has access_token:  {'access_token' in data}")
        print(f"Has refresh_token: {'refresh_token' in data}")
        if "expires_in" in data:
            print(f"Token expires_in:  {data['expires_in']}s")
    elif os.environ.get("BASILICA_API_TOKEN"):
        print("Using BASILICA_API_TOKEN environment variable.")
    else:
        print("Not logged in. Run: python basilica_login.py login")


# ── CLI ───────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="Basilica authentication")
    sub = parser.add_subparsers(dest="command")

    login_p = sub.add_parser("login", help="Log in to Basilica")
    login_p.add_argument(
        "--browser", action="store_true", help="Use browser PKCE flow (requires Auth0 callback whitelist)"
    )

    sub.add_parser("logout", help="Remove stored credentials")
    sub.add_parser("status", help="Show auth status")

    tokens_p = sub.add_parser("tokens", help="Manage API tokens")
    tokens_sub = tokens_p.add_subparsers(dest="tokens_command")
    create_p = tokens_sub.add_parser("create", help="Create a new API token")
    create_p.add_argument("--name", help="Optional token name")

    args = parser.parse_args()

    if args.command == "login":
        # Device-code is the default — browser PKCE requires a callback URL
        # whitelisted in Auth0, which we don't control.
        if args.browser:
            login_browser()
        else:
            login_device_code()
    elif args.command == "logout":
        logout()
    elif args.command == "status":
        show_status()
    elif args.command == "tokens":
        if args.tokens_command == "create":
            tokens_create(args.name)
        else:
            tokens_p.print_help()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
