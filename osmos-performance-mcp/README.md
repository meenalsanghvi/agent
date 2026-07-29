# osmos-performance-mcp

MCP server exposing the **marketplace data-analysis agent's SOP tools** to Claude
Code / the Claude Agent SDK. It is the runtime data layer for the agent's skills
(`osmos-data-analysis-agent/.claude/skills`).

```
Claude Code / Agent SDK
  → skill (playbook — names the tool)
  → THIS server (tool: fetch KAM report(s) + run the Python derived-math)
  → KAM service (/report/fetch, class-based KAM_AGENT_* configs)
  → BigQuery
```

Built on the same skeleton as `osmos-reporting-mcp` (FastMCP + `build_mcp()` +
Starlette/uvicorn, `KAMClient` over `osSvcClient4pyV2`, pydantic settings,
Hades-backed Redis rate limiting, ACL middleware). The difference: instead of one
generic `run_report`, it exposes **named SOP tools** (`check_gmv_attribution`,
`get_merchant_breakdown`, …) that each fetch a fixed `KAM_AGENT_*` report and run
the derived-metric layer (`metrics.py`, lifted from the agent's `utils/helpers.py`).

## Layout
```
src/osmos_performance_mcp/
├── server.py            # build_mcp() → single internal endpoint (/osmosPerformanceMcp)
├── config/              # settings, redis_config (Hades)
├── clients/kam_client.py# KAMClient over osSvcClient4pyV2 (reused) + fetch_agent_report helper
├── schemas/common.py    # FilterItem, OrderByItem, DateRange
├── auth/scopes.py       # resolve_user_scope
├── middleware/          # ACLMiddleware, ResponseSizeMiddleware
├── metrics.py           # derived math: pct_change, contribution_pct, roi_ratio, pareto, combine_* …
├── report_map.py        # tool → KAM reportType(s) + metric keys per program_type
└── tools/               # register_<group>_tools(mcp): roas, cpc, ctr, bu, rr,
                         #   budget_pacing, keyword_delivery, keyword_low_rr,
                         #   irrelevancy, campaign, common
```

## Status
- **Reference tool wired:** `check_gmv_attribution` (ROAS) — the validated
  two-report split (`KAM_AGENT_ROAS_PROGRAM_FUNNEL` + `KAM_AGENT_ROAS_SITE_FUNNEL`)
  combined in `metrics.combine_gmv_attribution`.
- **Everything else:** registered with the same pattern; each raises a clear
  "KAM config pending validation" error until its `KAM_AGENT_*` config is authored
  and validated (see `osmos-data-analysis-agent/kam_report_configs/`).

## Run (local)
```bash
uv sync            # needs the internal GCP package index (see pyproject)
cp .env.example .env
python -m osmos_performance_mcp.server
# → http://localhost:8080/osmosPerformanceMcp
```

## Test
```bash
uv run pytest
```

## Adding a tool (as a KAM config validates)
1. Author + validate the `KAM_AGENT_*` config (agent repo `kam_report_configs/`).
2. Add its `reportType` + per-`program_type` metric keys to `report_map.py`.
3. Implement the tool body in the right `tools/<group>.py` (fetch via
   `KAMClient.fetch_agent_report`, combine with `metrics.*`), keeping the tool
   name/args/return shape identical to the legacy `weekly_analysis_agent` tool.
