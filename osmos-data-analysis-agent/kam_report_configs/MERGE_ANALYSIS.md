# KAM report-config consolidation — what, why, how

Analysis of the `query_inventory/*.sql` → `kam_report_configs/*.json` pipeline and the
redundancy it accumulated. **70 configs → 41 (−29, −41%): 42 configs retired into 15
merged reports.** Per-report migration notes are in `MERGE_MAP.md`; the retired configs
are in `_retired/`.

---

## 1. WHAT — the flow, end to end

```
legacy ADK agent (weekly_analysis_agent/tools/*.py)
    │  76 hand-written BigQuery strings embedded in Python tool functions
    ▼
query_inventory/<skill>/<tool>.sql          ← extraction: one .sql per tool call-site
    │  (77 files: 76 queries + 1 shared fragment; INDEX.md is the catalogue)
    ▼
kam_report_configs/<skill>/INTERNAL_PERF_*.json   ← 70 KAM report configs
    │  inline (Gen1) configs: attributes{} + metrics{} + a parameterised query template
    ▼  POST → KAM (Mongo) per env, exposed in the external catalogue
KAM  /api/report/fetch   →  BigQuery
    ▼
osmos-reporting-mcp  run_report  →  MCP tool
    ▼
.claude/skills/debug-*  (the 10 metric SOPs)  →  the agent
```

The agent never writes SQL. A skill names a report, the MCP calls KAM, KAM substitutes
the template and runs it against BigQuery. Derived analysis (deltas, contribution %,
Pareto, verdicts) stays in the Python/agent layer.

## 2. WHY the redundancy exists

The extraction was **1 SQL string → 1 .sql file → 1 KAM report**, and the extraction unit
was *the Python call-site*, not *the dataset*. Three multipliers followed:

| Multiplier | Effect | Example |
|---|---|---|
| **One report per skill** | The same fact table got re-authored once per metric SOP | `MERCHANT_BU`, `MERCHANT_RR`, `MERCHANT_CTR`, `MERCHANT_CPC`, `MERCHANT_ROAS` — all `client_vendor_channel_performance_facts` at merchant grain |
| **One report per grain** | A different `GROUP BY` in the legacy Python became a whole new report | `RR_HOURLY`, `RR_HOURLY_AD_UNIT`, `RR_DISPLAY_PAGE_TYPE`, `RR_BY_DIMENSION_DISPLAY` — one table, four groupings |
| **`split=` per branch** (WAVE_PLAN convention) | A Python `if program_type == 'PLA'` became two reports | `RR_BY_PAGE_PLA` / `_DISPLAY`, `BU_REQUESTS_PLA` / `_DISPLAY` |

None of this was wrong at authoring time — it was the safe, mechanical way to port 76
queries. But it produced configs that are **byte-identical apart from `reportType`,
`filterTags` and `description`**. `INTERNAL_PERF_MERCHANT_BU` and
`INTERNAL_PERF_MERCHANT_RR` have the same template, the same four attributes and the same
three metrics. They are the same report twice.

### The cost of not merging
- **Column-metadata blast radius.** `columnMetadata` is keyed *globally* by `columnName`;
  every extra report that exposes `spend`/`clicks` is another writer to a shared row.
  This already caused a production-tag clobber incident (see `AUTHORING_STATUS.md`).
- **N× validation.** Every config needs its own post → catalogue → fetch → numeric diff.
- **Catalogue noise.** The external catalogue is what the MCP advertises to the agent;
  six near-identical RR reports make tool selection harder, not easier.
- **Drift.** A currency-conversion or attribution fix has to be applied 5 times.

## 3. HOW merging is possible — the enabling mechanism

Verified in `kamService/src/servicehelpers/fetchReportDataServiceHelper.js`:

- `createAttributeSelectors(attributes, configAttributes)` builds **both**
  `__ATTRIBUTES__` and `__ATTRIBUTES_GROUP_BY__` from *the attributes the caller
  requested*, not from everything the config declares (`:163-166`).
- `createMetricsSelectors(metrics, configMetrics)` does the same for `__METRICS__`
  (`:168-177`).

**So one config already serves every grain and every metric subset its template can
express.** A config declaring 10 attributes is not a 10-column report — it is a menu. That
is exactly why five merchant reports can be one.

### What blocks a naive merge, and the resolution

The only real differences between family members are **hardcoded `WHERE` guards**:

```sql
AND r.page_type IS NOT NULL AND TRIM(r.page_type) NOT IN ('', 'NA')
AND r.filter_keywords IS NOT NULL AND TRIM(r.filter_keywords) != ''
AND LOWER(mcgd.campaign_subtype) IN ('os_ads_search', 'smart_shopping')
AND k.is_negative = 1
```

