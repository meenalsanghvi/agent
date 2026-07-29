#!/usr/bin/env python3
"""
local_dev_server.py — a laptop-only stdio MCP server for demoing the data-analysis agent
========================================================================================
A dependency-light (stdlib + `requests`) MCP server that exposes the *validated*
config-only SOP tools by calling the KAM **test** env directly — NO Hades, NO Redis,
NO x-token, NO private package registry, NO port. This is the "just-for-me" stand-in
for the hosted `osmos-performance-mcp`; it is NOT the production server.

It speaks MCP over stdio (newline-delimited JSON-RPC 2.0), so Claude Code launches it
as a subprocess (see osmos-data-analysis-agent/.mcp.json). Each tool fetches a
KAM_AGENT_* report and returns the raw rows; the agent/skill interprets them and does
the delta/verdict math (mirroring the real Python derived layer).

Data source: http://test.onlinesales.ai/kamService/report/fetch  (must be reachable).
The KAM_AGENT_* configs must already be posted to test (they were, during validation).

Run standalone sanity check:  python3 local_dev_server.py --selftest
"""
from __future__ import annotations

import json
import sys
import traceback

import requests

BASE = "http://test.onlinesales.ai"
APPLICATION = "irisTestApplication"
HEADERS = {"Content-Type": "application/json"}

# A session that IGNORES environment proxies (a stray HTTP_PROXY was intercepting calls).
_session = requests.Session()
_session.trust_env = False


def log(*a):
    print("[local-mcp]", *a, file=sys.stderr, flush=True)


# ── KAM fetch ────────────────────────────────────────────────────────────────
def kam_fetch(report_type, metrics, attributes, filters, start, end, limit=100000):
    body = {
        "application": APPLICATION,
        "agencyId": None,  # filled by caller via _agency
        "reportType": report_type,
        "requestType": "REPORTING",
        "useExternalNames": False,
        "attributes": attributes or [],
        "metrics": metrics or [],
        "dateRanges": [{"startDate": start, "endDate": end}],
        "filters": filters or [],
        "limit": limit,
        "offset": 0,
    }
    return body


def _fetch(agency_id, report_type, metrics, attributes, filters, start, end, limit=100000):
    body = kam_fetch(report_type, metrics, attributes, filters, start, end, limit)
    body["agencyId"] = int(agency_id)
    r = _session.post(f"{BASE}/kamService/report/fetch", headers=HEADERS,
                      data=json.dumps(body), timeout=120)
    if r.status_code != 200:
        raise RuntimeError(f"KAM HTTP {r.status_code}: {r.text[:400]}")
    out = r.json()
    return out.get("data", out) if isinstance(out, dict) else out


def _period(args, kind="current"):
    """Extract [start, end] from args for 'current' or 'baseline'."""
    if kind == "current":
        return args["start_date"], args["end_date"]
    s, e = args.get("baseline_start_date"), args.get("baseline_end_date")
    return (s, e) if s and e else (None, None)


def _with_baseline(args, fn):
    """Run fn(start,end) for current, and for baseline if provided; return combined."""
    cs, ce = _period(args, "current")
    cur = fn(cs, ce)
    bs, be = _period(args, "baseline")
    if bs and be:
        return {"current": cur, "baseline": fn(bs, be)}
    return {"current": cur}


# ── External-report path — mirrors osmos-reporting-mcp (run_report over the catalogue) ──
def _fetch_ext(agency_id, report_type, attributes, metrics, filters, start, end, limit=1000):
    body = {"application": APPLICATION, "agencyId": int(agency_id), "reportType": report_type,
            "requestType": "REPORTING", "useExternalNames": True,
            "attributes": attributes or [], "metrics": metrics or [],
            "dateRanges": [{"startDate": start, "endDate": end}], "filters": filters or [],
            "limit": limit, "offset": 0}
    r = _session.post(f"{BASE}/kamService/report/fetch", headers=HEADERS,
                      data=json.dumps(body), timeout=120)
    if r.status_code != 200:
        raise RuntimeError(f"KAM HTTP {r.status_code}: {r.text[:400]}")
    out = r.json()
    return out.get("data", out) if isinstance(out, dict) else out


def t_run_report(a):
    """Generic run_report over the external catalogue — the shape osmos-reporting-mcp exposes."""
    return _with_baseline(a, lambda s, e: _fetch_ext(
        a["agency_id"], a["report_type"], a.get("attributes", []), a.get("metrics", []),
        a.get("filters", []), s, e, int(a.get("limit", 1000))))


