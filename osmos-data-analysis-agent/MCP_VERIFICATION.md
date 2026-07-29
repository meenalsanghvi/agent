# reporting-MCP verification — INTERNAL_PERFORMANCE endpoint

How to connect the new mount as an MCP in Claude Code and run the colleague's
positive + negative tests. **Gated:** the reporting-MCP endpoint must be deployed, and
our configs must already be re-posted as `INTERNAL_PERFORMANCE` (see
`kam_report_configs/repost_internal_performance.sh`) so they show up.

## 1. MCP config to add (`.mcp.json`)
Add both mounts — the new one (positive) and the existing `beatsInternal` (negative
guard). Fill in `<reporting-mcp-host>` and the Hades auth header (confirm exact scheme
with the reporting-MCP owner — internal `@onlinesales.ai` / `@osmos.ai` identities
resolve to `INTERNAL_USER`, level 3, which meets the endpoint's requirement).

```jsonc
{
  "mcpServers": {
    "osmos-reporting-internal-performance": {
      "type": "http",
      "url": "https://<reporting-mcp-host>/osmosReportingMcp/internal/performance",
      "headers": { "Authorization": "Bearer <HADES_TOKEN>" }
    },
    "osmos-reporting-beats-internal": {
      "type": "http",
      "url": "https://<reporting-mcp-host>/osmosReportingMcp/beatsInternal",
      "headers": { "Authorization": "Bearer <HADES_TOKEN>" }
    }
  }
}
```
(An example lives at `.claude/mcp.internal-performance.example.json`.)

## 2. Positive test — new endpoint serves our reports
1. `GET https://<reporting-mcp-host>/osmosReportingMcp/internal/performance/health` → 200.
2. In Claude Code, `/mcp` → `osmos-reporting-internal-performance` connected.
3. List tools → expect the auto-minted catalogue tools from our `report_group:*` tags
   (`get_rrs_reports`, `get_bus_reports`, `get_ctrs_reports`, `get_campaigns_reports`, …)
   plus `run_report`.
4. `run_report` a known report end-to-end, e.g. `CTR_OVERALL_REPORT`, agencyId 105,
   a recent window → expect real rows (converted spend, etc.).
5. Spot-check a filtered one, e.g. `MERCHANT_CATEGORY_PERFORMANCE_REPORT` with
   `os_client_id=10009172`, or `SEARCH_QUERY_CAMPAIGNS_REPORT` with `search_query=iphone`.

## 3. Negative test — our reports must NOT appear on beatsInternal (prod-Sofie mount)
1. `/mcp` → `osmos-reporting-beats-internal` connected.
2. List its catalogue tools / reports → confirm **none** of our `INTERNAL_PERFORMANCE`
   reports appear (no `*_RR_*`, `MERCHANT_*`, `CAMPAIGN_*`, `SEARCH_QUERY_*`, `BUDGET_*`,
   `MINUTE_*`, `CATEGORY_LEVEL`, `WALLET_BALANCE`, `PROBLEM_METRICS`, `MARKETPLACE_DIRECTORY`, …).
3. `beatsInternal` should show only its usual BEATS/INTERNAL_USER production reports.

> Why this matters: `beatsInternal` serves `["BEATS","INTERNAL_USER"]`. Our reports are
> `INTERNAL_PERFORMANCE`, so once re-posted they only surface on the dedicated
> `/internal/performance` mount and are invisible here. **If any of ours DO show on
> beatsInternal, the re-post step didn't run or a config is still `INTERNAL_USER`.**

## 4. kamService-side quick checks (no MCP needed)
```
# positive — our reports present:
curl -s --noproxy '*' -G '<KAM>/kamService/report/config/external' \
  --data-urlencode 'jsonQuery={"visibility":"INTERNAL_PERFORMANCE","application":"irisTestApplication"}'
# negative — none of ours:
curl -s --noproxy '*' -G '<KAM>/kamService/report/config/external' \
  --data-urlencode 'jsonQuery={"visibility":"INTERNAL_USER","application":"irisTestApplication"}'
curl -s --noproxy '*' -G '<KAM>/kamService/report/config/external' \
  --data-urlencode 'jsonQuery={"visibility":"BEATS","application":"irisTestApplication"}'
```
The automated version of these lives in the kamService PR:
`tests/src/dbaccessor/getExternalReportConfigs.test.js` and
`tests/src/routes/api/report/config/external/externalConfig.validator.test.js`.

## Current status (before deploy)
Our 63 configs are still posted in the test env as `INTERNAL_USER` → today they DO show
under `visibility=INTERNAL_USER` (and would appear on beatsInternal). The on-disk files are
already flipped to `INTERNAL_PERFORMANCE`; the re-post (step gated on the validator deploy)
is what makes both tests pass.
