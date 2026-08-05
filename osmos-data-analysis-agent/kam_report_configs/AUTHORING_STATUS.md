# Config-only authoring pass — status

## ✅ (2026-07-27) Consolidation validated on the test env — 15 merged reports live

The 15 consolidated reports are posted, fetch real data, and the 39 superseded
reportTypes are de-listed. Catalogue **137 → 111 unique** (+13 ours, −39 retired; 13 not
15 because `DISPLAY_AD_UNIT` and `GMV_ATTRIBUTION` merged in place). Full map:
`MERGE_MAP.md`. Rationale: `MERGE_ANALYSIS.md`.

| Report | Rows (agency 105, 2026-07-19→21) |
|---|---|
| MERCHANT_PERFORMANCE | 2,508 — replaces 5 reports; spend/ctr/cpc/roas/site funnel in ONE fetch |
| SKU_PERFORMANCE | 612 (scoped os_client_id 277661) |
| CATEGORY_PERFORMANCE | 33 (l1) · 55,377 (l1 × merchant_id) |
| RR_PLA / RR_DISPLAY | 5 / 10 page types |
| PAGE_PERFORMANCE_PLA | 5 · DISPLAY_AD_UNIT 40 |
| SEARCH_QUERY_REQUESTS_PLA | 1 (13,315 requests, 22.6% RR) |
| KEYWORD_PERFORMANCE / SEARCH_QUERY_PERFORMANCE | 5 / 1 |
| CAMPAIGN_PERFORMANCE | 1 · GMV_ATTRIBUTION 1 (ungrouped) |
| CAMPAIGN_KEYWORDS / CAMPAIGN_NETWORKS | 0 — predecessors also 0 for the same scope |
| AUDIT_EVENTS | ✅ working since 2026-08-04 — see below |

**Coverage vs the 42 predecessors:** 35 PASS · 4 PASS\* · 3 BLOCKED · **0 FAIL**. Each
predecessor's exact `externalColumnName` set was requested from its replacement.

**Numeric diff: ALL 39 runnable pairs IDENTICAL — 0 differing, 3 blocked.**
(`scripts/numeric_diff.py` = merchant + keyword, 8 pairs; `scripts/numeric_diff_all.py` =
the remaining 31.) Every predecessor was fetched at its own native grain and compared
row-by-row against its replacement, keyed by the grain tuple so a lost row and a gained
row cannot cancel out in a matching total. **Zero rows lost, zero gained, zero per-row
drift anywhere.**

| Family | pairs | largest comparison |
|---|---|---|
| MERCHANT_PERFORMANCE | 5 | 2,688 rows × 11 metrics |
| RR_DISPLAY | 6 | 3,973 rows × 3 |
| RR_PLA | 3 | **17,645** rows × 3 · STORE_LEVEL_RR at native day×hour grain |
| CATEGORY_PERFORMANCE | 2 | **186,238** rows × 6 |
| SKU_PERFORMANCE | 3 | 612 rows × 12 |
| CAMPAIGN_NETWORKS | 2 | 2,114 rows |
| PAGE_PERFORMANCE_PLA · DISPLAY_AD_UNIT · SEARCH_QUERY_* · CAMPAIGN_* · GMV · KEYWORD | 18 | — |

Spend reconciles to the cent (ZAR 3,326,249.54), program GMV 23,928,642.17, site revenue
173,733,404.53, PLA requests 25,576,711.

**This also verifies the migration instructions, not just the arithmetic.** Every pair whose
predecessor had a hardcoded guard was run with exactly the filter `MERGE_MAP.md` tells
callers to pass — `page_type NOT IN ('','NA')`, `category_l1 != ''`,
`campaign_type IN ('PERFORMANCE','INVENTORY','OFFSITE')`, `is_negative`,
`campaign_type='performance'` + `campaign_subtype IN (...)` — and reproduced the original
row set. Likewise the two renamed columns: `category_l*_raw` reproduces
MERCHANT_CATEGORY_CPC exactly (while `category_l*` keeps CATEGORY_LEVEL's `'Unknown'`/`'-'`
normalisation), and `internal_campaign_id` reproduces CAMPAIGN_NETWORKS_BY_ID exactly.