def t_list_reports(a):
    """Discover the internal-performance reports in the external catalogue (like get_<group>_reports)."""
    r = _session.get(f"{BASE}/kamService/report/config/external",
                     params={"application": APPLICATION}, headers=HEADERS, timeout=60)
    reports = (r.json() or {}).get("reports", []) if r.status_code == 200 else []
    want = a.get("report_group")
    out = []
    for x in reports:
        tags = x.get("filterTags", [])
        if not any(t.startswith("report_group:") for t in tags):
            continue  # ours carry report_group:*; skip the production BEAT/PULSE reports
        if want and f"report_group:{want}" not in tags:
            continue
        out.append({"report_type": x.get("externalReportType"), "tags": tags,
                    "attributes": list((x.get("attributes") or {}).keys()),
                    "metrics": list((x.get("metrics") or {}).keys()),
                    "required_filters": x.get("externalRequiredFilters", [])})
    return {"reports": out, "count": len(out)}


# ── Tool handlers ─────────────────────────────────────────────────────────────
RR_METRICS = ["request_count", "response_count", "response_percentage"]


def t_check_ctr_overall(a):
    return _with_baseline(a, lambda s, e: _fetch(
        a["agency_id"], "KAM_AGENT_CTR_OVERALL",
        ["clicks", "impressions", "ctr", "spend"], [], [], s, e))


def t_get_page_level_performance(a):
    return _with_baseline(a, lambda s, e: _fetch(
        a["agency_id"], "KAM_AGENT_PAGE_LEVEL_PERFORMANCE",
        ["request_count", "response_count", "impressions", "clicks", "cost"],
        ["page_type"], [], s, e))


def t_check_response_rate_by_page(a):
    rt = "KAM_AGENT_RR_BY_PAGE_" + a.get("program_type", "pla").upper()
    return _with_baseline(a, lambda s, e: _fetch(
        a["agency_id"], rt, RR_METRICS, ["page_type"], [], s, e))


def t_check_display_page_type_rr(a):
    return _with_baseline(a, lambda s, e: _fetch(
        a["agency_id"], "KAM_AGENT_RR_DISPLAY_PAGE_TYPE",
        ["request_count", "response_count"], ["page_type"], [], s, e))


def t_get_category_response_rates(a):
    group_by = a.get("group_by") or ["category_l1"]
    return _with_baseline(a, lambda s, e: _fetch(
        a["agency_id"], "KAM_AGENT_RR_CATEGORY", RR_METRICS, group_by, [], s, e))


def t_get_response_rate_by_dimension(a):
    rt = "KAM_AGENT_RR_BY_DIMENSION_" + a.get("program_type", "pla").upper()
    dims = a.get("dimensions") or ["page_type"]
    return _with_baseline(a, lambda s, e: _fetch(
        a["agency_id"], rt, RR_METRICS, dims, [], s, e))


def t_check_requests(a):
    rt = "KAM_AGENT_BU_REQUESTS_" + a.get("program_type", "pla").upper()
    return _with_baseline(a, lambda s, e: _fetch(
        a["agency_id"], rt, RR_METRICS, ["date"], [], s, e))


def t_get_display_ad_unit_performance(a):
    return _with_baseline(a, lambda s, e: _fetch(
        a["agency_id"], "KAM_AGENT_BU_DISPLAY_AD_UNIT",
        ["request_count", "response_count", "impressions", "clicks", "cost",
         "program_per_click_timestamp_conversions", "program_per_click_timestamp_sales"],
        ["ad_unit_name", "page_type"], [], s, e))


def t_get_merchant_wallet_balance(a):
    # point-in-time; dates are inert but required by the fetch API shape
    rows = _fetch(
        a["agency_id"], "KAM_AGENT_BU_WALLET_BALANCE", ["placeholder_metric"],
        ["clients_client_id", "clients_seller_id", "clients_alias",
         "clients_remaining_budget_amount_usd", "conversion_factor"],
        [], "2000-01-01", "2000-01-01", limit=int(a.get("top_n", 50)))
    # derived layer: convert USD -> marketplace currency, apply the >= 0.01 floor
    for row in rows:
        usd = row.get("clients_remaining_budget_amount_usd") or 0
        factor = row.get("conversion_factor") or 0
        row["remaining_balance"] = round(usd * factor, 2) if usd >= 0.01 else 0
    rows.sort(key=lambda r: r["remaining_balance"], reverse=True)
    return {"merchants": rows[: int(a.get("top_n", 50))]}


