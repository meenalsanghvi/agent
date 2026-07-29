"""Build a 4-column CSV: legacy query → its consolidated form → the config serving it.

  1 query_name          query_inventory id (skill.stem)
  2 raw_query           the exact legacy SQL extracted from the ADK agent
  3 consolidated_query  the SQL the ACTIVE report now runs to answer that same question
  4 report_config       the active report config JSON

Column 3 is real resolved SQL, not a template. It comes from KAM's own resolver
(POST /kamService/report/query), which runs the identical substitution path as
/report/fetch -- identity, pagination, attributes, metrics, order, filters, dates -- and
returns the SQL instead of executing it. So column 3 is exactly what BigQuery would run.

Which columns are requested for column 3: if the query had a predecessor config that was
merged away, we request precisely that predecessor's column set, so column 3 answers
"what does THIS query look like now" rather than "dump the whole merged report". Where a
predecessor's behaviour depended on a hardcoded WHERE that became a caller filter, that
filter is applied too (see MIGRATION_FILTERS), so the SQL is faithful to the migration.

Usage: HTTP_PROXY= HTTPS_PROXY= NO_PROXY="*" python3 build_query_csv.py
"""

import csv
import json
import os
import sys
import time

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import build_query_report_matrix as M  # noqa: E402
from merge_lib import ROOT, load  # noqa: E402

BASE = "http://test.onlinesales.ai"
APP = "irisTestApplication"
H = {"Content-Type": "application/json"}
S = requests.Session()
S.trust_env = False
AGENCY = 105
WINDOW = [{"startDate": "2026-07-19", "endDate": "2026-07-21"}]

# Filters a caller must now pass because the merged template dropped a guard that only
# some family members carried. Keyed by (successor reportType, predecessor reportType).
MIGRATION_FILTERS = {
    "INTERNAL_PERF_MERCHANT_KEYWORD": [
        {"key": "campaign_type", "operator": "=", "values": ["performance"]},
        {"key": "campaign_subtype", "operator": "IN",
         "values": ["os_ads_search", "smart_shopping"]}],
    "INTERNAL_PERF_CAMPAIGN_PERF_DAILY": [
        {"key": "campaign_type", "operator": "IN",
         "values": ["PERFORMANCE", "INVENTORY", "OFFSITE"]}],
    "INTERNAL_PERF_CAMPAIGN_KW_TARGETED": [
        {"key": "is_negative", "operator": "=", "values": ["0"]}],
    "INTERNAL_PERF_CAMPAIGN_KW_NEGATIVE": [
        {"key": "is_negative", "operator": "=", "values": ["1"]}],
    "INTERNAL_PERF_BUDGET_CHANGES": [
        {"key": "action_type_id", "operator": "=", "values": ["17"]}],
    "INTERNAL_PERF_CAMPAIGN_STATUS_CHANGES": [
        {"key": "action_type_id", "operator": "=", "values": ["16"]}],
    "INTERNAL_PERF_PRODUCT_SELECTION_CHANGES": [
        {"key": "action_type_id", "operator": "IN", "values": ["50", "51"]}],
    "INTERNAL_PERF_RR_DISPLAY_PAGE_TYPE": [
        {"key": "page_type", "operator": "NOT IN", "values": ["", "NA"]}],
    "INTERNAL_PERF_RR_BY_PAGE_DISPLAY": [
        {"key": "page_type", "operator": "NOT IN", "values": ["", "NA"]}],
    "INTERNAL_PERF_BU_REQUESTS_DISPLAY": [
        {"key": "page_type", "operator": "NOT IN", "values": ["", "NA"]}],
}

# Columns that cannot be requested as attributes: the report's template has no
# __ATTRIBUTES__ placeholder (filter-only), or the column was deliberately dropped.
UNREQUESTABLE = {
    "INTERNAL_PERF_GMV_ATTRIBUTION": {"channel"},
    "INTERNAL_PERF_RR_DISPLAY": {"store_id"},
}


