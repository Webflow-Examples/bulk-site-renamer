"""Show what the saved token can do, without printing the token.

    python3 check_auth.py

Exits non-zero if a scope needed for renaming is missing.
"""
import sys

from common import api, token

NEEDED = {"sites:read", "sites:write", "workspace:write"}


def main():
    try:
        info = api("GET", "/token/introspect", token())
    except RuntimeError as e:
        sys.exit(f"Token check failed (revoked or invalid?): {e}")
    auth = info.get("authorization", {})
    scopes = {s.strip() for s in (auth.get("scope") or "").split(",") if s.strip()}
    targets = auth.get("authorizedTo", {})

    print(f"scopes:        {', '.join(sorted(scopes)) or '(none)'}")
    print(f"workspace ids: {', '.join(targets.get('workspaceIds') or []) or '(none)'}")
    print(f"site ids:      {', '.join(targets.get('siteIds') or []) or '(none)'}")

    missing = NEEDED - scopes
    if missing:
        sys.exit(f"Missing scopes: {', '.join(sorted(missing))}. Re-run auth.py.")
    print("ok")


if __name__ == "__main__":
    main()
