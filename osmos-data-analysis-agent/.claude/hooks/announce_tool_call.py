#!/usr/bin/env python3
"""PreToolUse hook: surface every tool call to the user in plain language.

Claude Code already shows the main agent's tool calls inline, but calls made
inside a subagent (e.g. sku-drilldown) or deep in a debug-* skill run are
collapsed. Emitting `systemMessage` puts one line per call in front of the user
regardless of nesting depth.

The announced text is a friendly LABEL, not the raw tool name — a KAM reading the
trace should see "Merchant breakdown (ROAS/CPC/CTR/spend)", not
`run_report report_type=MERCHANT_PERFORMANCE`. Renaming here is display-only; the
real tool names are owned by the reporting MCP.

Only data-fetching / delegating tools are announced, so the trace reads as "which
reports did the agent pull" rather than every file read.
"""

import json
import re
import sys

# Built-ins worth announcing. MCP tools (mcp__*) are always announced.
ANNOUNCE_BUILTINS = {"Task", "Bash", "WebFetch"}

# ── Labels ────────────────────────────────────────────────────────────────────
# On the real endpoint nearly every data call is `run_report`, so the meaningful
# label comes from report_type. Keys are the catalogue's externalReportType.
REPORT_LABELS = {
    "MERCHANT_PERFORMANCE": "Merchant breakdown (spend, CTR, CPC, ROAS, site funnel)",
    "SKU_PERFORMANCE": "SKU drill-down",
    "CATEGORY_PERFORMANCE": "Category breakdown",
    "RR_PLA": "Response rate by page type (PLA)",
    "RR_DISPLAY": "Response rate by page type (Display)",
    "PAGE_PERFORMANCE_PLA": "Page-level performance (PLA)",
    "DISPLAY_AD_UNIT": "Display ad-unit performance",
    "SEARCH_QUERY_REQUESTS_PLA": "Search-query requests and fill",
    "KEYWORD_PERFORMANCE": "Keyword performance",
    "SEARCH_QUERY_PERFORMANCE": "Search-query performance",
    "CAMPAIGN_PERFORMANCE": "Campaign performance",
    "CAMPAIGN_KEYWORDS": "Campaign keywords",
    "CAMPAIGN_NETWORKS": "Campaign networks",
    "GMV_ATTRIBUTION": "GMV attribution",
    "AUDIT_EVENTS": "Audit log",
    "CTR_OVERALL_REPORT": "Overall CTR, clicks, impressions and spend",
}

# Named tools on the local dev shim (LOCAL_DEMO.md). The hosted endpoint exposes
# run_report instead, but these stay so the trace reads the same either way.
TOOL_LABELS = {
    "check_ctr_overall": "Overall CTR, clicks, impressions and spend",
    "get_page_level_performance": "Page-level performance",
    "check_response_rate_by_page": "Response rate by page type",
    "check_display_page_type_rr": "Response rate by page type (Display)",
    "get_category_response_rates": "Category response rates",
    "get_response_rate_by_dimension": "Response rate by dimension",
    "check_requests": "Ad requests and fill",
    "get_display_ad_unit_performance": "Display ad-unit performance",
    "get_merchant_wallet_balance": "Merchant wallet balance",
    "get_budget_delivery_mode": "Budget delivery mode",
    "run_kam_agent_report": "KAM report",
    "fetch_marketplace_info": "Marketplace lookup",
    "get_problem_metrics": "Flagged issues for the week",
    "list_reports": "Discovering available reports",
    "run_report": "Report",  # refined by report_type below
}

BUILTIN_LABELS = {
    "Bash": "Running a command",
    "WebFetch": "Fetching a page",
}

# Argument keys worth showing, most useful first.
INTERESTING_KEYS = (
    "agency_id",
    "os_client_id",
    "start_date",
    "end_date",
    "dimension",
    "channel",
    "keyword",
    "campaign_id",
    "description",
    "command",
)

MAX_VALUE_LEN = 60


def prettify(name):
    """get_display_ad_unit_performance -> 'Display ad unit performance'."""
    words = re.sub(r"^(get|check|fetch|run|list)_", "", name).replace("_", " ").strip()
    return words[:1].upper() + words[1:] if words else name


def label_for(tool_name, tool_input):
    """Human-readable label for a tool call, plus the MCP server it belongs to."""
    server = None
    bare = tool_name

    if tool_name.startswith("mcp__"):
        bits = tool_name.split("__")
        if len(bits) >= 3:
            server, bare = bits[1], bits[-1]
            # A plugin-shipped MCP server is scoped plugin_<plugin>_<server>.
            if server.startswith("plugin_"):
                server = server.split("_", 2)[-1]

    if bare == "Task":
        agent = tool_input.get("subagent_type") or "sub-agent"
        return f"Delegating to {agent}", None

    if bare in BUILTIN_LABELS:
        return BUILTIN_LABELS[bare], None

    # Catalogue discovery tools: get_<group>_reports
    m = re.match(r"^get_(.+)_reports$", bare)
    if m:
        group = m.group(1).replace("_", " ")
        return f"Discovering available {group} reports", server

    label = TOOL_LABELS.get(bare, prettify(bare))

    # run_report carries the real subject in report_type.
    if bare == "run_report":
        rt = tool_input.get("report_type")
        if rt:
            label = REPORT_LABELS.get(rt, prettify(rt.lower()))

    return label, server


def summarise(tool_input):
    parts = []
    for key in INTERESTING_KEYS:
        if key not in tool_input:
            continue
        value = tool_input[key]
        if isinstance(value, (dict, list)):
            value = json.dumps(value, separators=(",", ":"))
        value = str(value)
        if len(value) > MAX_VALUE_LEN:
            value = value[: MAX_VALUE_LEN - 1] + "…"
        parts.append(f"{key}={value}")
        if len(parts) == 3:
            break
    return ", ".join(parts)


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # never get in the way of a tool call

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        tool_input = {}

    is_mcp = tool_name.startswith("mcp__")
    if not is_mcp and tool_name not in ANNOUNCE_BUILTINS:
        return 0

    label, server = label_for(tool_name, tool_input)
    args = summarise(tool_input)

    message = f"🔧 {label}"
    if args:
        message += f" — {args}"
    if server:
        message += f"  ·  {server}"

    json.dump({"systemMessage": message, "suppressOutput": True}, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