def col_keys(cfg, section):
    return [k for k in (cfg.get(section) or {}).keys()]


def resolve_sql(report_type, attrs, metrics, filters):
    body = {"application": APP, "agencyId": AGENCY, "reportType": report_type,
            "requestType": "REPORTING", "attributes": attrs,
            "metrics": metrics or ["placeholder_metric"],
            "dateRanges": WINDOW, "filters": filters, "limit": 1000, "offset": 0}
    try:
        r = S.post(f"{BASE}/kamService/report/query", data=json.dumps(body),
                   headers=H, timeout=60)
    except Exception as e:
        return f"[could not resolve: {type(e).__name__}]"
    if r.status_code != 200:
        return f"[could not resolve: HTTP {r.status_code} {r.text[:160]}]"
    return (r.json() or {}).get("reportQuery") or "[empty reportQuery]"


def main():
    queries = [M.parse_sql(p) for p in sorted(M.QUERY_DIR.glob("*/*.sql"))]
    active = [c for p in sorted(M.CONFIG_DIR.glob("*/*.json"))
              if p.parent.name != "_retired" and (c := M.parse_config(p))]

    # (skill, stem) -> [active config, ...]
    serving = {}
    for cfg in active:
        claims, _ = M.match(cfg, queries)
        for claim in claims:
            serving.setdefault(claim, []).append(cfg)

    # Reconstruct which retired predecessor came from which query, so column 3 can
    # request that predecessor's exact column set rather than the whole merged report.
    pred_for = {}   # (skill, stem, successor_reportType) -> retired cfg dict
    for wave in ("merge_wave1", "merge_wave2", "merge_wave3"):
        for spec in __import__(wave).SPECS:
            for old_rel in spec["absorbs"]:
                if old_rel == spec["path"]:
                    continue
                old = load(old_rel)
                skill = old_rel.split("/")[0]
                claims, _ = M.match({"reportType": old["reportType"], "skill": skill}, queries)
                for (sk, stem) in claims:
                    pred_for[(sk, stem, spec["reportType"])] = old

    rows, resolved, failed = [], 0, 0
    for q in queries:
        cfgs = serving.get((q["skill"], q["stem"]), [])
        if not cfgs:
            rows.append({"query_name": q["query_id"], "raw_query": q["sql"],
                         "consolidated_query": "[no report serves this query yet]",
                         "report_config": ""})
            continue
        for cfg in cfgs:
            full = json.loads(cfg["config"])
            rt = full["reportType"]
            pred = pred_for.get((q["skill"], q["stem"], rt))
            src = pred or full
            skip = UNREQUESTABLE.get(rt, set())
            attrs = [a for a in col_keys(src, "attributes") if a not in skip]
            mets = [m for m in col_keys(src, "metrics")]
            filters = MIGRATION_FILTERS.get(pred["reportType"], []) if pred else []

            sql = resolve_sql(rt, attrs, mets, filters)
            ok = not sql.startswith("[")
            resolved += ok
            failed += not ok
            note = "" if pred else "  (no merged predecessor — full report column set)"
            rows.append({
                "query_name": q["query_id"] + (f"  →  {rt}" if len(cfgs) > 1 else ""),
                "raw_query": q["sql"],
                "consolidated_query": sql,
                "report_config": cfg["config"],
            })
            print(f"  {'ok ' if ok else 'ERR'} {q['query_id']:52s} → {rt}{note}")
            time.sleep(0.25)

    out = os.path.join(HERE, "out", "query_consolidated_matrix.csv")
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["query_name", "raw_query",
                                           "consolidated_query", "report_config"])
        w.writeheader()
        w.writerows(rows)
    print(f"\n{len(rows)} rows → {out}")
    print(f"  consolidated SQL resolved: {resolved}   failed: {failed}   "
          f"no report: {sum(1 for r in rows if r['consolidated_query'].startswith('[no report'))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
