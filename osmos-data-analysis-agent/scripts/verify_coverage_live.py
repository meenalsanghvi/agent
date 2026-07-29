"""Phase 4 — prove every retired report's columns still resolve from its replacement.

For each retired config: take its exact externalColumnName set (attributes + metrics),
fetch the MERGED report requesting precisely those names, and check it resolves.

Why HTTP 200 is the pass signal even at 0 rows: KAM validates requested external names
against the catalogue before running SQL, and an unresolvable name fails with
"attribute/metric not configured". A 200 therefore proves the column survived the merge
into the external catalogue. Where rows come back we additionally assert every requested
name appears as a key, which is the stronger check.

The failure this is hunting: filterTags intersection. A column whose tags stop
intersecting its report's tags is dropped from the catalogue SILENTLY -- no error, no log.

Fetches are strictly sequential (the test env 500s under concurrency).

Usage: HTTP_PROXY= HTTPS_PROXY= NO_PROXY="*" python3 verify_coverage_live.py
"""

import json
import os
import sys
import time

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from merge_lib import ROOT, load  # noqa: E402

BASE = "http://test.onlinesales.ai"
APP = "irisTestApplication"
H = {"Content-Type": "application/json"}
S = requests.Session()
S.trust_env = False
AGENCY = 105
WINDOW = {"startDate": "2026-07-19", "endDate": "2026-07-21"}

# Scoping per successor: keeps fetches inside the test env's query budget. These are
# the known-good scopes from REMAINING_QUEUE.md, not correctness filters.
SCOPE = {
    "SKU_PERFORMANCE_REPORT":            [("os_client_id", "IN", ["277661"])],
    "INTERNAL_KEYWORD_PERFORMANCE_REPORT": [("keyword", "IN", ["iphone"])],
    "INTERNAL_SEARCH_QUERY_PERF_REPORT": [("search_query", "IN", ["iphone"])],
    "SEARCH_QUERY_REQUESTS_PLA_REPORT":  [("keyword", "IN", ["iphone"])],
    "INTERNAL_CAMPAIGN_PERFORMANCE_REPORT": [("campaign_id", "IN", ["1322334"])],
    "CAMPAIGN_KEYWORDS_REPORT":          [("campaign_id", "IN", ["1322334"])],
    "CAMPAIGN_NETWORKS_REPORT":          [("campaign_id", "IN", ["1322334"])],
}
# Successors whose keyword grain needs scoping regardless of predecessor.
KEYWORD_GRAIN = {"RR_DISPLAY_REPORT": ("keyword", "IN", ["iphone"])}

# Attributes that exist only as FILTERS: their report's template has no __ATTRIBUTES__
# placeholder, so the column can be filtered on but never returned. Verified identical
# on the predecessor (PROGRAM_SPEND_REPORT also returns only `spend` when asked for
# `channel`), so this is inherited behaviour, not a coverage gap.
FILTER_ONLY = {"GMV_ATTRIBUTION_REPORT": {"channel"}}

# Deliberately not carried forward — see the justification in the merge spec.
# store_id: os_display_ads_filtered_level_performance_facts has no such column; the
# predecessor 500s on it identically.
DROPPED = {"RR_DISPLAY_REPORT": {"store_id"}}

# These group over the whole marketplace and need more than the default budget.
SLOW = {"CATEGORY_PERFORMANCE_REPORT": 150}

# audit.audit_logs_v2 is unreachable (unregistered appKey / missing IAM) — pre-existing.
BLOCKED = {"INTERNAL_PERF_BUDGET_CHANGES", "INTERNAL_PERF_CAMPAIGN_STATUS_CHANGES",
           "INTERNAL_PERF_PRODUCT_SELECTION_CHANGES"}


def ext_cols(cfg, section):
    return [c["externalColumnName"]
            for c in (cfg.get(section) or {}).values()
            if c.get("externalColumnName")]


def plan():
    """[(retired_reportType, retired_file, successor_externalReportType)]"""
    out = []
    for wave in ("merge_wave1", "merge_wave2", "merge_wave3"):
        for spec in __import__(wave).SPECS:
            for old in spec["absorbs"]:
                if old == spec["path"]:
                    continue
                out.append((load(old)["reportType"], old, spec["externalReportType"]))
    return out


def fetch(ext_rt, attrs, metrics, filters, tmo=40):
    body = {"application": APP, "agencyId": AGENCY, "reportType": ext_rt,
            "requestType": "REPORTING", "useExternalNames": True,
            "attributes": attrs, "metrics": metrics,
            "dateRanges": [WINDOW],
            "filters": [{"key": k, "operator": o, "values": v} for k, o, v in filters],
            "limit": 5, "offset": 0}
    try:
        r = S.post(f"{BASE}/kamService/report/fetch", data=json.dumps(body),
                   headers=H, timeout=tmo)
    except Exception as e:
        return None, f"{type(e).__name__}"
    if r.status_code != 200:
        return None, f"HTTP {r.status_code}: {r.text[:130]}"
    return r.json().get("data", []), "ok"


def main():
    rows = plan()
    print(f"Phase 4 — {len(rows)} retired reports to verify against their replacements\n")
    results = []
    for i, (rt, path, succ) in enumerate(sorted(rows), 1):
        old = load(path)
        attrs = ext_cols(old, "attributes")
        mets = ext_cols(old, "metrics") or ["placeholder_metric"]
        skip = FILTER_ONLY.get(succ, set()) | DROPPED.get(succ, set())
        attrs = [a for a in attrs if a not in skip]

        if rt in BLOCKED:
            results.append((rt, succ, "BLOCKED", "audit.audit_logs_v2 unreachable (pre-existing)"))
            print(f"[{i:2d}/{len(rows)}] {rt:46s} → SKIP (blocked)")
            continue

        filters = [t for t in SCOPE.get(succ, [])]
        if succ in KEYWORD_GRAIN and "keyword" in attrs:
            filters = [KEYWORD_GRAIN[succ]]

        data, status = fetch(succ, attrs, mets, filters, tmo=SLOW.get(succ, 40))
        if data is None:
            verdict, note = "FAIL", status
        else:
            want = set(attrs) | set(mets)
            if data:
                missing = sorted(want - set(data[0].keys()))
                verdict = "PASS" if not missing else "FAIL"
                extra = f" (+{len(skip)} filter-only/dropped)" if skip else ""
                note = f"{len(data)} rows, all {len(want)} cols present{extra}" if not missing \
                       else f"MISSING FROM ROWS: {missing}"
            else:
                verdict, note = "PASS*", f"0 rows in scope; all {len(want)} cols resolved"
        results.append((rt, succ, verdict, note))
        print(f"[{i:2d}/{len(rows)}] {rt:46s} → {verdict:6s} {note}")
        time.sleep(0.4)  # be gentle; the env 500s under rapid fire

    print("\n" + "=" * 100)
    for v in ("FAIL", "PASS", "PASS*", "BLOCKED"):
        n = sum(1 for r in results if r[2] == v)
        if n:
            print(f"  {v:8s} {n}")
    bad = [r for r in results if r[2] == "FAIL"]
    if bad:
        print("\nFAILURES:")
        for rt, succ, _, note in bad:
            print(f"  {rt} → {succ}\n      {note}")
    json.dump([{"retired": a, "successor": b, "verdict": c, "note": d} for a, b, c, d in results],
              open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "out", "coverage_live.json"), "w"), indent=2)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
