# KAM report configs for the data-analysis agent

Class-based KAM report configs that back the agent's SOP tools. Data flows through
KAM (`/api/report/fetch` or the `run_kam_report` MCP tool) instead of raw BigQuery;
the agent's **Python layer still computes the derived metrics** (deltas,
contribution %, CVRs, verdicts, Pareto) on the raw aggregates KAM returns.

## ⚠️ Read this first — the configs were consolidated

**41 active configs, down from 70.** 42 near-duplicate configs were merged into 15
reports and moved to `_retired/`. The redundancy came from authoring one report per
*call-site* instead of per *dataset*, so the same fact table was re-authored once per
metric SOP and once per `GROUP BY`.

- **`MERGE_ANALYSIS.md`** — what the flow is, why the duplication happened, and the
  engine mechanism (`__ATTRIBUTES__` / `__ATTRIBUTES_GROUP_BY__` are built from the
  *requested* columns) that makes one config serve many grains.
- **`MERGE_MAP.md`** — retired reportType → its replacement, and the filter or grouping
  a caller must now pass. **Check this before changing a call site.**
- `../scripts/merge_wave{1,2,3}.py` — the merge specs (re-runnable, idempotent).
- `../scripts/validate_merged.py` — coverage + alias + tag checks. Run after any change.

Before reposting the merged reports, re-read the "Still to do" list in
`MERGE_ANALYSIS.md` — the retired reportTypes are still live in the test catalogue.

## Class-based (the org standard)

Confirmed against `kamService/src/utils/schema/`: newer configs declare
`attributesClasses` / `metricsClasses` (arrays of registry class names) instead of
inlining a `metrics` map. At fetch time `schemaRegistry.generateSchemaFromClassArrays`
inflates the classes into the `metrics`/`attributes` maps the substitution engine
uses.

**Comparison mode — VERIFIED on test agency 105:** KAM does **not** auto-emit
`_prev`/`_change`/`_perc` comparison variants (a single fetch with two dateRanges
returned only window-1 metrics). Each `KAM_AGENT_*` report is **single-period**
(`dateRanges.count: 1`); the agent fetches **current and baseline as two separate
calls** and combines them in Python — mirroring the legacy `roi_analysis_tools`
two-`_overall` design.

**Authoring rules (from the class system):**
- Table `AS <alias>` in the query MUST equal the class's default alias
  (`monetize_merchant_facts` → `mmf`, `monetize_merchant_dimensions` → `mmd`,
  `static_currency_conversion` → `scc` for most classes; **but `MonetizeMerchantFacts`'s
  `site_*` selectors reference the full name `static_currency_conversion`**, so that
  is the alias used here).
- Metric selectors carry their own aggregation + `__START_DATE_1__` window; you only
  supply the JOINs their selectors require.
- Request the metric KEYS per program type (below); the config exposes all of them.

## Tool → reportType map (ROAS, in progress)

| Agent tool | KAM reportType | Classes | Status |
|---|---|---|---|
| `check_gmv_attribution` | `KAM_AGENT_ROAS_GMV_ATTRIBUTION` | MonetizeMerchantFacts + MonetizeMerchantDimensions | drafted (validate) |
| `get_daily_order_trends` | `KAM_AGENT_ROAS_DAILY_ORDER_TRENDS` | — | todo |
| `get_merchant_breakdown` | `KAM_AGENT_ROAS_MERCHANT_BREAKDOWN` | — | todo |
| `get_sku_level_performance` | `KAM_AGENT_ROAS_SKU_PERFORMANCE` | — | todo |
| `get_target_roi` | `KAM_AGENT_ROAS_TARGET_ROI` | Agencies (`onsite_target_roi`) | todo |

## `KAM_AGENT_ROAS_GMV_ATTRIBUTION` (first config)

Marketplace-level (agency-wide, all seller merchants, no grouping) → `requestType:
"REPORTING"`, `SELECT __METRICS__` with no GROUP BY. Comparison via `dateRanges.count
= 2` (request sends `dateRanges: [current, baseline]`).