Mechanics: predecessors are de-listed from the catalogue but still fetchable by internal
reportType with `useExternalNames:false`. `limit` caps at 100,000, so the heavy grains
page — truncation would have produced a bogus mismatch. One pair
(`RR_BY_DIMENSION_PLA`) hit a `ChunkedEncodingError` — a connection dropped mid-body on a
multi-MB chunked response, not a data or SQL failure — and passed on a clean retry.

**Still not proven by this exercise:**
- `is_negative` on `CAMPAIGN_KEYWORDS` — 0 rows on both sides for every campaign tried, so
  the discriminator the keywords merge depends on is untested.
- `attributed_sales` — 0.00 across every keyword row.
- The 3 audit pairs — `audit.audit_logs_v2` unreachable.
- One agency, one 3-day window. Strong evidence of SQL equivalence, not proof across all
  tenants. The `base.merchant_id IS NOT NULL` guard in MERCHANT_PERFORMANCE is inert
  *here* because agency 105 has no null merchant_ids; a tenant with unmapped merchants
  could still see rows drop.

## Full-estate verification (2026-07-28) — all 41 active configs

The 15 merged reports are covered above. The other **26 non-consolidated configs** were
re-verified in one sweep (`scripts/verify_remaining.py`, log + JSON in `scripts/out/`),
each fetched requesting **every exposed column** — which proves each column resolves
through the catalogue *and* compiles in BigQuery. Earlier wave validation clearly never
did that, which is why this surfaced a defect nobody had hit.

**Result: 20 OK · 2 EMPTY · 4 ERROR.**

`EMPTY` = HTTP 200, 0 rows for the tested scope; the config is sound, the data just is not
there (`PROBLEM_METRICS` — trend table unpopulated for this week; `SEARCH_QUERY_MATCH` —
no rows for the test advertiser).

Notable passes: `WALLET_BALANCE` 42,068 rows · `MINUTE_CPM` 192,280 · `TRUE_BU` 7,745 ·
`MARKETPLACE_DIRECTORY` 64 (cross-tenant) · `MINUTE_CPC` 953 · `MERCHANT_CATEGORY` 296.

### 🔧 The 4 errors — triaged, to be handled separately

Four distinct root causes. Two are genuinely blocked; two are ours to fix and are narrower
than the raw error suggests.

| Config | Error | Root cause | Fix |
|---|---|---|---|
| `CATEGORY_REQUEST_VOLUME` | `Access Denied: reporting_belgium.os_product_ads_request_report` | **KAM's BQ service account lacks IAM** on the region request-log datasets (ledger PR2-B) | infra grant — not a config change |
| `FILTER_PRESENCE_RR` | `report type 'FILTER_PRESENCE_RR_REPORT' is not configured yet` | **never posted to Mongo** — the only one of 41 missing. Config exists on disk | post it; it will then hit the same grant wall as above |
| `DAILY_ORDER_TRENDS` | `Unrecognized name: cvcpf at [1:42]` | **broken column, not a broken report.** The `channel` attribute's selector is `cvcpf.channel`, but the template selects from `(…) AS p FULL OUTER JOIN (…) AS s` — `cvcpf` is only bound inside the inner subquery. **Verified: without `channel` the report returns 3 rows of correct data.** This is §5 bug 1 of MERGE_ANALYSIS, now reproduced live | drop `channel`, or move it into the inner subquery's GROUP BY (watch for site-metric fan-out) |
| `RESPONDED_SKUS` | `ReadTimeout` (both full and reduced grain) | **not broken — unscoped scan too heavy.** No `externalRequiredFilters` declared, so an unscoped fetch reads the whole response-to-impressions mapping. **Verified: scoped to `keyword=iphone` it returns 18 rows of correct product data** | declare `externalRequiredFilters: ["keyword"]` so callers cannot attempt it unscoped |

