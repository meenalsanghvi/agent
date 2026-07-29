"""Numeric diff: merged report vs each predecessor, same agency/window/grain.

Coverage proved no column was LOST. This proves the numbers did not MOVE -- the thing
that matters for the two merges whose query shape actually changed:

  MERCHANT_PERFORMANCE  MERCHANT_BU/CTR/RR were single-table (INNER cvcpf only). The
                        merged report puts them on the two-CTE shape from ROAS/CPC, which
                        adds a site LEFT JOIN and a `WHERE base.merchant_id IS NOT NULL`
                        guard those three never had. If any merchant has a null
                        merchant_id, the merged report drops a row they returned.

  KEYWORD_PERFORMANCE   added `LEFT JOIN marketing_campaign_group_dimensions` so
                        campaign_type/subtype could become filterable attributes,
                        replacing MERCHANT_KEYWORD's hardcoded WHERE. A LEFT JOIN should
                        not fan out, but if mcgd is not 1:1 on
                        (client_id, marketing_campaign_group_id) it would double rows.

Predecessors are de-listed from the external catalogue but their configs still exist in
Mongo, so both sides are fetched by INTERNAL reportType with useExternalNames=false.

Usage: HTTP_PROXY= HTTPS_PROXY= NO_PROXY="*" python3 numeric_diff.py
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
TOL = 0.01          # absolute tolerance for float comparison
LIMIT = 20000

MERGED_MERCHANT = "INTERNAL_PERF_MERCHANT_PERFORMANCE"
MERGED_KEYWORD = "INTERNAL_PERF_KEYWORD_PERFORMANCE"

# (predecessor, key attributes, metrics to compare, extra filters for the MERGED side)
CASES = [
    # ---- MERCHANT family: key on os_client_id + channel ----
    (MERGED_MERCHANT, "INTERNAL_PERF_MERCHANT_BU", ["os_client_id", "channel"],
     ["spend", "clicks", "impressions"], []),
    (MERGED_MERCHANT, "INTERNAL_PERF_MERCHANT_RR", ["os_client_id", "channel"],
     ["spend", "clicks", "impressions"], []),
    (MERGED_MERCHANT, "INTERNAL_PERF_MERCHANT_CTR", ["os_client_id", "channel"],
     ["spend", "clicks", "impressions", "ctr", "cpc", "cpm"], []),
    (MERGED_MERCHANT, "INTERNAL_PERF_MERCHANT_CPC", ["os_client_id", "channel"],
     ["spend", "clicks", "impressions", "cpc", "program_viewproducts",
      "program_add2carts", "site_viewproducts", "site_add2carts"], []),
    (MERGED_MERCHANT, "INTERNAL_PERF_MERCHANT_ROAS", ["os_client_id", "channel"],
     ["spend", "clicks", "program_viewproducts", "program_add2carts", "program_orders",
      "program_gmv", "roas", "site_viewproducts", "site_add2carts", "site_orders",
      "site_revenue"], []),

    # ---- KEYWORD family: scoped to one keyword, key on keyword + campaign_id ----
    (MERGED_KEYWORD, "INTERNAL_PERF_KW_COMPETITION", ["keyword", "campaign_id"],
     ["spend", "impressions", "clicks", "attributed_sales"], []),
    (MERGED_KEYWORD, "INTERNAL_PERF_KW_PERF_IN_CAMPAIGNS",
     ["keyword", "keyword_match_type", "campaign_id"],
     ["spend", "impressions", "clicks", "attributed_sales"], []),
    # MERCHANT_KEYWORD hardcoded campaign_type/subtype in its WHERE; the merged report
    # exposes them as attributes, so the caller must now pass them as filters.
    (MERGED_KEYWORD, "INTERNAL_PERF_MERCHANT_KEYWORD",
     ["keyword", "keyword_match_type", "campaign_id"],
     ["spend", "impressions", "clicks", "attributed_sales"],
     [{"key": "campaign_type", "operator": "=", "values": ["performance"]},
      {"key": "campaign_subtype", "operator": "IN",
       "values": ["os_ads_search", "smart_shopping"]}]),
]

KEYWORD_SCOPE = [{"key": "keyword", "operator": "IN", "values": ["iphone"]}]


def fetch(rt, attrs, metrics, filters, tmo=180):
    body = {"application": APP, "agencyId": AGENCY, "reportType": rt,
            "requestType": "REPORTING", "useExternalNames": False,
            "attributes": attrs, "metrics": metrics,
            "dateRanges": WINDOW, "filters": filters,
            "limit": LIMIT, "offset": 0}
    try:
        r = S.post(f"{BASE}/kamService/report/fetch", data=json.dumps(body),
                   headers=H, timeout=tmo)
    except Exception as e:
        return None, type(e).__name__
    if r.status_code != 200:
        return None, f"HTTP {r.status_code}: {r.text[:150]}"
    return r.json().get("data", []), "ok"


def keyed(rows, key_attrs, metrics):
    out = {}
    for r in rows:
        k = tuple(str(r.get(a)) for a in key_attrs)
        out[k] = {m: float(r.get(m) or 0) for m in metrics}
    return out


def main():
    print(f"Numeric diff — agency {AGENCY}, {WINDOW[0]['startDate']}→{WINDOW[0]['endDate']}, "
          f"tolerance ±{TOL}\n")
    overall_ok = True
    for merged, pred, key_attrs, metrics, extra in CASES:
        is_kw = merged == MERGED_KEYWORD
        base_filters = KEYWORD_SCOPE if is_kw else []
        print("=" * 96)
        print(f"{pred}\n  vs {merged}   key={key_attrs}  metrics={len(metrics)}")

        old, s1 = fetch(pred, key_attrs, metrics, base_filters)
        if old is None:
            print(f"  PREDECESSOR FETCH FAILED: {s1}")
            overall_ok = False
            continue
        time.sleep(0.4)
        new, s2 = fetch(merged, key_attrs, metrics, base_filters + extra)
        if new is None:
            print(f"  MERGED FETCH FAILED: {s2}")
            overall_ok = False
            continue

        O, N = keyed(old, key_attrs, metrics), keyed(new, key_attrs, metrics)
        only_old = sorted(set(O) - set(N))
        only_new = sorted(set(N) - set(O))
        shared = set(O) & set(N)

        drift = {}
        for k in shared:
            for m in metrics:
                d = abs(O[k][m] - N[k][m])
                if d > TOL:
                    drift.setdefault(m, []).append((k, O[k][m], N[k][m], d))

        tot_o = {m: sum(v[m] for v in O.values()) for m in metrics}
        tot_n = {m: sum(v[m] for v in N.values()) for m in metrics}

        print(f"  rows: predecessor {len(O)}  merged {len(N)}  shared {len(shared)}"
              f"  only-old {len(only_old)}  only-new {len(only_new)}")
        bad = bool(only_old or only_new or drift)
        for m in metrics:
            flag = "  ← DRIFT" if m in drift else ""
            print(f"    {m:22s} old={tot_o[m]:>18,.2f}   new={tot_n[m]:>18,.2f}{flag}")
        if only_old:
            print(f"  ROWS LOST BY MERGE ({len(only_old)}), first 5: {only_old[:5]}")
        if only_new:
            print(f"  ROWS ADDED BY MERGE ({len(only_new)}), first 5: {only_new[:5]}")
        for m, items in drift.items():
            print(f"  per-row drift in {m}: {len(items)} rows, worst 3:")
            for k, a, b, d in sorted(items, key=lambda x: -x[3])[:3]:
                print(f"      {k}  old={a:,.4f}  new={b:,.4f}  Δ={d:,.4f}")
        print(f"  VERDICT: {'❌ DIFFERS' if bad else '✅ IDENTICAL'}")
        overall_ok &= not bad
        time.sleep(0.6)

    print("\n" + "=" * 96)
    print("OVERALL:", "✅ every merged report reproduces its predecessors exactly"
          if overall_ok else "❌ differences found — see above")
    return 0 if overall_ok else 1


if __name__ == "__main__":
    sys.exit(main())