`createFilterClauses` (`:432`) supports `= != < <= > >= IN "NOT IN" LIKE "NOT LIKE" LIKES
"STARTS WITH" "ENDS WITH"`. **There is no `IS NULL` / `IS NOT NULL` operator** — so the
guards cannot be moved verbatim into caller filters. Resolution, applied per merge:

1. **Fold the `TRIM` into the attribute selector** (`LOWER(TRIM(r.filter_keywords))`).
   The stored value is then trimmed, and `NOT IN ('')` becomes exactly equivalent to the
   original guard — SQL `NULL NOT IN ('')` evaluates to `NULL`, so NULLs are excluded too.
2. **Promote the discriminator to an attribute** (`is_negative`, `campaign_type`,
   `campaign_subtype`) so the caller filters it with `=` / `IN`.
3. **Keep a guard hardcoded only when every member shares it** (e.g. `page_type NOT IN
   ('','NA')` on the PLA page-name family — all three members have it).

Where a guard is dropped, the merged report is a **superset**: the caller must send the
filter to reproduce the old row set. This is recorded per report in `MERGE_MAP.md`.

### Two facts that make this cheap
- `externalRequiredFilters` is **advisory** — it is stored and echoed into the external
  catalogue (`externalConfigServiceHelper.js:40`) but never enforced at fetch. Merging
  members with different required filters does not break anything; the recommended
  scoping moves into the description and the MCP layer.
- Requesting zero attributes is supported (`__ATTRIBUTES__` collapses, `, __METRICS__`
  handling at `:172-176`), so a grouped report can still serve the ungrouped total.

---

### One hard constraint discovered while executing

`createAttributeSelectors` produces an empty string when the caller requests no
attributes, and **nothing in the engine strips a now-dangling `GROUP BY`** — the emitted
SQL would be `SELECT , … GROUP BY ;`. So **a grouped template cannot serve an ungrouped
caller.** Consequences:

- A report whose template has no `GROUP BY` (`GMV_ATTRIBUTION`, `FILTER_PRESENCE_RR`, the
  audit passthroughs) can only merge with another ungrouped report.
- This is what killed the planned `CATEGORY_REQUEST_VOLUME` + `FILTER_PRESENCE_RR` merge:
  the former is grouped, the latter is a single-row marketplace-wide scan. Merging them
  would force the filter-presence caller to group and then re-sum 34 metrics in Python.

## 4. The merge plan — 15 families, 70 → 41

Grouped by wave. "Δ" is configs removed.

### Wave 1 — shared fact table, pure grain duplication (−13)

| # | Merged report | Absorbs | Δ | Note |
|---|---|---|---|---|
| M3 | `INTERNAL_PERF_RR_DISPLAY` | `RR_BY_DIMENSION_DISPLAY`, `RR_DISPLAY_PAGE_TYPE`, `RR_HOURLY`, `RR_HOURLY_AD_UNIT`, `SEARCH_QUERY_RR_DISPLAY`, `SEARCH_QUERY_RR_DISPLAY_AD_UNIT` | −5 | identical template; add `hour` + `keyword` attrs |
| M4 | `INTERNAL_PERF_RR_PLA` | `RR_BY_DIMENSION_PLA`, `CATEGORY_RR`, `STORE_LEVEL_RR` | −2 | add `day`, `hour`, `category` (concat) attrs |
| M5 | `INTERNAL_PERF_SEARCH_QUERY_REQUESTS_PLA` | `SEARCH_QUERY_RR_PLA`, `SEARCH_QUERY_RR_BUCKETS`, `KW_REQUEST_VOLUME` | −2 | identical SP-timezone template; union of 4 metrics |
| M7 | `INTERNAL_PERF_PAGE_PERFORMANCE_PLA` | `PAGE_LEVEL`, `RR_BY_PAGE_PLA`, `BU_REQUESTS_PLA` | −2 | add `date` attr + `response_rate` metric |
| M8 | `INTERNAL_PERF_DISPLAY_AD_UNIT` | `DISPLAY_AD_UNIT`, `RR_BY_PAGE_DISPLAY`, `BU_REQUESTS_DISPLAY` | −2 | add `date` attr + `response_rate` metric |

### Wave 2 — cvcpf / SKU / funnel (−8)