Neither of the two fixable ones is a consolidation regression — `DAILY_ORDER_TRENDS` and
`RESPONDED_SKUS` were both left out of the merge deliberately.

### ⚠️ Read before touching these configs again

1. **`visibility`: disk and Mongo intentionally differ.** All configs on disk say
   `INTERNAL_PERFORMANCE`; the test env was posted as **`INTERNAL_USER`** via the new
   `post_external.py --visibility` flag. `INTERNAL_PERFORMANCE` is NOT in
   `commonValidators.js:9 VALID_VISIBILITY_VALUES` — every POST 400s until the enum ships.
   Reconcile with `repost_internal_performance.sh` once it lands.
2. **`GET /report/config` returns a UI projection, not a storable document.**
   `attributes` comes back as `[{label, value}]`, not the selector map. **Never post back
   what you read** — it would replace a config's real attributes with a label list. Joi's
   `"attributes" must be of type object` is the only thing that caught this (39 rejected
   writes, zero damage). Use a **minimal body** for field-level updates:
   `{application, id, cacheInfo, <field>: null}` — `buildUpdateQuery` only `$set`s fields
   present in the body. `restore_snapshot.py --configs` was corrected the same way and now
   restores only `externalReportType`.
3. **Three external names were renamed** — the originals are owned by live BEATS/PULSE
   reports. `KEYWORD_PERFORMANCE_REPORT` → `INTERNAL_KEYWORD_PERFORMANCE_REPORT`;
   `CAMPAIGN_PERFORMANCE_REPORT` → `INTERNAL_CAMPAIGN_PERFORMANCE_REPORT`;
   `SEARCH_QUERY_PERFORMANCE_REPORT` → `INTERNAL_SEARCH_QUERY_PERF_REPORT` (the obvious
   `INTERNAL_SEARCH_QUERY_PERFORMANCE_REPORT` was held by the predecessor it retires).
   Posting under a taken name does not overwrite — it creates a **duplicate catalogue
   entry**, which resolves ambiguously. Two such duplicates already exist in the test
   catalogue (`TARGETING_LEVEL_PERFORMANCE_REPORT`,
   `OSMOSX_MCC_BEAT_REPORTING_SEARCH_TERM_PERFORMANCE`) — both other teams', pre-existing.
4. **`AUDIT_EVENTS` — RESOLVED 2026-08-04, no longer blocked.** It previously named
   appKey `GCP_BQ_KAM_CREDENTIALS_EXTERNAL_DATASET` (unregistered) and its predecessor
   used `KAM_EXPORT_GCP_BQ_CREDENTIALS` (registered but lacking IAM on
   `audit.audit_logs_v2`). Both are fixed: all 43 configs now use
   `GCP_PERF_BQ_KAM_CREDENTIALS`, which is registered and has the grants, and
   `action_type_id` gained a `SAFE_CAST(... AS STRING)`.
   **Verified working** — agency 576 returns audit rows for 2026-07-16..19 and
   2026-07-30..31; agency 105 returns 13,630 rows unfiltered. Use it; do not
   report the audit family as unavailable.
5. **`store_id` was dropped from `RR_DISPLAY`.**
   `os_display_ads_filtered_level_performance_facts` has no such column; requesting it
   500s identically on the retired report. The other 9 attributes were each probed and
   work. `store_id` remains on `RR_PLA`, where the column exists.
6. **Not proven:** the `is_negative` discriminator on `CAMPAIGN_KEYWORDS`. Both test
   campaigns have no keywords, and an unscoped probe exceeds the query budget.

### Safety verification (the columnMetadata clobber did NOT recur)

- **87 columns checked before and after every write: 57 grew, 0 shrank, 0 vanished.**
- **96 non-ours catalogue reports: attribute/metric key sets byte-identical to baseline.**
  This is the check that would have caught the original incident — that clobber did not
  remove reports, it silently emptied their columns.
