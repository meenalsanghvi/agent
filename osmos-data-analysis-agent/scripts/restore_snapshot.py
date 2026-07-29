"""Restore KAM test-env state from a snapshot_kam.py snapshot.

The break-glass script. Two independent restores:

  --columns   re-POST the snapshotted columnMetadata verbatim. Use when a filterTags
              shrink is detected (the global-clobber scenario).
  --configs   re-POST the snapshotted report config documents verbatim, by Mongo id.
              Use when a de-list or an in-place update went wrong.

Both are exact restores of what was live at snapshot time -- NOT merges. That is the
point: after a clobber you want the old state back, not a union with the bad state.

Usage:
  HTTP_PROXY= HTTPS_PROXY= NO_PROXY="*" python3 restore_snapshot.py \
      --dir out/snapshot_YYYYmmdd_HHMMSS [--columns] [--configs] [--dry-run]

Safety: refuses to restore a config document whose reportType does not match
^INTERNAL_PERF_ , so this can never write another team's report.
"""

import argparse
import json
import os
import re
import sys

import requests

BASE = "http://test.onlinesales.ai"
APP = "irisTestApplication"
H = {"Content-Type": "application/json"}
S = requests.Session()
S.trust_env = False

OURS = re.compile(r"^INTERNAL_PERF_")


def restore_columns(snap, dry):
    data = json.load(open(os.path.join(snap, "column_metadata.json")))
    found = data["found"]
    cols = [{"columnName": n,
             "description": v.get("description", ""),
             "filterTags": v.get("filterTags", [])}
            for n, v in sorted(found.items())]
    print(f"[columns] restoring {len(cols)} columns to their snapshot filterTags")
    for c in cols[:5]:
        print(f"    e.g. {c['columnName']}: {c['filterTags']}")
    if dry:
        print("[columns] dry-run — not posting")
        return
    r = S.post(f"{BASE}/kamService/report/column-metadata",
               data=json.dumps({"application": APP, "columns": cols}), headers=H, timeout=120)
    print(f"[columns] POST {r.status_code} {r.text[:200]}")


def restore_configs(snap, dry):
    """Restore each config's externalReportType (catalogue membership).

    IMPORTANT: this deliberately restores ONLY externalReportType, not whole documents.
    /report/config serves a UI projection -- `attributes` comes back as [{label, value}]
    rather than the selector map -- so the snapshot is NOT a faithful copy of the stored
    config and must never be posted back wholesale: doing so would replace each config's
    real attributes with a label list. externalReportType is the only field this task
    ever changes, so it is the only field that needs undoing. To rebuild a config's body,
    re-post from the JSON file on disk via post_external.py.
    """
    docs = json.load(open(os.path.join(snap, "report_configs.json")))
    print(f"[configs] {len(docs)} reportTypes in snapshot — restoring externalReportType only")
    for rt, found in sorted(docs.items()):
        if not OURS.match(rt):
            print(f"  SKIP (not ours): {rt}")
            continue
        if len(found) != 1:
            print(f"  SKIP ({len(found)} docs, expected 1): {rt}")
            continue
        doc = found[0]
        eid = doc.get("id") or doc.get("_id")
        if isinstance(eid, dict):
            eid = eid.get("$oid")
        if not eid:
            print(f"  SKIP (no id): {rt}")
            continue
        ext = doc.get("externalReportType")
        if not ext:
            print(f"  skip {rt}: was already de-listed at snapshot time")
            continue
        if dry:
            print(f"  would restore {rt} → id {eid}  externalReportType={ext}")
            continue
        body = {"application": APP, "id": eid,
                "cacheInfo": doc.get("cacheInfo") or {"isCachingEnabled": True,
                                                      "cachingExpiryInSec": 900},
                "externalReportType": ext}
        r = S.post(f"{BASE}/kamService/report/config",
                   data=json.dumps(body), headers=H, timeout=90)
        print(f"  {rt}: {r.status_code} {'' if r.status_code == 200 else r.text[:160]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--columns", action="store_true")
    ap.add_argument("--configs", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if not os.path.isdir(a.dir):
        sys.exit(f"no such snapshot dir: {a.dir}")
    if not (a.columns or a.configs):
        sys.exit("pick at least one of --columns / --configs")

    if a.columns:
        restore_columns(a.dir, a.dry_run)
    if a.configs:
        restore_configs(a.dir, a.dry_run)


if __name__ == "__main__":
    main()
