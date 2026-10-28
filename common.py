"""Shared helpers: .env read/write and Webflow API requests (stdlib only)."""
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ENV_PATH = Path(__file__).parent / ".env"
API_BASE = "https://api.webflow.com/v2"
USER_AGENT = "bulk-renamer/0.1"
MAX_RETRIES = 3


def load_env():
    if not ENV_PATH.exists():
        sys.exit("No .env found. Copy .env.example to .env and fill in the app credentials.")
    values = {}
    for line in ENV_PATH.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def require(env, *keys):
    missing = [k for k in keys if not env.get(k)]
    if missing:
        sys.exit(f"Missing in .env: {', '.join(missing)}")


def token():
    env = load_env()
    require(env, "WEBFLOW_ACCESS_TOKEN")
    return env["WEBFLOW_ACCESS_TOKEN"]


def set_env_value(key, value):
    lines = ENV_PATH.read_text().splitlines()
    for i, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[i] = f"{key}={value}"
            break
    else:
        lines.append(f"{key}={value}")
    ENV_PATH.write_text("\n".join(lines) + "\n")


def api(method, path, token, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        f"{API_BASE}{path}",
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        },
    )
    for attempt in range(MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read() or b"{}")
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < MAX_RETRIES:
                wait = int(e.headers.get("Retry-After") or 60)
                print(f"rate limited, waiting {wait}s", file=sys.stderr)
                time.sleep(wait)
                continue
            raise RuntimeError(f"{method} {path} -> {e.code}: {e.read().decode(errors='replace')}") from None