- `sync_column_metadata.py` hardened: `prod_tags()` / `current_tags()` now **raise**
  instead of returning `{}`, and `_retired/` is excluded. Returning `{}` silently dropped
  an input from the three-way union, turning the protective merge into the clobber.
- Snapshot + rollback: `scripts/out/snapshot_20260727_182900/`, restore via
  `scripts/restore_snapshot.py`.

New tooling: `scripts/snapshot_kam.py`, `restore_snapshot.py`, `assert_no_tag_shrink.py`,
`verify_coverage_live.py`, `delist_retired.py`, `final_catalogue_diff.py`.


> **Note:** the reportTypes named throughout this file predate the consolidation pass.
> 42 of them were merged into 15 reports; map any name here to its replacement via
> `MERGE_MAP.md`. The validation findings, engine learnings and the columnMetadata
> clobber post-mortem below all still apply — and matter more now, since the merged
> reports carry unioned `filterTags` and must be re-synced with `sync_column_metadata.py`.

Authored the config-only queue (ledger §2) via `.claude/kam-config-authoring-prompt.md`,
one agent per tool, then validated each against the KAM **test** env (agency 105,
2026-07-19→21). No kamService changes were made. **All 12 authored configs validated
green.**

## Result per tool (11 tools from ledger §2)

| Tool | reportType(s) | File(s) | Status | Test |
|---|---|---|---|---|
| get_page_level_performance | KAM_AGENT_PAGE_LEVEL_PERFORMANCE | shared/ | authored | ✅ green (cost caveat) |
| check_response_rate_by_page | KAM_AGENT_RR_BY_PAGE_PLA, _DISPLAY | rr/ | authored (split) | ✅ green |
| check_display_page_type_rr | KAM_AGENT_RR_DISPLAY_PAGE_TYPE | rr/ | authored (patched) | ✅ green |
| get_category_response_rates | KAM_AGENT_RR_CATEGORY | rr/ | authored | ✅ green |
| get_response_rate_by_dimension | KAM_AGENT_RR_BY_DIMENSION_PLA, _DISPLAY | rr/ | authored (split) | ✅ green |
| check_requests | KAM_AGENT_BU_REQUESTS_PLA, _DISPLAY | bu/ | authored (split) | ✅ green |
| get_display_ad_unit_performance | KAM_AGENT_BU_DISPLAY_AD_UNIT | bu/ | authored (patched) | ✅ green (cost/sales caveat) |
| get_merchant_wallet_balance | KAM_AGENT_BU_WALLET_BALANCE | bu/ | authored (rewritten) | ✅ green |
| get_budget_delivery_mode | KAM_AGENT_BUDGET_DELIVERY_MODE | budget_pacing/ | authored (patched) | ✅ green |
| check_targeted_keyword_performance_in_campaigns | — | — | **BLOCKED → needs-class** | — |
| get_targeted_keyword_competition | — | — | **BLOCKED → needs-class** | — |

**12 config files, all valid JSON, all fetch real agency-105 data.**

## Fixes applied during validation
- `RR_DISPLAY_PAGE_TYPE`, `BU_DISPLAY_AD_UNIT`: table has no `agency_id` → switched to
  `JOIN marketplace_clients ON marketplace_client_id → mc.agency_id` (1:1 with agency).
- `BU_WALLET_BALANCE`: **rewritten** — ledger was wrong (`clients_remaining_budget_amount_usd`
  is a raw-USD *attribute*, not a converted metric; ClientsMetrics has only `placeholder_metric`).
  Now returns raw USD balance + `conversion_factor` (StaticCurrencyConversion attr) and the
  Python layer does `balance*factor` with the `>=0.01` floor. Real keys: `clients_client_id`,
  `clients_seller_id`, `clients_alias`; alias `clients` (not `c`).
