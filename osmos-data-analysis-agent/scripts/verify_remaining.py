"""Verify the 26 active configs that were NOT part of the consolidation.

The 15 merged reports are verified (posted, fetched, numerically diffed). These 26 were
validated in earlier authoring waves but not re-checked since; this re-establishes their
current state on the test env in one pass.

Per config: request EVERY exposed column. That is the strong test -- it proves each
column resolves through the external catalogue AND compiles in BigQuery. If the full
grain is too heavy, fall back to the first two attributes so a timeout is not mistaken
for a broken config, and record which attempt was used.

Fetches are strictly sequential. Verdicts:
  OK      rows returned
  EMPTY   HTTP 200, 0 rows for the tested scope (config is sound; data may not exist)
  ERROR   non-200 or transport failure -- captured verbatim for separate follow-up

Usage: HTTP_PROXY= HTTPS_PROXY= NO_PROXY="*" python3 verify_remaining.py
"""

import glob
import json
import os
import sys
import time

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from merge_lib import ROOT  # noqa: E402

BASE = "http://test.onlinesales.ai"
APP = "irisTestApplication"
H = {"Content-Type": "application/json"}
S = requests.Session()
S.trust_env = False
AGENCY = 105
WINDOW = [{"startDate": "2026-07-19", "endDate": "2026-07-21"}]

# Known-good scoping values for agency 105 (REMAINING_QUEUE.md).
FILTER_VALUES = {
    "os_client_id": ["277661"],
    "campaign_id": ["1322334"],
    "keyword": ["iphone"],
    "search_query": ["iphone"],
    "page_type": ["search"],
}


def merged_types():
    out = set()
    for w in ("merge_wave1", "merge_wave2", "merge_wave3"):
        out |= {s["reportType"] for s in __import__(w).SPECS}
    return out


def ext_cols(cfg, section):
    return [c["externalColumnName"] for c in (cfg.get(section) or {}).values()
            if c.get("externalColumnName")]


def fetch(ext_rt, attrs, metrics, filters, tmo):
    body = {"application": APP, "agencyId": AGENCY, "reportType": ext_rt,
            "requestType": "REPORTING", "useExternalNames": True,
            "attributes": attrs, "metrics": metrics or ["placeholder_metric"],
            "dateRanges": WINDOW, "filters": filters, "limit": 50, "offset": 0}
    try:
        r = S.post(f"{BASE}/kamService/report/fetch", data=json.dumps(body),
                   headers=H, timeout=tmo)
    except Exception as e:
        return None, f"{type(e).__name__}"
    if r.status_code != 200:
        try:
            msg = r.json().get("message", r.text)
        except Exception:
            msg = r.text
        return None, " ".join(str(msg).split())[:300]
    return r.json().get("data", []), "ok"


def main():
    merged = merged_types()
    targets = []
    for p in sorted(glob.glob(os.path.join(ROOT, "*", "*.json"))):
        if "_retired" in p:
            continue
        d = json.load(open(p))
        if d["reportType"] in merged:
            continue
        targets.append((d, os.path.relpath(p, ROOT)))

    print(f"Verifying {len(targets)} non-consolidated configs — agency {AGENCY}, "
          f"{WINDOW[0]['startDate']}→{WINDOW[0]['endDate']}\n")

    results = []
    for i, (cfg, path) in enumerate(sorted(targets, key=lambda t: t[0]["reportType"]), 1):
        rt, ext = cfg["reportType"], cfg.get("externalReportType")
        attrs, mets = ext_cols(cfg, "attributes"), ext_cols(cfg, "metrics")
        filters = [{"key": k, "operator": "IN", "values": FILTER_VALUES[k]}
                   for k in (cfg.get("externalRequiredFilters") or [])
                   if k in FILTER_VALUES]
        unscoped_req = [k for k in (cfg.get("externalRequiredFilters") or [])
                        if k not in FILTER_VALUES]

        data, status = fetch(ext, attrs, mets, filters, 90)
        attempt = "all columns"
        if data is None and len(attrs) > 2:
            time.sleep(0.5)
            data, status = fetch(ext, attrs[:2], mets, filters, 120)
            attempt = "reduced grain (first 2 attrs)"

        if data is None:
            verdict, note = "ERROR", status
        elif data:
            verdict, note = "OK", f"{len(data)} rows · {attempt}"
        else:
            verdict, note = "EMPTY", f"0 rows in scope · {attempt}"
        if unscoped_req:
            note += f" · required filter with no known test value: {unscoped_req}"

        results.append({"reportType": rt, "externalReportType": ext, "path": path,
                        "verdict": verdict, "note": note})
        print(f"[{i:2d}/{len(targets)}] {verdict:5s} {rt:44s} {note}")
        time.sleep(0.4)

    print("\n" + "=" * 100)
    for v in ("OK", "EMPTY", "ERROR"):
        n = [r for r in results if r["verdict"] == v]
        print(f"  {v:6s} {len(n)}")
    errs = [r for r in results if r["verdict"] == "ERROR"]
    if errs:
        print(f"\nERRORS — to be triaged separately ({len(errs)}):")
        for r in errs:
            print(f"\n  {r['reportType']}  ({r['path']})")
            print(f"    {r['note']}")
    json.dump(results, open(os.path.join(HERE, "out", "verify_remaining.json"), "w"), indent=2)
    print(f"\nwrote out/verify_remaining.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