def t_get_budget_delivery_mode(a):
    ids = [str(x) for x in (a.get("campaign_ids") or [])]
    filters = [{"key": "marketing_campaign_id", "operator": "IN", "values": ids}] if ids else []
    return _fetch(a["agency_id"], "KAM_AGENT_BUDGET_DELIVERY_MODE", ["placeholder_metric"],
                  ["marketing_campaign_id", "budget_delivery_mode"], filters,
                  "2000-01-01", "2000-01-01", limit=int(a.get("top_n", 100)))


def t_run_kam_agent_report(a):
    return _with_baseline(a, lambda s, e: _fetch(
        a["agency_id"], a["report_type"], a.get("metrics", []),
        a.get("attributes", []), a.get("filters", []), s, e))


# ── Tool registry (name -> (handler, description, inputSchema)) ────────────────
def _schema(props, required):
    return {"type": "object", "properties": props, "required": required}


_AG = {"agency_id": {"type": "integer", "description": "Marketplace agency id (e.g. 105)"}}
_CUR = {
    "start_date": {"type": "string", "description": "Current window start, YYYY-MM-DD"},
    "end_date": {"type": "string", "description": "Current window end, YYYY-MM-DD"},
}
_BASE_OPT = {
    "baseline_start_date": {"type": "string", "description": "Optional baseline start (enables WoW comparison)"},
    "baseline_end_date": {"type": "string", "description": "Optional baseline end"},
}
_PT = {"program_type": {"type": "string", "enum": ["pla", "display"], "description": "Ad channel"}}

TOOLS = {
    "check_ctr_overall": (t_check_ctr_overall,
        "Marketplace-level clicks / impressions / CTR / spend for a period (optionally vs a baseline).",
        _schema({**_AG, **_CUR, **_BASE_OPT}, ["agency_id", "start_date", "end_date"])),
    "get_page_level_performance": (t_get_page_level_performance,
        "PLA page-type breakdown: requests, responses, impressions, clicks, cost.",
        _schema({**_AG, **_CUR, **_BASE_OPT}, ["agency_id", "start_date", "end_date"])),
    "check_response_rate_by_page": (t_check_response_rate_by_page,
        "Response rate by page type (program_type pla|display).",
        _schema({**_AG, **_PT, **_CUR, **_BASE_OPT}, ["agency_id", "start_date", "end_date"])),
    "check_display_page_type_rr": (t_check_display_page_type_rr,
        "Display response rate by page type (from filtered-level facts).",
        _schema({**_AG, **_CUR, **_BASE_OPT}, ["agency_id", "start_date", "end_date"])),
    "get_category_response_rates": (t_get_category_response_rates,
        "Category-level (l1/l2/l3) response rate. Optional group_by list of category attrs.",
        _schema({**_AG, **_CUR, **_BASE_OPT,
                 "group_by": {"type": "array", "items": {"type": "string"},
                              "description": "e.g. [\"category_l1\",\"category_l2\"]"}},
                ["agency_id", "start_date", "end_date"])),
    "get_response_rate_by_dimension": (t_get_response_rate_by_dimension,
        "Response rate grouped by chosen dimension(s) (network, store_id, page_type, ad_unit_name, category_l1..). program_type pla|display.",
        _schema({**_AG, **_PT, **_CUR, **_BASE_OPT,
                 "dimensions": {"type": "array", "items": {"type": "string"}}},
                ["agency_id", "start_date", "end_date"])),
    "check_requests": (t_check_requests,
        "Daily request / non-zero-response volume for a period (program_type pla|display).",
        _schema({**_AG, **_PT, **_CUR, **_BASE_OPT}, ["agency_id", "start_date", "end_date"])),
    "get_display_ad_unit_performance": (t_get_display_ad_unit_performance,
        "Display ad-unit x page-type breakdown: requests, responses, impressions, clicks, cost, funnel (cost/sales are USD-basis).",
        _schema({**_AG, **_CUR, **_BASE_OPT}, ["agency_id", "start_date", "end_date"])),
    "get_merchant_wallet_balance": (t_get_merchant_wallet_balance,
        "Per-merchant remaining wallet balance (converted to marketplace currency, sorted desc). top_n optional.",
        _schema({**_AG, "top_n": {"type": "integer"}}, ["agency_id"])),
    "get_budget_delivery_mode": (t_get_budget_delivery_mode,
        "Budget delivery mode (ACCELERATED/STANDARD) for given campaign_ids (or a sample if omitted).",
        _schema({**_AG, "campaign_ids": {"type": "array", "items": {"type": "string"}},
                 "top_n": {"type": "integer"}}, ["agency_id"])),
    "run_kam_agent_report": (t_run_kam_agent_report,
        "POWER TOOL: fetch any KAM_AGENT_* report by name with explicit metrics/attributes/filters.",
        _schema({**_AG, **_CUR, **_BASE_OPT,
                 "report_type": {"type": "string"},
                 "metrics": {"type": "array", "items": {"type": "string"}},
                 "attributes": {"type": "array", "items": {"type": "string"}},
                 "filters": {"type": "array", "items": {"type": "object"}}},
                ["agency_id", "report_type", "start_date", "end_date"])),
    "list_reports": (t_list_reports,
        "Discover the internal-performance reports (report_type, columns, required_filters, tags). "
        "Optional report_group filter: roas|cpc|ctr|bu|rr|merchant_breakdown|category|sku|keyword|intake. "
        "Mirrors osmos-reporting-mcp's get_<group>_reports catalogue tools.",
        _schema({"report_group": {"type": "string"}}, [])),
    "run_report": (t_run_report,
        "Run any internal-performance report by external report_type (from list_reports), with "
        "attributes/metrics/filters. Mirrors osmos-reporting-mcp's run_report. "
        "filters = [{\"key\":..,\"operator\":\"IN\",\"values\":[..]}]. SKU/keyword reports require an os_client_id filter.",
        _schema({**_AG, **_CUR, **_BASE_OPT,
                 "report_type": {"type": "string", "description": "e.g. MERCHANT_ROAS_BREAKDOWN_REPORT"},
                 "attributes": {"type": "array", "items": {"type": "string"}},
                 "metrics": {"type": "array", "items": {"type": "string"}},
                 "filters": {"type": "array", "items": {"type": "object"}},
                 "limit": {"type": "integer"}},
                ["agency_id", "report_type", "start_date", "end_date"])),
}