- `BUDGET_DELIVERY_MODE`: empty `metricsClasses` is rejected by the config validator AND the
  fetch API requires ≥1 metric → set `metricsClasses:["Clients"]` and request the
  `placeholder_metric` (`0`); confirmed real STANDARD/ACCELERATED values return.

## Engine learnings (for report_map.py / MCP wiring)
- Pure-dimension reports still need ≥1 requested metric at fetch → use the `Clients`
  `placeholder_metric` and drop it in Python.
- Fetch filters use `{"key", "operator", "values"}` (not `attribute`).
- Point-in-time reports: template has no `__START_DATE_1__`; dates in the request are inert.

## Remaining caveat to close (numeric, not structural)
- **`PAGE_LEVEL_PERFORMANCE` cost** — uses unconverted `SUM(cost)`. Agency 105 is non-USD
  (conversion_factor ≈ 15.74), so if that table's `cost` is really USD the figure is ~15×
  off. Needs a numeric diff vs legacy `SUM(cost_usd*scc.conversion_factor)`. If it diverges,
  flip to needs-class (converted-spend metric on OsProductAdsPageNamePerformanceFacts).
  Same converted-spend theme as BU_DISPLAY_AD_UNIT cost/sales.

## Ledger corrections (found while authoring — update CLASS_CHANGE_LEDGER.md)
The ledger's §2 "config-only" classification is wrong for these; reclassify to
**needs-class**, all blocked by the same "converted vs unconverted spend" gap:
- **get_targeted_keyword_competition** — needs converted `spend`/`attributed_sales`
  metrics + `seller_id` on `OsAdsKeywordPerformanceReport`.
- **check_targeted_keyword_performance_in_campaigns** — needs converted
  `spend`/`attributed_sales` **and** `client_id` + `marketing_campaign_id` attributes on
  `OsAdsKeywordPerformanceReport` (the latter derived via campaign_tagging_data →
  marketing_campaign_dimensions; not on the keyword report).
- **get_display_ad_unit_performance** — raw aggregates are config-only, but `cost` and
  `sales` need converted variants on `OsDisplayAdsAdUnitFactsMetricsClass`
  (`SUM(cost*conversion_factor)`). Draft config returns USD-basis cost/sales meanwhile.

This converted-spend theme is the same one tracked in ledger §PR1 (cvcpf). A single
"add converted-spend/sales metric" pattern across `OsAdsKeywordPerformanceReport`,
`OsDisplayAdsAdUnitFacts` (and the cvcpf work) would unblock this whole cluster.

## Intake reports (session bootstrap — authored INLINE / Gen1)

The two reports the CLAUDE.md intake protocol needs. **Neither is config-only** (class
gaps below), so both were authored as **inline (Gen1) configs** — selectors written
directly in the config, no schema class. This also empirically settled two open questions.

| Report | File | Backs | Status |
|---|---|---|---|
| `KAM_AGENT_MARKETPLACE_DIRECTORY` | shared/ | `fetch_marketplace_info` | ✅ validated — 64 rows |
| `KAM_AGENT_PROBLEM_METRICS` | shared/ | `get_problem_metrics` | ⚠️ structurally validated; 0 rows (trend table appears unpopulated in test) |

**Findings proven against the test env:**
- **Inline (Gen1) configs WORK** — a config with inline `attributes`/`metrics` (no
  `attributesClasses`/`metricsClasses`) posts without rejection and resolves/fetches
  correctly. So the no-class path is viable for **direct `/report/fetch`**. (External-
  catalogue exposure of inline columns via `externalColumnName` is still unverified.)
- **Cross-tenant fetch WORKS** — a report whose template omits `__AGENCY_ID__` returns
  all-tenant rows; a dummy `agencyId` in the request is fine. This is how the marketplace
  directory (which has no agency yet) is served.
- Both still need the `placeholder_metric` (`0`) trick — the fetch API requires ≥1 metric.

