# Local demo — run the agent in Claude Code (just for you)

A laptop-only setup to *see* the data-analysis agent work: the debug-* skills drive
real MCP tool calls against the **validated** config-only KAM reports on the KAM
**test** env. No Hades/Redis/token/deploy — a stdlib stdio shim
(`osmos-performance-mcp/local_dev_server.py`) stands in for the hosted MCP.

> This is a demo stand-in, NOT the production MCP. Only the ~config-only tools are
> backed (see "What's backed" below). Deeper SOP steps that need not-yet-built
> reports will come back as "Unknown tool" — that's expected for now.

## Prerequisites (already verified)
- `python3` on PATH with `requests` installed.
- Network reachability to `http://test.onlinesales.ai` (VPN/office network).
- The KAM_AGENT_* configs posted to test (done during validation).

## Run it
```bash
cd /Users/manav.kumawat/Documents/agent/osmos-data-analysis-agent
claude
```
On first launch Claude Code sees `.mcp.json` and asks to approve the
`osmos-performance-local` server → approve it.

Verify the connection:
```
/mcp
```
You should see `osmos-performance-local` connected with 11 tools.

## Try a prompt (stays within backed tools)
```
For agency 105, response rate looks off for the week 2026-07-19 to 2026-07-21
versus the prior week 2026-07-12 to 2026-07-18. Dig into why — break it down by
page type and by category.
```
This triggers the **debug-rr** skill, which calls `check_requests`,
`check_response_rate_by_page`, and `get_category_response_rates` — all backed —
and reasons over the real rows.

Simpler single-tool sanity prompt:
```
Using the tools, what was agency 105's CTR, clicks, impressions and spend for
2026-07-19 to 2026-07-21?
```

## Faithful reporting-mcp shape (covers ALL authored reports)
The shim now also exposes the two tools the real `osmos-reporting-mcp` will:
- **`list_reports`** — discover the internal-performance reports (report_type, columns,
  required_filters, tags). Optional `report_group` filter (roas|cpc|ctr|bu|rr|
  merchant_breakdown|category|sku|keyword|intake). = the `get_<group>_reports` catalogue tools.
- **`run_report`** — run any report by external `report_type` (from `list_reports`) with
  attributes/metrics/filters (+ optional baseline window). = the real `run_report`.

Demo prompt that exercises the target architecture end-to-end:
```
For agency 105, analyse ROAS for 2026-07-19..2026-07-21 vs the prior week
2026-07-12..2026-07-18. Use list_reports to find the right reports, then run_report to
pull the merchant breakdown, and tell me which merchants drove the change.
```
(SKU/keyword reports need an `os_client_id` filter, e.g. `{"key":"os_client_id","operator":"IN","values":["277661"]}`.)

## What's backed by the named tools (11)
`check_ctr_overall`, `get_page_level_performance`, `check_response_rate_by_page`
(pla/display), `check_display_page_type_rr`, `get_category_response_rates`,
`get_response_rate_by_dimension` (pla/display), `check_requests` (pla/display),
`get_display_ad_unit_performance`, `get_merchant_wallet_balance`,
`get_budget_delivery_mode`, plus `run_kam_agent_report` (power tool: fetch any
KAM_AGENT_* report by name).

Not yet backed (needs-class / unauthored): merchant breakdowns (ROAS/CPC/CTR/RR/BU),
search-query RR, SKU drill-downs, ROAS GMV attribution, campaign/budget-pacing/
irrelevancy deep tools. Asking for those will hit "Unknown tool".

## Troubleshooting
- **Server won't start / no tools in `/mcp`**: run the shim directly —
  `python3 /Users/manav.kumawat/Documents/agent/osmos-performance-mcp/local_dev_server.py --selftest`
  (should print CTR + wallet rows). Check `requests` is importable by the `python3`
  on PATH.
- **KAM connection errors**: confirm VPN; a stray `HTTP_PROXY` is already bypassed
  by the shim (`trust_env=False`).
- **A tool returns "Unknown tool"**: that report isn't backed yet (see above) — pick
  a prompt that stays within the backed set.