# ── MCP stdio protocol (newline-delimited JSON-RPC 2.0) ────────────────────────
def _send(msg):
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def _result(id_, result):
    _send({"jsonrpc": "2.0", "id": id_, "result": result})


def _error(id_, code, message):
    _send({"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": message}})


def handle(msg):
    method = msg.get("method")
    id_ = msg.get("id")
    is_request = id_ is not None

    if method == "initialize":
        proto = (msg.get("params") or {}).get("protocolVersion", "2024-11-05")
        _result(id_, {
            "protocolVersion": proto,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "osmos-performance-local", "version": "0.1.0"},
        })
    elif method in ("notifications/initialized", "notifications/cancelled"):
        pass  # notifications: no response
    elif method == "ping":
        _result(id_, {})
    elif method == "tools/list":
        tools = [{"name": n, "description": d, "inputSchema": s}
                 for n, (_, d, s) in TOOLS.items()]
        _result(id_, {"tools": tools})
    elif method == "tools/call":
        params = msg.get("params") or {}
        name = params.get("name")
        args = params.get("arguments") or {}
        entry = TOOLS.get(name)
        if not entry:
            _result(id_, {"content": [{"type": "text", "text": f"Unknown tool: {name}"}],
                          "isError": True})
            return
        try:
            data = entry[0](args)
            text = json.dumps(data, indent=2, default=str)
            _result(id_, {"content": [{"type": "text", "text": text}], "isError": False})
        except Exception as ex:
            log("tool error:", name, repr(ex))
            _result(id_, {"content": [{"type": "text", "text": f"ERROR calling {name}: {ex}"}],
                          "isError": True})
    elif is_request:
        _error(id_, -32601, f"Method not found: {method}")


def selftest():
    log("selftest: fetching check_ctr_overall for agency 105 …")
    out = t_check_ctr_overall({"agency_id": 105, "start_date": "2026-07-19", "end_date": "2026-07-21"})
    print(json.dumps(out, indent=2))
    log("selftest: get_merchant_wallet_balance top 3 …")
    out = t_get_merchant_wallet_balance({"agency_id": 105, "top_n": 3})
    print(json.dumps(out, indent=2))


def main():
    if "--selftest" in sys.argv:
        selftest()
        return
    log("osmos-performance-local MCP server up (stdio). Tools:", ", ".join(TOOLS))
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except Exception:
            log("bad json:", line[:200])
            continue
        try:
            handle(msg)
        except Exception:
            log("handler crash:", traceback.format_exc())


if __name__ == "__main__":
    main()
