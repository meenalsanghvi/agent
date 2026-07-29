"""Numeric diff for the remaining 34 predecessor → successor pairs.

Complements numeric_diff.py (merchant + keyword families, 8 pairs, all identical).

Each case declares, per side, what to request -- because three things differ between a
predecessor and its replacement:

  * RENAMED COLUMNS. CATEGORY_PERFORMANCE exposes the untouched category values as
    category_l*_raw (category_l* is the display-normalised CASE inherited from
    CATEGORY_LEVEL), and CAMPAIGN_NETWORKS renamed the numeric id to
    internal_campaign_id. So the two sides request different keys for the same value.
  * GUARDS THAT BECAME FILTERS. Where only some family members carried a null/NA guard,
    the merged template dropped it and the caller must supply it. `mfilters` is exactly
    what MERGE_MAP.md tells callers to pass, so these cases test the migration
    instruction as well as the arithmetic.
  * SCOPE. Some grains are far too heavy to fetch whole; `scope` applies to BOTH sides
    identically, so the comparison stays honest.

Rows are keyed by the grain tuple, so a lost row and a gained row cannot cancel out in a
matching total.

Usage: HTTP_PROXY= HTTPS_PROXY= NO_PROXY="*" python3 numeric_diff_all.py
"""

import json
import sys
import time

import requests

BASE = "http://test.onlinesales.ai"
APP = "irisTestApplication"
H = {"Content-Type": "application/json"}
S = requests.Session()
S.trust_env = False
AGENCY = 105
WINDOW = [{"startDate": "2026-07-19", "endDate": "2026-07-21"}]
TOL = 0.01

RR3 = ["requests", "responses", "response_rate"]
RR2 = ["requests", "responses"]
KW = ["iphone"]


def f(key, op, vals):
    return {"key": key, "operator": op, "values": vals}


NOT_BLANK_PT = [f("page_type", "NOT IN", ["", "NA"])]
KW_SCOPE = [f("keyword", "IN", KW)]
CAMP = [f("campaign_id", "IN", ["1322334"])]

