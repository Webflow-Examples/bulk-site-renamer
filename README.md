# bulk-renamer

Rename Webflow sites in bulk through the Data API. Built for Enterprise workspaces, where the MCP has no site-update tool. Python 3.9+, stdlib only.

## Setup

1. In Webflow: **Workspace settings → Apps & Integrations → Develop → Create app**.
   - Type: Data Client
   - Scopes: `sites:read`, `sites:write`, `workspace:read`, `workspace:write`
   - Redirect URI: `http://localhost:3000/callback`
2. `cp .env.example .env`, then add the client ID and secret.
3. `python3 auth.py`. On the consent screen, pick the **workspace**, not individual sites. The token is saved to `.env` and never printed.
4. `python3 check_auth.py` should print `ok`.

## Usage

```sh
python3 list_sites.py --filter demo > sites.csv     # find IDs
python3 rename.py --csv renames.csv                 # dry run
python3 rename.py --csv renames.csv --apply         # rename, writes undo-<ts>.csv
python3 rename.py <site_id> "New name" --apply      # single site
```

CSV format (see `renames.example.csv`):

```csv
site_id,new_name,current_name
6aa2dd2e2369b9df8d89220b,ix3-gsap-demo,sticky-scroll-builder
```

`current_name` is optional. When set, the row is skipped if the site's live name differs.

## Using with Claude Code

`CLAUDE.md` and `.claude/agents/site-renamer.md` let an agent drive this. Ask Claude Code to "rename these sites…" and it will list, write the CSV, dry run, and wait for your approval before applying. `.claude/settings.json` blocks the agent from reading `.env` or running `auth.py`.

## Security

- The token is a long-lived credential for the whole workspace. Revoke it by uninstalling the app from the workspace when you are done.
- `.env`, `renames.csv`, `sites.csv`, and `undo-*.csv` are gitignored. Keep it that way.
- Never paste the client secret or token into an AI tool.

## Gotcha

The endpoint docs list only `sites:write`, but the API returns `403 missing_scopes: workspace:write` without it. `auth.py` requests all four scopes.
