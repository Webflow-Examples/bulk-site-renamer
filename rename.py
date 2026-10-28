"""Rename Webflow sites. Dry run by default; pass --apply to make changes.

    python3 rename.py <site_id> <new_name> [--apply]
    python3 rename.py --csv renames.csv [--apply]

CSV columns: site_id,new_name[,current_name]
If current_name is set, a row is skipped when the site's live name differs.
--apply writes an undo CSV (undo-<timestamp>.csv) that reverses the run.
"""
import argparse
import csv
import sys
from datetime import datetime

from common import api, token

REQUIRED_COLUMNS = {"site_id", "new_name"}


def load_rows(args):
    if args.csv:
        with open(args.csv, newline="") as f:
            reader = csv.DictReader(f)
            missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
            if missing:
                sys.exit(f"{args.csv}: missing columns {', '.join(sorted(missing))}")
            rows = [{k: (v or "").strip() for k, v in row.items() if k} for row in reader]
        rows = [r for r in rows if r.get("site_id")]
    elif args.site_id and args.new_name:
        rows = [{"site_id": args.site_id, "new_name": args.new_name}]
    else:
        sys.exit("Pass <site_id> <new_name> or --csv <file>.")

    errors, seen = [], set()
    for i, r in enumerate(rows, start=2):
        if not r.get("new_name"):
            errors.append(f"row {i}: new_name is empty")
        if r["site_id"] in seen:
            errors.append(f"row {i}: duplicate site_id {r['site_id']}")
        seen.add(r["site_id"])
    if errors:
        sys.exit("CSV invalid, nothing changed:\n  " + "\n  ".join(errors))
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("site_id", nargs="?")
    parser.add_argument("new_name", nargs="?")
    parser.add_argument("--csv")
    parser.add_argument("--apply", action="store_true", help="actually rename (default is dry run)")
    args = parser.parse_args()

    rows = load_rows(args)
    tok = token()
    failures, undo = 0, []

    for r in rows:
        site_id, new_name, expected = r["site_id"], r["new_name"], r.get("current_name")
        try:
            current = api("GET", f"/sites/{site_id}", tok).get("displayName")
            if expected and current != expected:
                failures += 1
                print(f"FAIL  {site_id}  live name is '{current}', CSV expected '{expected}'")
                continue
            if current == new_name:
                print(f"skip  {site_id}  already '{new_name}'")
                continue
            if not args.apply:
                print(f"plan  {site_id}  '{current}' -> '{new_name}'")
                continue
            updated = api("PATCH", f"/sites/{site_id}", tok, {"name": new_name})
            print(f"done  {site_id}  '{current}' -> '{updated.get('displayName', new_name)}'")
            undo.append({"site_id": site_id, "new_name": current, "current_name": new_name})
        except RuntimeError as e:
            failures += 1
            print(f"FAIL  {site_id}  {e}")

    if undo:
        path = f"undo-{datetime.now():%Y%m%d-%H%M%S}.csv"
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["site_id", "new_name", "current_name"])
            writer.writeheader()
            writer.writerows(undo)
        print(f"\nUndo file: {path}  (python3 rename.py --csv {path} --apply)")
    if not args.apply:
        print("\nDry run. Re-run with --apply to rename.")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