# (predecessor, successor, pred_attrs, merged_attrs|None, metrics, scope, mfilters, limit, tmo)
CASES = [
    # ---- RR_DISPLAY (6) ----
    ("INTERNAL_PERF_RR_BY_DIMENSION_DISPLAY", "INTERNAL_PERF_RR_DISPLAY",
     ["network", "page_type", "device", "ad_unit", "category_l1", "category_l2", "category_l3"],
     None, RR3, [], [], 200000, 240),
    ("INTERNAL_PERF_RR_DISPLAY_PAGE_TYPE", "INTERNAL_PERF_RR_DISPLAY",
     ["page_type"], None, RR3, [], [f("page_type", "!=", [""])], 20000, 90),
    ("INTERNAL_PERF_RR_HOURLY", "INTERNAL_PERF_RR_DISPLAY",
     ["hour"], None, RR2, [], [], 20000, 90),
    ("INTERNAL_PERF_RR_HOURLY_AD_UNIT", "INTERNAL_PERF_RR_DISPLAY",
     ["ad_unit"], None, RR2, [], [], 20000, 90),
    ("INTERNAL_PERF_SEARCH_QUERY_RR_DISPLAY", "INTERNAL_PERF_RR_DISPLAY",
     ["keyword"], None, RR3, KW_SCOPE, [], 20000, 120),
    ("INTERNAL_PERF_SEARCH_QUERY_RR_DISPLAY_AD_UNIT", "INTERNAL_PERF_RR_DISPLAY",
     ["keyword", "ad_unit"], None, RR3, KW_SCOPE, [], 20000, 120),

    # ---- RR_PLA (3) ----
    ("INTERNAL_PERF_RR_BY_DIMENSION_PLA", "INTERNAL_PERF_RR_PLA",
     ["network", "store_id", "page_type", "page_name", "device",
      "category_l1", "category_l2", "category_l3", "category_l4", "category_l5"],
     None, RR3, [], [], 200000, 240),
    ("INTERNAL_PERF_CATEGORY_RR", "INTERNAL_PERF_RR_PLA",
     ["page_type", "category_l1", "category_l2", "category_l3"], None, RR3, [],
     [f("category_l1", "!=", [""])] + NOT_BLANK_PT, 200000, 240),
    ("INTERNAL_PERF_STORE_LEVEL_RR", "INTERNAL_PERF_RR_PLA",
     ["store_id", "category", "day", "hour", "page_type"], None, RR2, [], [], 200000, 300),

    # ---- SEARCH_QUERY_REQUESTS_PLA (3) ----
    ("INTERNAL_PERF_SEARCH_QUERY_RR_PLA", "INTERNAL_PERF_SEARCH_QUERY_REQUESTS_PLA",
     ["keyword"], None, RR3, KW_SCOPE, [], 20000, 120),
    ("INTERNAL_PERF_SEARCH_QUERY_RR_BUCKETS", "INTERNAL_PERF_SEARCH_QUERY_REQUESTS_PLA",
     ["keyword"], None, RR2, KW_SCOPE, [], 20000, 120),
    ("INTERNAL_PERF_KW_REQUEST_VOLUME", "INTERNAL_PERF_SEARCH_QUERY_REQUESTS_PLA",
     ["keyword"], None, ["requests", "days_with_requests"], KW_SCOPE, [], 20000, 120),

    # ---- PAGE_PERFORMANCE_PLA (3) ----
    ("INTERNAL_PERF_PAGE_LEVEL", "INTERNAL_PERF_PAGE_PERFORMANCE_PLA",
     ["page_type"], None, ["requests", "responses", "impressions", "clicks", "spend"],
     [], [], 20000, 120),
    ("INTERNAL_PERF_RR_BY_PAGE_PLA", "INTERNAL_PERF_PAGE_PERFORMANCE_PLA",
     ["page_type"], None, RR3, [], [], 20000, 120),
    ("INTERNAL_PERF_BU_REQUESTS_PLA", "INTERNAL_PERF_PAGE_PERFORMANCE_PLA",
     ["date"], None, RR2, [], [], 20000, 120),

    # ---- DISPLAY_AD_UNIT (2) ----
    ("INTERNAL_PERF_RR_BY_PAGE_DISPLAY", "INTERNAL_PERF_DISPLAY_AD_UNIT",
     ["page_type"], None, RR3, [], NOT_BLANK_PT, 20000, 120),
    ("INTERNAL_PERF_BU_REQUESTS_DISPLAY", "INTERNAL_PERF_DISPLAY_AD_UNIT",
     ["date"], None, RR2, [], NOT_BLANK_PT, 20000, 120),

    # ---- SKU_PERFORMANCE (3) ----
    ("INTERNAL_PERF_SKU_ROAS", "INTERNAL_PERF_SKU_PERFORMANCE",
     ["sku_id", "os_client_id"], None,
     ["spend", "impressions", "clicks", "program_viewproducts", "program_add2carts",
      "program_orders", "program_gmv", "site_viewproducts", "site_add2carts",
      "site_orders", "site_gmv"], [f("os_client_id", "IN", ["277661"])], [], 20000, 180),
    ("INTERNAL_PERF_SKU_CPC", "INTERNAL_PERF_SKU_PERFORMANCE",
     ["sku_id", "os_client_id"], None,
     ["spend", "impressions", "clicks", "cpc", "program_viewproducts", "program_add2carts",
      "program_orders", "program_gmv", "site_viewproducts", "site_add2carts",
      "site_orders", "site_gmv"], [f("os_client_id", "IN", ["277661"])], [], 20000, 180),
    ("INTERNAL_PERF_SKU_CTR", "INTERNAL_PERF_SKU_PERFORMANCE",
     ["sku_id", "os_client_id"], None, ["spend", "impressions", "clicks", "ctr"],
     [f("os_client_id", "IN", ["277661"])], [], 20000, 180),

    # ---- GMV_ATTRIBUTION (1) — both ungrouped ----
    ("INTERNAL_PERF_PROGRAM_SPEND", "INTERNAL_PERF_GMV_ATTRIBUTION",
     [], None, ["spend"], [], [], 100, 90),

    # ---- CATEGORY_PERFORMANCE (2) — note the raw/normalised split ----
    ("INTERNAL_PERF_CATEGORY_LEVEL", "INTERNAL_PERF_CATEGORY_PERFORMANCE",
     ["category_l1", "category_l2", "category_l3"], None,
     ["spend", "impressions", "clicks", "program_orders", "program_revenue",
      "program_viewproducts", "program_add_to_carts", "site_viewproducts",
      "site_add_to_carts", "site_orders", "site_revenue"], [], [], 200000, 240),
    ("INTERNAL_PERF_MERCHANT_CATEGORY_CPC", "INTERNAL_PERF_CATEGORY_PERFORMANCE",
     ["category_l1", "category_l2", "category_l3", "merchant_id"],
     ["category_l1_raw", "category_l2_raw", "category_l3_raw", "merchant_id"],
     ["spend", "clicks", "program_gmv", "program_orders", "program_viewproducts",
      "merchant_count"], [], [], 200000, 300),

    # ---- SEARCH_QUERY_PERFORMANCE (2) ----
    ("INTERNAL_PERF_SEARCH_QUERY_PERF", "INTERNAL_PERF_SEARCH_QUERY_PERFORMANCE",
     ["search_query"], None,
     ["impressions", "clicks", "spend", "ctr", "auto_impressions", "auto_clicks",
      "manual_impressions", "manual_clicks"],
     [f("search_query", "IN", KW)], [], 20000, 150),
    ("INTERNAL_PERF_KEYWORD_SELLER", "INTERNAL_PERF_SEARCH_QUERY_PERFORMANCE",
     ["search_query", "os_client_id", "seller_id", "merchant_name"], None,
     ["impressions", "clicks", "spend", "ctr", "auto_impressions", "manual_impressions"],
     [f("search_query", "IN", KW)], [], 20000, 150),

    # ---- CAMPAIGN_PERFORMANCE (2) ----
    ("INTERNAL_PERF_CAMPAIGN_PERF_AGG", "INTERNAL_PERF_CAMPAIGN_PERFORMANCE",
     ["campaign_id", "campaign_group_id", "merchant_id", "os_client_id"], None,
     ["impressions", "clicks", "spend", "orders", "revenue"], CAMP, [], 20000, 180),
    ("INTERNAL_PERF_CAMPAIGN_PERF_DAILY", "INTERNAL_PERF_CAMPAIGN_PERFORMANCE",
     ["date", "campaign_id", "campaign_group_id", "merchant_id", "os_client_id"], None,
     ["impressions", "clicks", "spend", "orders", "revenue"], CAMP,
     [f("campaign_type", "IN", ["PERFORMANCE", "INVENTORY", "OFFSITE"])], 20000, 180),

    # ---- CAMPAIGN_KEYWORDS (2) ----
    ("INTERNAL_PERF_CAMPAIGN_KW_TARGETED", "INTERNAL_PERF_CAMPAIGN_KEYWORDS",
     ["keyword", "bidding_value", "campaign_id", "os_client_id"], None,
     ["placeholder_metric"], CAMP, [f("is_negative", "=", ["0"])], 20000, 120),
    ("INTERNAL_PERF_CAMPAIGN_KW_NEGATIVE", "INTERNAL_PERF_CAMPAIGN_KEYWORDS",
     ["keyword", "campaign_id", "os_client_id"], None,
     ["placeholder_metric"], CAMP, [f("is_negative", "=", ["1"])], 20000, 120),

    # ---- CAMPAIGN_NETWORKS (2) — BY_ID's campaign_id is now internal_campaign_id ----
    ("INTERNAL_PERF_CAMPAIGN_NETWORKS_BY_ID", "INTERNAL_PERF_CAMPAIGN_NETWORKS",
     ["campaign_id", "target_details"], ["internal_campaign_id", "target_details"],
     ["placeholder_metric"], [], [], 20000, 120),
    ("INTERNAL_PERF_CAMPAIGN_NETWORKS_VIA_CTD", "INTERNAL_PERF_CAMPAIGN_NETWORKS",
     ["campaign_id", "resolved_campaign_id", "target_details"], None,
     ["placeholder_metric"], CAMP, [], 20000, 120),
]

