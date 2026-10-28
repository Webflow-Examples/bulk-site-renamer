# bulk-renamer

Renames Webflow sites in an Enterprise workspace through the Data API (`PATCH /v2/sites/{site_id}`). Python 3.9+, stdlib only, no install step.

For rename requests, use the `site-renamer` agent (`.claude/agents/site-renamer.md`).

## Files

| File | Purpose | Who runs it |
|---|---|---|
| `auth.py` | OAuth flow, writes token to `.env` | Human only |
| `check_auth.py` | Shows token scopes and workspace, never the token | Agent or human |
| `list_sites.py` | Lists sites as CSV on stdout | Agent or human |
| `rename.py` | Renames sites; dry run unless `--apply` | Agent (with approval) or human |
| `common.py` | `.env` helpers, API wrapper with 429 retry | — |

## Hard rules

- Never read, print, edit, or `source` `.env`, and never echo the token. Use `check_auth.py` to inspect auth.
- Never run `auth.py`. It needs a browser and the client secret. If auth is missing or broken, ask the human to run it.
- Always dry run first. Show the plan to the user and wait for explicit approval before `--apply`.
- Do not change scopes in `auth.py` or API behavior in `common.py` without asking.

## CSV format

```csv
site_id,new_name,current_name
6aa2dd2e2369b9df8d89220b,ix3-gsap-demo,sticky-scroll-builder
```

- `site_id` (required): 24-char hex ID. Never guess it; take it from `list_sites.py`.
- `new_name` (required): the new display name. Non-empty.
- `current_name` (optional, recommended for agents): the name you expect now. If the live name differs, that row fails and nothing changes for it.
- Header row required. One row per site; duplicate `site_id`s fail validation. Quote names that contain commas.
- `rename.py` validates the whole file before any API call.
- Write working files as `renames.csv` (gitignored). `renames.example.csv` is the committed sample.

## Workflow

1. `python3 check_auth.py` — must print `ok`.
2. `python3 list_sites.py [--filter TEXT] > sites.csv` — find site IDs.
3. Write `renames.csv`, copying `site_id` and `current_name` from `sites.csv`.
4. `python3 rename.py --csv renames.csv` — dry run; show the output to the user.
5. After approval: `python3 rename.py --csv renames.csv --apply`.
6. Report results and the `undo-*.csv` path it prints. Undo: `python3 rename.py --csv undo-<ts>.csv --apply`.

## Errors

| Output | Meaning | Action |
|---|---|---|
| `403 ... missing_scopes` | Token lacks a scope | Ask human to re-run `auth.py` |
| `401` | Token revoked or invalid | Ask human to re-run `auth.py` |
| `404` | Bad `site_id`, or site outside the authorized workspace | Re-check with `list_sites.py` |
| `live name is ... CSV expected ...` | Site changed since the CSV was written | Re-list, rewrite the row, dry run again |
| `rate limited, waiting Ns` | 429; the script retries | Nothing |

Note: the API docs list only `sites:write` for this endpoint, but it actually requires `workspace:write` too.