**Site keys (RESOLVED — match the Python baseline exactly):** request
`site_revenue` (= `SUM(total_sok_sales_usd * conversion_factor)`, identical to the
baseline), `site_orders` (= `total_sok_salecompletes`), `site_viewproducts`,
`site_add2carts`. **Do NOT use `site_sales`** — it is native `total_sok_sales` (no
conversion) and does NOT match the baseline. `site_cvr` = site_orders ÷
site_viewproducts is computed in Python. The report is single-period (`count: 1`);
the tool fetches current + baseline as two separate calls.

**Program keys — DECISION PENDING (see Validation status).** The Python baseline's
program funnel uses **`program_per_click_timestamp_*`** from
`client_vendor_channel_performance_facts`. `MonetizeMerchantFacts` does NOT expose
overall per-click-timestamp keys — only native `program_orders` / `program_revenue`
(a different attribution). So the program-side metric keys depend on which path we
take (below). `attributed_cvr` is computed in Python from whichever
orders/viewproducts keys we settle on.

## Validation status (gate a + b run on agency 105, 2026-07-19→21)

**RESOLVED and applied to the config:**
- **3-key `mmd` join** (`+ marketplace_client_id`) — canonical form; prevents fan-out
  where a merchant_id spans multiple marketplace_client_ids (latent, not active on 105).
- **Site currency → marketplace currency.** Join `marketplace_clients` and convert
  `to_currency = mc.currency` (matches baseline) — not `mmd.currency`. Request
  `site_revenue` (converted), not `site_sales` (native). This is the exact baseline
  site formula.
- **`static_currency_conversion` is now a real, `LEFT` join.** With `site_revenue`
  requested, the selector uses the join (no longer dead). `LEFT` + a single
  marketplace currency avoids the row-drop that the old INNER `to=mmd.currency` join
  caused (empirically +13 site_orders / +3,045 site_sales recovered on 105).

**OPEN — program-side attribution fork (blocks final sign-off):**
The Python baseline builds the PROGRAM funnel from
`client_vendor_channel_performance_facts` with **per-click-timestamp** attribution
(`program_per_click_timestamp_conversions/sales/viewproduct/add_to_cart`, spend =
`cost * conversion_factor`). `MonetizeMerchantFacts` has NO overall
per-click-timestamp keys — only native `program_orders`/`program_revenue` and raw
`SUM(cost)` spend. So this single-table config cannot reproduce the baseline's
program funnel. Two paths:
1. **Match legacy exactly** — author a two-CTE query (cvcpf per-click-timestamp
   program + mmf site, FULL OUTER JOIN on date), using
   `ClientVendorChannelPerformanceFacts` for the program metrics. Faithful, but
   partly hand-written SQL (not purely single-class).
2. **Adopt the class standard** — accept `MonetizeMerchantFacts`' native
   `program_orders`/`program_revenue` as the new definition of attributed
   orders/GMV. Purely class-based, single table — but the numbers WILL differ from
   the legacy per-click-timestamp tool (the legacy attribution is retired).

Also still to confirm via the diff: whether `mmf` program-side `SUM(cost)` (no
conversion) equals cvcpf's converted spend (i.e. is `mmf.cost` already in
marketplace currency).

## Baseline query (run in BigQuery to get the diff target)

The exact aggregates the Python `check_gmv_attribution` computes (single period,
all programs) — run for agency 105, 2026-07-19→21, paste the row to complete the
diff. Source: `weekly_analysis_agent/tools/roi_analysis_tools.py` `_overall()`.
(Program = cvcpf per-click-timestamp; site = mmf converted.) See the message thread
for the parameterized SQL.

## Validation workflow (per config)

1. `kam-writer-mcp` → `analyze_query_for_schema` on the flattened query to confirm
   the referenced classes/columns resolve (and none must be created).
2. Post to the **test** env: `run_kam_report` posts/uses configs, or
   `scripts/post_kam_report_config.py -f <file> -e test`.
3. `run_kam_report` (or `POST /api/report/fetch`) with a known agency + current &
   baseline dates; check the row.
4. Diff the raw aggregates against the current Python `check_gmv_attribution` output
   for the same agency/dates. Reconcile currency/grain before marking validated.

## Deploy path
Configs live here while we iterate; they are posted to KAM (MongoDB) per environment
via `kamService/scripts/post_kam_report_config.py` (or the writer MCP). They only
become fetchable once posted. No `kamService` class changes are needed for the ROAS
configs that reuse `MonetizeMerchantFacts` — only new tables/metrics would require a
new class + `schemaRegistry` registration.