BLOCKED = [("INTERNAL_PERF_BUDGET_CHANGES", "action_type_id=17"),
           ("INTERNAL_PERF_CAMPAIGN_STATUS_CHANGES", "action_type_id=16"),
           ("INTERNAL_PERF_PRODUCT_SELECTION_CHANGES", "action_type_id IN (50,51)")]


PAGE = 100000   # kamService caps `limit` at 100000 (fetch.validator)


def fetch(rt, attrs, metrics, filters, limit, tmo):
    """Fetch ALL rows, paging when the grain exceeds the server's 100k limit.

    Paging matters for correctness, not just completeness: a silently truncated page
    would drop rows from one side and report a bogus mismatch (STORE_LEVEL_RR alone is
    ~123k rows at its native grain).
    """
    rows, offset = [], 0
    while True:
        body = {"application": APP, "agencyId": AGENCY, "reportType": rt,
                "requestType": "REPORTING", "useExternalNames": False,
                "attributes": attrs, "metrics": metrics, "dateRanges": WINDOW,
                "filters": filters, "limit": min(PAGE, limit), "offset": offset}
        try:
            r = S.post(f"{BASE}/kamService/report/fetch", data=json.dumps(body),
                       headers=H, timeout=tmo)
        except Exception as e:
            return None, type(e).__name__
        if r.status_code != 200:
            return None, f"HTTP {r.status_code}: {r.text[:120]}"
        page = r.json().get("data", [])
        rows += page
        if len(page) < min(PAGE, limit) or len(rows) >= limit:
            return rows, "ok"
        offset += len(page)
        time.sleep(0.3)