| # | Merged report | Absorbs | Δ | Note |
|---|---|---|---|---|
| M1 | `INTERNAL_PERF_MERCHANT_PERFORMANCE` | `MERCHANT_BU`, `MERCHANT_RR`, `MERCHANT_CTR`, `MERCHANT_CPC`, `MERCHANT_ROAS` | −4 | `MERCHANT_BU` ≡ `MERCHANT_RR` byte-for-byte; use the ROAS two-CTE shape (site `LEFT JOIN`) as the base |
| M2 | `INTERNAL_PERF_SKU_PERFORMANCE` | `SKU_ROAS`, `SKU_CPC`, `SKU_CTR` | −2 | `SKU_ROAS` ≡ `SKU_CPC` byte-for-byte |
| M6 | `INTERNAL_PERF_GMV_ATTRIBUTION` | `PROGRAM_SPEND` | −1 | `PROGRAM_SPEND` is a strict 1-metric subset |
| M15 | `INTERNAL_PERF_CATEGORY_PERFORMANCE` | `CATEGORY_LEVEL`, `MERCHANT_CATEGORY_CPC` | −1 | same table + same WHERE; expose raw *and* normalised category |

### Wave 3 — keyword / search-query / campaign / audit (−11)

| # | Merged report | Absorbs | Δ | Note |
|---|---|---|---|---|
| M9 | `INTERNAL_PERF_KEYWORD_PERFORMANCE` | `KW_COMPETITION`, `KW_PERF_IN_CAMPAIGNS`, `MERCHANT_KEYWORD` | −2 | same base; promote `campaign_type`/`campaign_subtype` to attrs |
| M10 | `INTERNAL_PERF_SEARCH_QUERY_PERFORMANCE` | `SEARCH_QUERY_PERF`, `KEYWORD_SELLER` | −1 | the two SP-timezone siblings only — see below |
| M11 | `INTERNAL_PERF_CAMPAIGN_PERFORMANCE` | `CAMPAIGN_PERF_AGG`, `CAMPAIGN_PERF_DAILY` | −1 | identical but for `date` attr + a `campaign_type IN (…)` guard → caller filter |
| M12 | `INTERNAL_PERF_AUDIT_EVENTS` | `BUDGET_CHANGES`, `CAMPAIGN_STATUS_CHANGES`, `PRODUCT_SELECTION_CHANGES` | −2 | one `audit_logs_v2` passthrough; `action_type_id` becomes a required attr filter |
| M13 | `INTERNAL_PERF_CAMPAIGN_KEYWORDS` | `CAMPAIGN_KW_TARGETED`, `CAMPAIGN_KW_NEGATIVE` | −1 | differ only by `is_negative = 0/1` |
| M14 | `INTERNAL_PERF_CAMPAIGN_NETWORKS` | `CAMPAIGN_NETWORKS_BY_ID`, `CAMPAIGN_NETWORKS_VIA_CTD` | −1 | `INNER JOIN ctd` → `LEFT JOIN ctd`, expose both id forms |

**Not merged, deliberately:**

| Pair | Why kept apart |
|---|---|
| `SEARCH_QUERY_MATCH`, `SEARCH_QUERY_CAMPAIGNS` vs the M10 pair | All four read `os_ads_search_query_performance_report`, but the M10 pair filters dates with `DATE(TIMESTAMP(date,'UTC'), __SP_TIMEZONE__)` while these two use a plain `date BETWEEN`. Unifying them silently reinterprets the date window for two reports. `SEARCH_QUERY_CAMPAIGNS` additionally joins `campaign_tagging_data` on `campaign_id` alone (no `client_id`/`account_id`), so merging it would also change its fan-out. Both are worth fixing — as deliberate fixes, not as a side effect of a merge. |
| `CATEGORY_REQUEST_VOLUME` vs `FILTER_PRESENCE_RR` | Grouped vs ungrouped template; see the `GROUP BY` constraint above. |
| `DAILY_ORDER_TRENDS` vs `GMV_ATTRIBUTION` | different query shapes — `FULL OUTER JOIN` on date vs correlated scalar subqueries. Merging means rewriting the site funnel; real fan-out risk if `channel` joins the grain. |
| `CTR_OVERALL` vs `GMV_ATTRIBUTION` | different source table (`monetize_merchant_facts` vs `cvcpf`). Spend reconciles numerically but clicks/impressions attribution does not. |
| `MINUTE_CPC` vs `MINUTE_CPM` | different fact tables (`response_to_clicks_mapping` vs `response_to_impressions_mapping`). |
| `CAMPAIGN_DAILY_BUDGET_AVG` vs `_FLEXI` | different tables *and* mutually exclusive marketplace modes. |
| `SKU_*` vs `MERCHANT_CATEGORY` | share `os_product_ads_device_product_facts` but `MERCHANT_CATEGORY` aggregates at category×campaign with different metric names; folding it in would make the SKU report's `externalRequiredFilters` misleading. Revisit later. |

