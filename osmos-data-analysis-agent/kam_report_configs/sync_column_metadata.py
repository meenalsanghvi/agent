#!/usr/bin/env python3
"""
sync_column_metadata.py — safe, MERGE-based columnMetadata sync (fixes the global-clobber bug)
==============================================================================================
columnMetadata is keyed GLOBALLY by columnName; a POST REPLACES that column's filterTags.
Our per-report posts therefore overwrote shared/production columns (e.g. `clicks`, `spend`),
stripping their production tags in the test env and breaking other reports (BEATS/PULSE/
LOCALIUM). And a column is usable by a report only if its columnMetadata.filterTags INTERSECT
the report's filterTags (externalNameTranslatorHelper.buildMappings).

This script computes, for every column ANY of our inline+external configs exposes:
    merged_filterTags = union(
        production-file tags   (kamService/config/columnMetadata.json — authoritative),
        current test-env tags  (preserve anything already there),
        our tags               (every report_group tag of every OUR config exposing it),
    )
and posts the merged entry. This RESTORES production tags AND adds ours → every report
(theirs and ours) can use the column simultaneously. Union-only: it never removes a tag.

Run:  HTTP_PROXY= HTTPS_PROXY= NO_PROXY="*" python3 sync_column_metadata.py [--dry-run]
"""
from __future__ import annotations
import glob, json, os, sys
import requests

BASE = "http://test-data.onlinesales.ai"; APP = "irisTestApplication"
H = {"Content-Type": "application/json"}
# A checkout of kamService, for the production columnMetadata baseline. There is no
# API for it, and without it the union merge silently degrades into the global clobber
# it exists to prevent — so `prod_tags()` raises rather than defaulting.
PROD_FILE = os.environ.get(
    "KAM_SERVICE_COLUMN_METADATA",
    os.path.expanduser("~/kamService/config/columnMetadata.json"),
)
S = requests.Session(); S.trust_env = False


def our_columns():
    """{externalColumnName: {"tags": set(report filterTags), "desc": str}} across our configs."""
    cols: dict[str, dict] = {}
    for f in glob.glob("**/*.json", recursive=True):
        if "columnMetadata" in f:
            continue
        # _retired/ configs are superseded and being de-listed; folding their filterTags
        # back into the union would keep dead report_group tags alive on shared columns.
        if "_retired" in f.split(os.sep):
            continue
        try:
            c = json.load(open(f))
        except Exception:
            continue
        rt = c.get("filterTags") or []
        if not c.get("externalReportType"):
            continue  # only external-exposed configs contribute
        for sec in ("attributes", "metrics"):
            for d in (c.get(sec) or {}).values():
                if not isinstance(d, dict):
                    continue
                ext = d.get("externalColumnName")
                if not ext:
                    continue
                e = cols.setdefault(ext, {"tags": set(), "desc": ""})
                e["tags"].update(rt)
                if not e["desc"]:
                    e["desc"] = d.get("description", "")
    return cols


def prod_tags():
    """Production-file tags. RAISES on failure -- never returns {}.

    Returning {} here silently removes one of the three inputs to the union, which
    turns this protective merge into exactly the global clobber it exists to prevent.
    A missing production file must stop the run, not degrade it.
    """
    try:
        cols = json.load(open(PROD_FILE))["columns"]
    except Exception as exc:
        raise SystemExit(
            f"FATAL: cannot read production columnMetadata at {PROD_FILE}: {exc}\n"
            "  Without it the merge loses production filterTags and will clobber shared\n"
            "  columns (the incident recorded in AUTHORING_STATUS.md). Fix the path first."
        )
    return {c["columnName"]: {"tags": set(c.get("filterTags") or []),
                              "desc": c.get("description", "")} for c in cols}


def current_tags(names):
    """Live test-env tags. RAISES on a non-200 -- never returns {} (see prod_tags)."""
    out = {}
    r = S.get(f"{BASE}/kamService/report/column-metadata",
              params={"jsonQuery": json.dumps({"columnNames": names})}, headers=H, timeout=90)
    if r.status_code != 200:
        raise SystemExit(
            f"FATAL: columnMetadata GET returned {r.status_code}: {r.text[:200]}\n"
            "  Cannot merge against live tags we failed to read -- posting now would\n"
            "  strip whatever is currently there. Aborting."
        )
    body = r.json()
    rows = body.get("columns") or body.get("data") or (body if isinstance(body, list) else [])
    for x in rows:
        out[x.get("columnName")] = set(x.get("filterTags") or [])
    return out


def main():
    dry = "--dry-run" in sys.argv
    ours = our_columns()
    prod = prod_tags()
    cur = current_tags(sorted(ours))
    payload, restored = [], []
    for name, info in sorted(ours.items()):
        p = prod.get(name, {}).get("tags", set())
        c = cur.get(name, set())
        merged = sorted(p | c | info["tags"])
        # flag columns where production tags were missing from the current (test) state => we had clobbered them
        if p and not p.issubset(c):
            restored.append(f"{name}: restored {sorted(p - c)} (had {sorted(c)})")
        desc = prod.get(name, {}).get("desc") or info["desc"] or name
        payload.append({"columnName": name, "description": desc, "filterTags": merged})

    print(f"columns to sync: {len(payload)} | production collisions restored: {len(restored)}")
    for r in restored:
        print("  RESTORE", r)
    if dry:
        print("[dry-run] not posting"); return
    resp = S.post(f"{BASE}/kamService/report/column-metadata",
                  data=json.dumps({"application": APP, "columns": payload}), headers=H, timeout=120)
    print("POST", resp.status_code, resp.text[:160])


if __name__ == "__main__":
    main()