def keyed(rows, attrs, metrics):
    out = {}
    for r in rows:
        k = tuple(str(r.get(a)) for a in attrs) if attrs else ("__total__",)
        cur = out.setdefault(k, {m: 0.0 for m in metrics})
        for m in metrics:
            cur[m] += float(r.get(m) or 0)
    return out


def main():
    print(f"Numeric diff — remaining {len(CASES)} pairs "
          f"(+{len(BLOCKED)} blocked)  agency {AGENCY}  tol ±{TOL}\n")
    ident = diff = err = 0
    problems = []
    for pred, succ, pa, ma, metrics, scope, mfilters, lim, tmo in CASES:
        ma = ma or pa
        old, s1 = fetch(pred, pa, metrics, scope, lim, tmo)
        time.sleep(0.4)
        new, s2 = fetch(succ, ma, metrics, scope + mfilters, lim, tmo)
        label = f"{pred:46s} → {succ.replace('INTERNAL_PERF_','')}"
        if old is None or new is None:
            err += 1
            problems.append((pred, f"fetch failed: pred={s1} merged={s2}"))
            print(f"  ERR  {label}  pred={s1} merged={s2}")
            continue
        O, N = keyed(old, pa, metrics), keyed(new, ma, metrics)
        lost, gained = sorted(set(O) - set(N)), sorted(set(N) - set(O))
        drift = []
        for k in set(O) & set(N):
            for m in metrics:
                if abs(O[k][m] - N[k][m]) > TOL:
                    drift.append((m, k, O[k][m], N[k][m]))
        if lost or gained or drift:
            diff += 1
            detail = (f"rows {len(O)}→{len(N)} lost={len(lost)} gained={len(gained)} "
                      f"drift={len(drift)}")
            problems.append((pred, detail, lost[:3], gained[:3], drift[:3]))
            print(f"  ❌   {label}  {detail}")
        else:
            ident += 1
            print(f"  ✅   {label}  {len(O)} rows × {len(metrics)} metrics")
        time.sleep(0.5)

    for rt, note in BLOCKED:
        print(f"  ⏭   {rt:46s} → AUDIT_EVENTS  SKIPPED (BQ unreachable; {note})")

    print(f"\n{'='*94}\n  identical {ident}   differing {diff}   errored {err}   "
          f"blocked {len(BLOCKED)}")
    if problems:
        print("\nDETAIL:")
        for p in problems:
            print(f"\n  {p[0]}: {p[1]}")
            if len(p) > 2:
                if p[2]:
                    print(f"    lost rows  : {p[2]}")
                if p[3]:
                    print(f"    gained rows: {p[3]}")
                for m, k, a, b in p[4]:
                    print(f"    drift {m} @ {k}: old={a:,.4f} new={b:,.4f}")
    return 1 if (diff or err) else 0


if __name__ == "__main__":
    sys.exit(main())