## 5. Bugs found during the analysis (not caused by merging)

1. **`DAILY_ORDER_TRENDS.channel` is unusable.** Its selector is `cvcpf.channel`, but
   `cvcpf` is not in scope in the outer query — the template selects from
   `(…) AS p FULL OUTER JOIN (…) AS s`. Requesting `channel` will fail to compile.
2. **`GMV_ATTRIBUTION.channel` / `PROGRAM_SPEND.channel` are filter-only.** Their template
   is `SELECT __METRICS__` with no `__ATTRIBUTES__` placeholder, so `channel` can be
   filtered on but never grouped by. Fine, but the description should say so.
3. **`CAMPAIGN_KW_TARGETED` has no `GROUP BY __ATTRIBUTES_GROUP_BY__`** while its sibling
   `CAMPAIGN_KW_NEGATIVE` does. The merge fixes this.
4. **`BU_REQUESTS_PLA` carries `AND pf.date >= '2022-07-11'`** — a hardcoded data-quality
   floor absent from its two siblings on the same table. Moot under
   `dataAvailabilityDays: 90`; dropped in the merge.
5. **`CAMPAIGN_NETWORKS_*` do not scope by tenant.** Neither retired config filtered on
   `__AGENCY_ID__` — `os_ads_db_campaign_targeting_mapping` has no agency column and they
   relied entirely on the caller's `campaign_id` filter. The merge preserved that
   behaviour rather than changing it silently; the merged report is allowlisted in
   `scripts/validate_merged.py` so the tenant-scoping check stays on for everything else.
   Worth fixing by joining `clients` on `ctm.client_id`.
6. **`PRODUCT_SELECTION_CHANGES.action` mislabelled non-product events.** Its selector was
   `CASE WHEN action_type_id = 50 THEN 'added' ELSE 'removed' END` — harmless while the
   report hardcoded `action_type_id IN (50,51)`, but wrong the moment the type is a caller
   filter. The merged `AUDIT_EVENTS` returns `NULL` outside 50/51.

## 6. What was executed

- `scripts/merge_lib.py` — shared builder. Each merged config is the **union** of its
  members' column definitions (first member wins, explicit overrides applied on top), so
  every column's provenance is traceable. The builder **fails** if a member column is not
  listed in the merged config, which is what guarantees nothing is silently dropped.
- `scripts/merge_wave1.py` / `merge_wave2.py` / `merge_wave3.py` — the 15 merge specs.
- `scripts/validate_merged.py` — per config: required fields present, tenant scoping,
  ≥1 metric, every selector's table alias actually bound by the template (the failure mode
  when a column is inherited from a member that used a different alias), column
  `filterTags` intersecting report `filterTags`, and full `(attributes, metrics)` coverage
  of every retired report. **15 configs, 0 problems.**
- `scripts/retire_merged.py` — moved 42 configs to `_retired/` and generated `MERGE_MAP.md`.

Re-running any wave script is idempotent; the merged output is regenerated from the specs.

## 7. Still to do

**Done 2026-07-27** — see the validation section at the top of `AUTHORING_STATUS.md`:
- ~~Repost the 15 merged reports on the test env~~ — 14/15 return real data, AUDIT_EVENTS
  blocked on BQ credentials.
- ~~De-list the retired reportTypes~~ — 39 de-listed; the 3 audit predecessors kept
  deliberately (their replacement is unverifiable, so removing them would leave a gap).
- ~~Run `sync_column_metadata.py`~~ — done and hardened; 57 columns grew, none shrank.

