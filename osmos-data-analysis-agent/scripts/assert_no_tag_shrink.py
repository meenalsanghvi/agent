"""Assert no column's filterTags shrank versus the snapshot.

This is the guard for the global-clobber failure mode: columnMetadata is keyed globally
by columnName, a POST *replaces* the row, and a column is usable by a report only if
their filterTags intersect. So a lost tag silently removes a column from somebody else's
report -- no error, no log. The only way to catch it is to diff.

Rule enforced: for every column in the snapshot, live_tags MUST be a superset of
snapshot_tags. Growth is fine (that is what the merge is for). Any shrink is a P0.

Usage:
  HTTP_PROXY= HTTPS_PROXY= NO_PROXY="*" python3 assert_no_tag_shrink.py --dir <snapshot>

Exit 0 = safe. Exit 1 = a tag was lost; restore immediately:
  python3 restore_snapshot.py --dir <snapshot> --columns
"""

import argparse
import json
import os
import sys

import requests

BASE = "http://test.onlinesales.ai"
H = {"Content-Type": "application/json"}
S = requests.Session()
S.trust_env = False

# The columns most likely to break another team's report if they lose a tag.
CANONICAL = ["spend", "clicks", "impressions", "ctr", "cpc", "cpm", "requests",
             "responses", "date", "page_type", "campaign_id", "os_client_id"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--quiet", action="store_true", help="only print problems and the verdict")
    a = ap.parse_args()

    snap = json.load(open(os.path.join(a.dir, "column_metadata.json")))["found"]
    names = sorted(snap)

    r = S.get(f"{BASE}/kamService/report/column-metadata",
              params={"jsonQuery": json.dumps({"columnNames": names})}, headers=H, timeout=120)
    if r.status_code != 200:
        sys.exit(f"FATAL: columnMetadata GET {r.status_code} — cannot verify, assume unsafe")
    body = r.json()
    rows = body.get("columns") or body.get("data") or (body if isinstance(body, list) else [])
    live = {x.get("columnName"): set(x.get("filterTags") or []) for x in rows}

    shrunk, grown, gone = [], [], []
    for n in names:
        before = set(snap[n]["filterTags"])
        if n not in live:
            gone.append(n)
            continue
        after = live[n]
        if not before <= after:
            shrunk.append((n, sorted(before - after), sorted(before), sorted(after)))
        elif after > before:
            grown.append((n, sorted(after - before)))

    if not a.quiet and grown:
        print(f"tags GREW on {len(grown)} columns (expected, safe):")
        for n, added in grown[:15]:
            print(f"    + {n:32s} {added}")
        if len(grown) > 15:
            print(f"    … and {len(grown) - 15} more")

    if gone:
        print(f"\n❌ {len(gone)} columns VANISHED from columnMetadata: {gone}")
    if shrunk:
        print(f"\n❌ {len(shrunk)} columns LOST tags — this is the clobber signature:")
        for n, lost, b, af in shrunk:
            mark = "  ⚠ CANONICAL/SHARED" if n in CANONICAL else ""
            print(f"    {n}{mark}\n        lost   {lost}\n        before {b}\n        after  {af}")

    if shrunk or gone:
        print(f"\nVERDICT: UNSAFE — restore now:\n"
              f"  HTTP_PROXY= HTTPS_PROXY= NO_PROXY='*' python3 restore_snapshot.py "
              f"--dir {a.dir} --columns")
        return 1

    print(f"\n✅ VERDICT: SAFE — {len(names)} columns checked, "
          f"{len(grown)} grew, 0 shrank, 0 vanished.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
