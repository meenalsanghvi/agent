"""Snapshot every KAM test-env resource this task may overwrite.

Three artifacts, all rollback inputs:
  1. catalogue_baseline.json  — GET /report/config/external (the before-picture)
  2. column_metadata.json     — current filterTags/description for every column our 15
                                merged configs expose. THIS is the rollback artifact for
                                the global-clobber scenario: columnMetadata is keyed
                                globally by columnName and a POST replaces the row.
  3. report_configs.json      — full Mongo documents (incl. id) for the 42 retired +
                                15 merged reportTypes. Rollback artifact for the de-list.

Usage:  HTTP_PROXY= HTTPS_PROXY= NO_PROXY="*" python3 snapshot_kam.py [--dir PATH]
Any failure is fatal: a partial snapshot is not a rollback path.
"""

import argparse
import glob
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

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
CONFIGS = os.path.join(REPO, "kam_report_configs")


def die(msg):
    sys.exit(f"FATAL: {msg}\n  → snapshot incomplete; do NOT proceed to any write phase.")


def merged_report_types():
    """reportTypes of the 15 merged configs, read from the merge specs."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    out = []
    for wave in ("merge_wave1", "merge_wave2", "merge_wave3"):
        out += [s["reportType"] for s in __import__(wave).SPECS]
    return sorted(set(out))


def exposed_columns():
    """Every externalColumnName the 15 merged configs expose (the clobber surface)."""
    want = set(merged_report_types())
    cols = set()
    for p in glob.glob(os.path.join(CONFIGS, "*", "*.json")):
        if "_retired" in p:
            continue
        d = json.load(open(p))
        if d.get("reportType") not in want:
            continue
        for sec in ("attributes", "metrics"):
            for c in (d.get(sec) or {}).values():
                if c.get("externalColumnName"):
                    cols.add(c["externalColumnName"])
    return sorted(cols)


def retired_report_types():
    return sorted(json.load(open(p))["reportType"]
                  for p in glob.glob(os.path.join(CONFIGS, "_retired", "*.json")))


def get(path, params, what):
    try:
        r = S.get(f"{BASE}{path}", params=params, headers=H, timeout=90)
    except Exception as e:
        die(f"{what}: {type(e).__name__}: {e}")
    if r.status_code != 200:
        die(f"{what}: HTTP {r.status_code} {r.text[:200]}")
    return r.json()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=None)
    args = ap.parse_args()

    outdir = args.dir or os.path.join(REPO, "scripts", "out", "snapshot")
    os.makedirs(outdir, exist_ok=True)

    # 1 — catalogue
    cat = get("/kamService/report/config/external", {"application": APP}, "catalogue")
    reps = cat.get("reports", [])
    if not reps:
        die("catalogue returned 0 reports — refusing to snapshot an empty baseline")
    json.dump(cat, open(os.path.join(outdir, "catalogue_baseline.json"), "w"), indent=2)

    # 2 — columnMetadata for our exposed columns
    cols = exposed_columns()
    if not cols:
        die("computed 0 exposed columns — the config glob is wrong")
    body = get("/kamService/report/column-metadata",
               {"jsonQuery": json.dumps({"columnNames": cols})}, "columnMetadata")
    rows = body.get("columns") or body.get("data") or (body if isinstance(body, list) else [])
    cm = {x.get("columnName"): {"filterTags": sorted(x.get("filterTags") or []),
                                "description": x.get("description", "")}
          for x in rows}
    json.dump({"requested": cols, "found": cm},
              open(os.path.join(outdir, "column_metadata.json"), "w"), indent=2)

    # 3 — config documents
    want = retired_report_types() + merged_report_types()
    docs = {}
    for rt in want:
        q = json.dumps({"reportTypes": [rt], "application": APP})
        found = get("/kamService/report/config", {"jsonQuery": q}, f"config {rt}").get("reports", [])
        if found:
            docs[rt] = found
    json.dump(docs, open(os.path.join(outdir, "report_configs.json"), "w"), indent=2)

    # ---- report ----
    shared = {n: v for n, v in cm.items()
              if any(not t.startswith("report_group:") for t in v["filterTags"])}
    print(f"snapshot dir: {outdir}")
    print(f"  catalogue        : {len(reps)} reports")
    print(f"  columnMetadata   : {len(cm)}/{len(cols)} of our exposed columns found live")
    print(f"  config documents : {len(docs)}/{len(want)} reportTypes found in Mongo")
    print(f"\n  SHARED columns (carry non-report_group tags — the dangerous ones): {len(shared)}")
    for n, v in sorted(shared.items()):
        foreign = [t for t in v["filterTags"] if not t.startswith("report_group:")]
        print(f"    {n:34s} {foreign}")
    missing = [c for c in cols if c not in cm]
    if missing:
        print(f"\n  not yet in columnMetadata ({len(missing)}, will be created): {missing}")
    print(f"\nRollback available: {len(cm)} columns, {len(docs)} config documents, "
          f"snapshot at {outdir}")


if __name__ == "__main__":
    main()