**Why not config-only:**
- `fetch_marketplace_info`: `Agencies` class lacks `region` & `marketplace_type`;
  `MarketplaceClients` lacks `timezone`. Inline supplies them directly.
- `get_problem_metrics`: no schema class exists for
  `os_ads_performance_trend_analysis_report`; it's a row-level passthrough.

**Useful fact discovered:** agency **105 = "takealot-marketplace"**, marketplace_client_id
**100002**, currency **ZAR**, tz **Africa/Johannesburg**. To get real PROBLEM_METRICS rows,
filter `marketplace_client_id=100002` on a week the trend report actually populated.

## ✅ Chosen architecture PROVEN end-to-end (inline + external + reporting-mcp)

Decision locked: **inline (Gen1) configs + external report system + the existing
`osmos-reporting-mcp-release`** (no bespoke `osmos-performance-mcp`). Proven on one query
(`get_page_level_performance` → `shared/INTERNAL_PERF_PAGE_LEVEL.json`), agency 105:

1. `columnMetadata` POST (6 cols) → 200
2. inline config POST (INTERNAL_USER visibility, no schema classes) → OK
3. `GET /report/config/external` → our `PAGE_LEVEL_PERFORMANCE_REPORT` is in the catalogue
   (73 reports) with its external column names
4. `POST /report/fetch` `useExternalNames:true` → 5 real rows under external names, **spend
   currency-converted to ZAR** — this is exactly what reporting-mcp's `run_report` calls.

**Open questions this settled:**
- Inline configs CAN be exposed via the external catalogue (`externalColumnName` +
  `columnMetadata` + intersecting `filterTags`) — the last risk in the inline path.
- Converted spend inline (`cost_usd * scc.conversion_factor`) works with **no class** →
  the converted-spend "needs-class" blocker is gone for inline configs.
- Field facts: translation keys on **`externalColumnName`**; valid `visibility` values are
  `BEATS/PULSE/AGENT/INTERNAL_USER/LOCALIUM_BEATS/OSMOSX_BEATS`; `INTERNAL_USER` is served
  by the existing `/osmosReportingMcp/beatsInternal` mount (no new mount required).
- Bonus: converted spend (33,183.56) == earlier class `SUM(cost)` (33,183.57) → this
  table's `cost` is already marketplace-currency; **PAGE_LEVEL cost caveat resolved.**

**Reusable workflow driver:** `post_external.py` (derives columnMetadata from the config's
`externalColumnName` columns, posts config, checks the catalogue, fetches via
`useExternalNames`). Run: `python post_external.py --config <cfg> --agency N --current S E`.

**Remaining for a live MCP tool call** (infra, not config): caller Hades scope ≥
`INTERNAL_USER` on the `beatsInternal` mount + catalogue TTL refresh (300s). The KAM data
path is done.

## Inline+external batch #1 (via `.claude/kam-inline-external-authoring-prompt.md`)

Three reports authored the chosen way (inline + external, `INTERNAL_USER`) and validated
green end-to-end (columnMetadata → config → catalogue → `useExternalNames` fetch), agency 105:

| Tool | external reportType | tags | Result |
|---|---|---|---|
| check_program_spend | PROGRAM_SPEND_REPORT | bu | ✅ ungrouped; converted cvcpf spend inline |
| get_merchant_ctr_breakdown | MERCHANT_CTR_BREAKDOWN_REPORT | merchant_breakdown, ctr | ✅ 2688 rows; converted spend + CTR/CPC/CPM inline |
| get_category_response_rates | CATEGORY_RESPONSE_RATES_REPORT | category, rr | ✅ 3703 rows; response_rate inline; no currency |

**Blocker officially busted:** `check_program_spend` and `get_merchant_ctr_breakdown` were
both **PR1-cvcpf "needs-class"** (converted spend). They now work **config-only inline, no
kamService PR**. And `PROGRAM_SPEND` reconciles numerically — converted spend
**ZAR 3,326,249.54 == the `mmf.cost` spend** from CTR_OVERALL on the same agency/window.

