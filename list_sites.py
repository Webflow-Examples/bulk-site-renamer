"""List sites the token can see, as CSV on stdout.

    python3 list_sites.py
    python3 list_sites.py --filter demo > sites.csv

Columns: site_id,current_name,short_name,workspace_id,last_published
"""
import argparse
import csv
import sys

from common import api, token


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--filter", help="case-insensitive substring match on name or short name")
    args = parser.parse_args()

    sites = api("GET", "/sites", token()).get("sites", [])
    if args.filter:
        needle = args.filter.lower()
        sites = [s for s in sites if needle in (s.get("displayName") or "").lower() or needle in (s.get("shortName") or "").lower()]

    writer = csv.writer(sys.stdout)
    writer.writerow(["site_id", "current_name", "short_name", "workspace_id", "last_published"])
    for s in sites:
        writer.writerow([s.get("id"), s.get("displayName"), s.get("shortName"), s.get("workspaceId"), s.get("lastPublished") or ""])


if __name__ == "__main__":
    main()
