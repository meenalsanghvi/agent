#!/usr/bin/env python3
"""
post_and_fetch.py — standalone KAM config post + run (no kam-tester/kam-writer needed)
=====================================================================================
Posts a KAM report config to the KAM service and runs it, printing the returned row(s).
Mirrors kamService/mcp_servers/shared/http_client.py (Content-Type only; no bearer
token — KAM report endpoints are internal-network trust). Only stdlib + `requests`.

ACCESS NEEDED: network reachability to the KAM env base URL (VPN, or the
http://127.0.0.1:8118 proxy tunnel via the gateway). No auth token required for
test/staging report endpoints. Use --token only if your env front-ends KAM with one.

Usage (CTR test, agency 105, current vs prior week):
  python post_and_fetch.py \
    --config ctr/KAM_AGENT_CTR_OVERALL.json \
    --agency 105 \
    --current 2026-07-19 2026-07-21 \
    --baseline 2026-07-12 2026-07-18 \
    --metrics clicks impressions ctr spend
  # add --proxy   to route via http://127.0.0.1:8118
  # add --show-sql to also print the resolved BigQuery SQL
  # add --skip-post if the config is already deployed
"""
from __future__ import annotations

import argparse
import json
import sys

import requests

DEFAULT_BASE = "http://test.onlinesales.ai"
PROXY = {"http": "http://127.0.0.1:8118", "https": "http://127.0.0.1:8118"}
HEADERS = {"Content-Type": "application/json"}


def _headers(token: str | None) -> dict:
    h = dict(HEADERS)
    if token:
        h["x-token"] = token  # only if your env requires it; kam-tester sends none
    return h


def get_existing(base, report_type, application, proxies, token):
    """Fetch an existing config by reportType (returns the doc incl. its Mongo id, or None)."""
    query = json.dumps({"reportTypes": [report_type], "application": application})
    r = requests.get(f"{base}/kamService/report/config", params={"jsonQuery": query},
                     headers=_headers(token), proxies=proxies, timeout=60)
    if r.status_code != 200:
        return None
    reports = (r.json() or {}).get("reports", [])
    return reports[0] if reports else None


def post_config(base, config, proxies, token, application):
    """Insert or UPDATE a config. KAM updates only when the body carries the existing
    doc's `id`; otherwise it inserts and collides on the unique reportType. So we look
    up the existing id first and merge it in."""
    existing = get_existing(base, config.get("reportType"), application, proxies, token)
    mode = "inserted"
    if existing:
        eid = existing.get("id") or existing.get("_id")
        if isinstance(eid, dict):          # e.g. {"$oid": "..."}
            eid = eid.get("$oid")
        if eid:
            config = {**config, "id": eid}
            mode = f"updated (id={eid})"
    url = f"{base}/kamService/report/config"
    r = requests.post(url, headers=_headers(token), data=json.dumps(config), proxies=proxies, timeout=60)
    if r.status_code != 200:
        sys.exit(f"[post config] HTTP {r.status_code}: {r.text}")
    print(f"[post config] OK — {config.get('reportType')} ({mode})")
    return r.json()


def run_report(base, body, proxies, token, path="fetch"):
    url = f"{base}/kamService/report/{path}"
    if body.get("clientId"):
        url = f"{base}/kamService/report/fetch/client"
    r = requests.post(url, headers=_headers(token), data=json.dumps(body), proxies=proxies, timeout=120)
    if r.status_code != 200:
        sys.exit(f"[{path}] HTTP {r.status_code}: {r.text}")
    return r.json()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, help="Path to the KAM config JSON.")
    ap.add_argument("--base", default=DEFAULT_BASE, help=f"KAM base URL (default {DEFAULT_BASE}).")
    ap.add_argument("--agency", type=int, required=True)
    ap.add_argument("--current", nargs=2, metavar=("START", "END"), required=True)
    ap.add_argument("--baseline", nargs=2, metavar=("START", "END"),
                    help="Baseline window (enables comparison mode).")
    ap.add_argument("--metrics", nargs="+", required=True, help="Metric keys to request.")
    ap.add_argument("--attributes", nargs="*", default=[], help="Attribute keys (group-by).")
    ap.add_argument("--application", default="irisTestApplication")
    ap.add_argument("--proxy", action="store_true", help="Route via http://127.0.0.1:8118.")
    ap.add_argument("--token", default=None, help="Optional x-token, if your env requires it.")
    ap.add_argument("--skip-post", action="store_true", help="Config already deployed; skip posting.")
    ap.add_argument("--show-sql", action="store_true", help="Also print the resolved BigQuery SQL.")
    args = ap.parse_args()

    proxies = PROXY if args.proxy else None
    config = json.load(open(args.config))

    if not args.skip_post:
        post_config(args.base, config, proxies, args.token, args.application)

    date_ranges = [{"startDate": args.current[0], "endDate": args.current[1]}]
    if args.baseline:
        date_ranges.append({"startDate": args.baseline[0], "endDate": args.baseline[1]})

    body = {
        "application": args.application,
        "agencyId": args.agency,
        "reportType": config["reportType"],
        "requestType": "REPORTING",
        "useExternalNames": False,
        "attributes": args.attributes,
        "metrics": args.metrics,
        "dateRanges": date_ranges,
        "filters": [],
        "limit": 100000,
        "offset": 0,
    }

    if args.show_sql:
        sql = run_report(args.base, body, proxies, args.token, path="query")
        print("\n--- RESOLVED SQL ---")
        print(sql.get("reportQuery") or sql)

    result = run_report(args.base, body, proxies, args.token, path="fetch")
    data = result.get("data", []) if isinstance(result, dict) else result
    print(f"\n--- DATA ({len(data)} row(s)) ---")
    print(json.dumps(data, indent=2))
    # Quick sanity: show the comparison-variant keys on the first row (validates <key>_prev naming)
    if data:
        keys = sorted(data[0].keys())
        print("\n--- RETURNED KEYS (confirm _prev / _change / _perc variants) ---")
        print(keys)


if __name__ == "__main__":
    main()
