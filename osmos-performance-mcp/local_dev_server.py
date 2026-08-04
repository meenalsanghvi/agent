#!/usr/bin/env python3
"""
local_dev_server.py — a laptop-only stdio MCP server for demoing the data-analysis agent
========================================================================================
A dependency-light (stdlib + `requests`) MCP server that exposes the SAME surface as the
hosted osmos-reporting-mcp -- list_reports + run_report over the external catalogue --
by calling the KAM **test** env directly — NO Hades, NO Redis,
NO x-token, NO private package registry, NO port. This is the "just-for-me" stand-in
for the hosted `osmos-performance-mcp`; it is NOT the production server.

It speaks MCP over stdio (newline-delimited JSON-RPC 2.0), so Claude Code launches it
as a subprocess (see osmos-data-analysis-agent/.mcp.json).

Deliberately NO per-SOP named tools. Earlier revisions exposed check_*/get_* wrappers
bound to the retired KAM_AGENT_* generation, which the 70->43 consolidation superseded;
they kept working only because KAM has no delete API, so a green test proved nothing
about the reports that actually ship. Every call now goes through the live external
catalogue, and all derived math is the agent's job -- same as production.

Data source: http://test-data.onlinesales.ai/kamService/report/fetch  (must be reachable).
The INTERNAL_PERFORMANCE configs must already be posted to test (all 43 are).

Run standalone sanity check:  python3 local_dev_server.py --selftest
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import traceback

import requests

BASE = "http://test-data.onlinesales.ai"
APPLICATION = "irisTestApplication"
HEADERS = {"Content-Type": "application/json"}

# A session that IGNORES environment proxies (a stray HTTP_PROXY was intercepting calls).
_session = requests.Session()
_session.trust_env = False


def log(*a):
    print("[local-mcp]", *a, file=sys.stderr, flush=True)


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
# Rows are never dropped. The only real constraint is how much JSON can cross stdio in one
# response — ~27 MB of CAMPAIGN_LOOKUP_REPORT drops the connection. So above this many rows
# we write the COMPLETE result to a file and hand back the path plus its shape. The caller
# analyses the file with shell tools, which is what an analysis agent needs: all the data,
# without paying for it in context.
INLINE_ROW_CAP = 400
KAM_MAX_LIMIT = 100_000          # kamService rejects anything above this
SPILL_DIR = os.environ.get("OSMOS_MCP_SPILL_DIR") or tempfile.gettempdir()


def _page(agency_id, report_type, attributes, metrics, filters, start, end, limit, offset):
    body = {"application": APPLICATION, "agencyId": int(agency_id), "reportType": report_type,
            "requestType": "REPORTING", "useExternalNames": True,
            "attributes": attributes or [], "metrics": metrics or [],
            "dateRanges": [{"startDate": start, "endDate": end}], "filters": filters or [],
            "limit": limit, "offset": offset}
    r = _session.post(f"{BASE}/kamService/report/fetch", headers=HEADERS,
                      data=json.dumps(body), timeout=300)
    if r.status_code != 200:
        raise RuntimeError(f"KAM HTTP {r.status_code}: {r.text[:400]}")
    out = r.json()
    return out.get("data", out) if isinstance(out, dict) else out


def _fetch_ext(agency_id, report_type, attributes, metrics, filters, start, end, limit=None):
    # No limit given means "the whole answer". kamService caps a single page at 100k, and
    # several reports exceed that (CAMPAIGN_LOOKUP_REPORT is ~186k), so walk pages with
    # offset until one comes back short. This is only sound because the report configs now
    # carry ORDER BY — without a stable sort, BigQuery may order pages differently and
    # offset paging would silently overlap or skip rows.
    args = (agency_id, report_type, attributes, metrics, filters, start, end)
    if limit is not None:
        data = _page(*args, int(limit), 0)
        pages = 1
    else:
        data, off, pages = [], 0, 0
        while True:
            chunk = _page(*args, KAM_MAX_LIMIT, off)
            pages += 1
            if not isinstance(chunk, list):
                return chunk
            data.extend(chunk)
            if len(chunk) < KAM_MAX_LIMIT:
                break
            off += KAM_MAX_LIMIT

    if not isinstance(data, list) or len(data) <= INLINE_ROW_CAP:
        return data

    # Spill the full set. JSONL so it streams and every row survives verbatim.
    slug = re.sub(r"[^A-Za-z0-9]+", "_", f"{report_type}_{agency_id}_{start}_{end}").strip("_")
    path = os.path.join(SPILL_DIR, f"kam_{slug}_{len(data)}rows.jsonl")
    with open(path, "w") as fh:
        for row in data:
            fh.write(json.dumps(row) + "\n")
    return {
        "rows_file": path,
        "format": "jsonl",
        "row_count": len(data),
        "complete": limit is None,
        "pages_fetched": pages,
        "columns": sorted(data[0].keys()) if isinstance(data[0], dict) else None,
        "sample": data[:5],
        "note": (f"COMPLETE result set — all {len(data):,} rows written to {path}. Nothing was "
                 f"dropped. Too large to return inline without risking the stdio connection, so "
                 f"analyse the file directly (python/jq/awk) rather than re-fetching a smaller "
                 f"slice: totals, Pareto and per-entity aggregates are all valid on it. "
                 f"`sample` is the first 5 rows for shape only — row order follows the report's "
                 f"attributes, not magnitude, so do not read it as a ranking."),
    }


def t_run_report(a):
    """Generic run_report over the external catalogue — the shape osmos-reporting-mcp exposes."""
    return _with_baseline(a, lambda s, e: _fetch_ext(
        a["agency_id"], a["report_type"], a.get("attributes", []), a.get("metrics", []),
        a.get("filters", []), s, e, a.get("limit")))


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
        if want:
            # substring match on the group segment: "budget" hits budget_utilisation
            # AND budget_pacings, and a caller need not know the exact tag spelling.
            groups = [t.split("report_group:", 1)[1] for t in tags if t.startswith("report_group:")]
            if not any(want.lower() in g.lower() for g in groups):
                continue
        out.append({"report_type": x.get("externalReportType"), "tags": tags,
                    "attributes": list((x.get("attributes") or {}).keys()),
                    "metrics": list((x.get("metrics") or {}).keys()),
                    "required_filters": x.get("externalRequiredFilters", [])})
    return {"reports": out, "count": len(out)}


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

TOOLS = {
    "list_reports": (t_list_reports,
        "Discover the internal-performance reports (report_type, columns, required_filters, tags). "
        "Optional report_group filter - the tags as they exist in the live catalogue: "
        "budget_utilisation | campaigns | response_rate | budget_pacings | categories | roas | "
        "click_through | merchant_breakdowns | search_queries | keywords | intake | cost_per_click | "
        "skus | page_performances | relevance. Substring match, so 'budget' matches both budget_* "
        "groups. Call with no filter to see everything. "
        "Mirrors osmos-reporting-mcp's get_<group>_reports catalogue tools.",
        _schema({"report_group": {"type": "string"}}, [])),
    "run_report": (t_run_report,
        "Run any internal-performance report by external report_type (from list_reports), with "
        "attributes/metrics/filters. Mirrors osmos-reporting-mcp's run_report. "
        "filters = [{\"key\":..,\"operator\":\"IN\",\"values\":[..]}]. Reports with required filters "
        "reject calls that omit them. Derived math (currency conversion, deltas, ratios, sorting) is "
        "yours to do - the report returns raw columns, exactly as the hosted MCP will.",
        _schema({**_AG, **_CUR, **_BASE_OPT,
                 "report_type": {"type": "string", "description": "e.g. RR_PLA_REPORT"},
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
    """Exercise the two tools the agent actually gets, against the live catalogue."""
    log("selftest: list_reports report_group=response_rate …")
    rr = t_list_reports({"report_group": "response_rate"})
    print(json.dumps(rr, indent=2)[:900])

    log("selftest: run_report RR_PLA_REPORT by page type, agency 105 …")
    out = t_run_report({"agency_id": 105, "report_type": "RR_PLA_REPORT",
                        "attributes": ["perf_page_type"],
                        "metrics": ["perf_requests", "perf_responses", "perf_response_rate"],
                        "start_date": "2026-07-19", "end_date": "2026-07-21", "limit": 10})
    print(json.dumps(out, indent=2)[:900])


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
