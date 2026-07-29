# Prompt — Build `osmos-performance-mcp`

Build the runtime MCP server for the data-analysis agent, mirroring the org's
`osmos-reporting-mcp` skeleton (`/Users/manav.kumawat/Desktop/osmos-reporting-mcp`).

## Goal
A FastMCP HTTP server that exposes the agent's SOP tools (the names the
`.claude/skills` call — `check_gmv_attribution`, `get_merchant_breakdown`, …).
Each tool: fetch the KAM report(s) via `KAMClient` → run the Python derived-math
(contribution %, verdicts, Pareto, CVRs) → return the shaped dict. This is the
third leg (skills → **MCP server** → KAM configs).

## Keep the org skeleton (reuse, don't reinvent)
Same package layout, deps, and conventions as `osmos-reporting-mcp`:
- **FastMCP** + `build_mcp()` factory mounted via Starlette/uvicorn (`server.py`).
- **`KAMClient`** wrapping `osSvcClient4pyV2.KamServiceClient` — reuse ~verbatim
  (`fetch_report(payload, entity_type, fetch_mode)`, `fetch_catalog`).
- **`config/settings.py`** (pydantic-settings) + **`config/redis_config.py`**
  (Hades-fetched Redis for rate limiting) — reuse.
- **Middleware**: `ResponseSizeMiddleware` (reuse), `ACLMiddleware` (reuse the
  os-pyutils AuthHandler pattern; single internal endpoint → `allowed_entity_types=None`).
- **`tools/decorators.py`** `@rate_limit` + **`tools/context.py`** — reuse.
- **`schemas/common.py`** (`FilterItem`, `OrderByItem`, `DateRange`).
- Same `pyproject.toml` deps (`fastmcp`, `os-svc-client-v2`, `os-pyutils`,
  `pydantic`, `uvicorn`, `redis`) + the internal GCP package index, same `Dockerfile`.

## What's different from reporting-mcp
- **Tools, not a generic `run_report`.** Replace `tools/run_report.py` with one
  module per metric group (`tools/roas.py`, `cpc.py`, …), each a
  `register_<group>_tools(mcp)` that registers the named SOP tools.
- **New `metrics.py`** — the derived-math layer lifted verbatim from
  `weekly_analysis_agent/utils/helpers.py` (`pct_change`, `contribution_pct`,
  `share_pct`, `cvr`, `roi_ratio`, `cpc_ratio`, `ctr_ratio`, `ir_ratio`,
  `pareto_high_impact`, `sanitize_output`) + `combine_*` funcs (e.g.
  `combine_gmv_attribution` = the ROAS trend-verdict/user-intent logic).
- **New `report_map.py`** — tool → KAM `reportType`(s) + metric keys per
  `program_type`. The single place that names the `KAM_AGENT_*` reports.
- **Drop `catalog/`** and the run_report `ResponseFormatMiddleware` — our tools call
  fixed `KAM_AGENT_*` reports with known keys; no dynamic catalog validation.
- **One internal endpoint** (`/osmosAnalysisAgentMcp`), not 5 visibility endpoints.

## Tool contract (matches the skills + the legacy Python tools)
Each tool keeps the **same name, args, and return shape** as the current
`weekly_analysis_agent/tools/*` function it replaces — only the data source
changes (`run_query(sql)` → `kam_client.fetch_report(KAM_AGENT_* payload)`), the
math stays. Comparison mode = two `dateRanges` in the payload.

## Reference implementation
Fully wire **`check_gmv_attribution`** (ROAS) using the validated two-report split:
fetch `KAM_AGENT_ROAS_PROGRAM_FUNNEL` + `KAM_AGENT_ROAS_SITE_FUNNEL`, combine in
`metrics.combine_gmv_attribution`. Every other tool follows this exact pattern and
is filled in as its KAM config passes validation (raise a clear "config pending"
error until then, so the tool surface is complete and the gaps are explicit).

## Definition of done
Complete, faithful repo: packaging (pyproject/Dockerfile/.env.example/.gitignore/
.dockerignore/README), `src/osmos_performance_mcp/` (server, config, clients,
schemas, auth, middleware, metrics, report_map, tools/*), and `tests/` (metrics
unit tests + a tool smoke test). `check_gmv_attribution` wired end-to-end; other
SOP tools registered with the pattern + "pending" markers. Names align 1:1 with
the skills' tool references.