**Refinement noted (not blocking):** inline templates skipped the legacy `impressions > 0`
HAVING gate (left to caller). The engine does expose `__ADVANCED_FILTERS_HAVING__`, so a
HAVING can be added later if we want the report to self-filter zero rows.

## ⚠️→✅ columnMetadata global-clobber bug — found, fixed, remediated

**Bug:** columnMetadata is keyed globally by `columnName`; a POST REPLACES its `filterTags`
(`columnMetadataServiceHelper.prepareUpsertQuery`). A column is usable by a report only if
its columnMetadata tags INTERSECT the report tags (`externalNameTranslatorHelper`). Our
per-report posts reused canonical names (`spend`, `clicks`, …) and **overwrote 16 shared
columns' production tags** in the test env (e.g. `clicks`/`spend` lost `scope:localium_beats`)
— breaking the team's BEATS/PULSE/LOCALIUM reports there, and making our own "green"
validations non-durable (last-post-wins).

**Fix (applied):**
- `sync_column_metadata.py` — MERGE-based sync: for every column any of our configs exposes,
  post `union(production-file tags, current test-env tags, all our report tags)`. Restored
  all 16 clobbered production columns AND unified our tags. Verified (`clicks`/`spend`/`channel`
  now carry production + all our `report_group:*` tags).
- `post_external.py` — patched to MERGE (never replace) for single-report posting.
- Re-validated 8 reports **simultaneously green** (CTR_OVERALL, PROGRAM_SPEND, MERCHANT_ROAS/CTR,
  CATEGORY_RR, PAGE_LEVEL, CAMPAIGN_SUBTYPE_CPC, TARGET_ROI) — no "attribute not configured".
- De-listed the stray `TMP_CLIENTS_105_REPORT` (a runaway subagent created it; no delete
  endpoint, so overwritten inert → removed from catalogue). Two pre-existing `TMP_*_OLD`
  reports are not ours — left untouched.
- Prompt hardened: gotcha #12 (columnMetadata global/merge) + guardrail (no throwaway reports;
  reuse os_client_id 277661 for scoped validation).

**Security note:** the runaway SKU_ROAS subagent modified shared test-env resources
autonomously (temp report + columnMetadata toggling) — process failure; subagents should not
post to shared envs unsupervised. Data accessed was our own test-env data (in project scope).

## SP tokens CONFIRMED (unblocks region/timezone tools)
`__SP_TIMEZONE__` resolved to `'Africa/Johannesburg'` for agency 105 (KEYWORD_SELLER test).
`__SP_REPORTING_DB_REGION__` → `_<region>`. So timezone-aware and region-specific tools are
inline-expressible — NOT blockers. Use `DATE(TIMESTAMP(col,'UTC'),'__SP_TIMEZONE__')` and
`reporting__SP_REPORTING_DB_REGION__.table`.

## Wave 3 (CTR) — 4/4 authored (validate after the columnMetadata fix, done)
- ✅ check_ctr_overall → CTR_OVERALL_REPORT (re-authored inline; matches class version)
- ✅ get_sku_level_ctr_performance → SKU_CTR_PERFORMANCE_REPORT (`externalRequiredFilters:[os_client_id]`)
- ✅ get_keyword_seller_breakdown → KEYWORD_SELLER_BREAKDOWN_REPORT (SP-timezone; scoped fetch only)
- (held) get_search_query_match_performance → later search-query wave

## Not yet done (bookkeeping, when configs are validated)
- Add each validated reportType + metric_key_map to
  `osmos-performance-mcp/src/osmos_performance_mcp/report_map.py`.
- Reconcile the ROAS drift: `report_map.py` expects `KAM_AGENT_ROAS_PROGRAM_FUNNEL`
  + `KAM_AGENT_ROAS_SITE_FUNNEL`, but only `KAM_AGENT_ROAS_GMV_ATTRIBUTION.json` exists.