- ~~Numeric diff~~ — **ALL 39 runnable pairs IDENTICAL; 0 differing, 3 blocked.**
  (`scripts/numeric_diff.py` 8 pairs + `scripts/numeric_diff_all.py` 31; logs in
  `scripts/out/`.) Row-level, keyed by grain tuple, agency 105 / 2026-07-19→21. Zero rows
  lost, zero gained, zero per-row drift — including 186,238 rows for
  MERCHANT_CATEGORY_CPC and 17,645 for RR_BY_DIMENSION_PLA.

  Every hypothesised regression was disproven:

  | Feared change | Outcome |
  |---|---|
  | `base.merchant_id IS NOT NULL` guard added to BU/CTR/RR | inert — 2,688 rows both sides. **Latent, not permanently safe:** agency 105 has no null merchant_ids |
  | `LEFT JOIN mcgd` on KEYWORD_PERFORMANCE | no fan-out — mcgd is 1:1 on client_id + marketing_campaign_group_id |
  | null/NA guards demoted to caller filters (RR families, BU_REQUESTS_*) | reproduced exactly with the filters `MERGE_MAP.md` prescribes |
  | `date >= '2022-07-11'` floor dropped from BU_REQUESTS_PLA | no effect on a 2026 window |
  | raw vs normalised category split | `category_l*_raw` reproduces MERCHANT_CATEGORY_CPC; `category_l*` keeps CATEGORY_LEVEL's `'Unknown'`/`'-'` |
  | `campaign_id` → `internal_campaign_id` rename | reproduces CAMPAIGN_NETWORKS_BY_ID exactly (2,114 rows) |

  So the `Caller must now` column of `MERGE_MAP.md` is **verified**, not merely asserted.

  Two engine facts worth keeping: `limit` caps at **100,000** (heavier grains must page —
  silent truncation would fake a mismatch), and large chunked responses can drop
  mid-body with `ChunkedEncodingError`, which is transport, not data — one pair hit it
  and passed on a clean retry.

  **Caveat:** one agency, one 3-day window. Strong evidence of SQL equivalence, not proof
  across tenants.

**Remaining:**

1. **Widen the numeric diff** — a second agency, and a window with non-zero
   `attributed_sales` (0.00 on every keyword row here).
2. **Exercise the `is_negative` discriminator** on `CAMPAIGN_KEYWORDS` — 0 rows on both
   sides for every campaign tried, so the mechanism the keywords merge depends on is
   still unproven.
3. **Post `INTERNAL_PERF_FILTER_PRESENCE_RR`** — the only one of the 41 active configs
   never written to Mongo (BQ-blocked regardless, but it should exist).

### Full-estate verification (2026-07-28) — the 4 configs needing separate attention

All 41 active configs were fetched requesting every exposed column
(`scripts/verify_remaining.py` for the 26 non-consolidated ones). **20 OK · 2 EMPTY ·
4 ERROR.** Full triage table in `AUTHORING_STATUS.md`; summary:

| Config | Cause | Owner |
|---|---|---|
| `CATEGORY_REQUEST_VOLUME` | BQ IAM on `reporting_<region>.os_product_ads_request_report` | infra |
| `FILTER_PRESENCE_RR` | never posted to Mongo (then same IAM wall) | us, then infra |
| `DAILY_ORDER_TRENDS` | `channel` selector references `cvcpf`, unbound in the outer query — **report is fine without it (3 rows verified)** | us — §5 bug 1, now reproduced |
| `RESPONDED_SKUS` | no `externalRequiredFilters`, so unscoped fetch times out — **works scoped (18 rows verified)** | us |

Plus `AUDIT_EVENTS` + its 3 predecessors, blocked on the unregistered
`GCP_BQ_KAM_CREDENTIALS_EXTERNAL_DATASET` appKey and IAM on `audit.audit_logs_v2`.

So: **35 of 41 configs return real data, 2 are empty-but-sound, 4 need the fixes above,
and the audit family needs a kamService change.** None of the four is a consolidation
regression — `DAILY_ORDER_TRENDS` and `RESPONDED_SKUS` were deliberately left unmerged.
3. **Fix the audit appKey.** `GCP_BQ_KAM_CREDENTIALS_EXTERNAL_DATASET` is not registered in
   kamService; register it, or grant an existing service account IAM on
   `audit.audit_logs_v2`. Unblocks `AUDIT_EVENTS` and its 3 predecessors.
4. **Flip visibility to `INTERNAL_PERFORMANCE`** once the enum ships to test, via
   `repost_internal_performance.sh`. Disk already carries the target value.
5. **Update the `debug-*` skills and `report_map.py`** to the merged reportTypes, using the
   `Caller must now` column in `MERGE_MAP.md`.
6. Fix bugs 1, 5 and 6 in §5, and revisit the two deferred search-query merges.
7. **Consider the tag taxonomy** before more reports are added — `report_group:bu` mints an
   MCP tool named `get_bus_reports`, `report_group:rr` → `get_rrs_reports`. Renaming later
   touches every config and every columnMetadata entry.

## 8. Original order of work

Wave 1 → Wave 2 → Wave 3, then a coverage check that every retired report's
`(attributes, metrics)` set is fully contained in its successor, then repost + re-validate
on the test agency. Retired configs move to `_retired/` rather than being deleted, so the
posted-but-superseded reportTypes stay traceable until they are de-listed from the
catalogue.
