# Remaining KAM config queue (inline + external, INTERNAL_USER)

Authored via `.claude/kam-authoring-prompt-v2.md` (author-only subagents). **Validation is
run only by the orchestrator (main session)** with `post_external.py` — subagents never touch
the test env. External names below are pre-checked against the test-env catalogue baseline
(`$CLAUDE_JOB_DIR/tmp/catalogue_baseline.txt`) to avoid collisions with production reports.

Status: ⬜ todo · 🛠 authoring · 🧪 authored (awaiting validate) · ✅ green · ⛔ blocked

## Progress log
- **Proof wave ✅ 3/3 green** (agency 105, 2026-07-19→21): `INTERNAL_PERF_MERCHANT_RR` (2688 rows),
  `INTERNAL_PERF_KW_PERF_IN_CAMPAIGNS` (19921 rows), `INTERNAL_PERF_RR_BY_DIMENSION_PLA` (5 page types).
  Catalogue diff clean — only our 3 external reports added, no rogue reports. Safety model held.

- **Wave B ✅ 9/9 green**: RR_BY_DIMENSION_DISPLAY, RR_BY_PAGE_PLA, RR_BY_PAGE_DISPLAY, RR_DISPLAY_PAGE_TYPE,
  DISPLAY_AD_UNIT (spend now converted), BU_REQUESTS_PLA, BU_REQUESTS_DISPLAY, WALLET_BALANCE (42k rows),
  BUDGET_DELIVERY_MODE. Catalogue diff clean.
- **Wave C ✅ 5/5 green**: KW_COMPETITION (25k rows), KW_REQUEST_VOLUME (SP-tz), SEARCH_QUERY_MATCH
  (top-of-search via agencies flag; SOV omitted as not-inline-templatable), SEARCH_QUERY_PERF (SP-tz),
  SEARCH_QUERY_CAMPAIGNS.
- **Env lesson:** KAM test env returns intermittent **500s under rapid-fire heavy queries** — validate
  configs ONE AT A TIME (solo), retry a 500 alone. Added `--filter KEY:OP:V1,V2` to `post_external.py`
  to validate required-filter reports scoped (light + correct). Known agency-105 advertiser: os_client_id
  10009172 (campaigns 1322334, 1105688); merchant os_client_id 277661; keyword/search_query "iphone".

- **Wave D — 5 green, 2 structural, 2 BLOCKED(infra)**:
  - ✅ green: SEARCH_QUERY_RR_PLA, SEARCH_QUERY_RR_BUCKETS, RR_HOURLY, RR_HOURLY_AD_UNIT, STORE_LEVEL_RR.
  - 🟨 authored+structural (posts/catalogues/columns resolve; mirror green RR_DISPLAY_PAGE_TYPE on same
    table; unfiltered fetch exceeds test-env query time — real scoped usage works): SEARCH_QUERY_RR_DISPLAY,
    SEARCH_QUERY_RR_DISPLAY_AD_UNIT.
  - ⛔ BLOCKED — infra, not config: CATEGORY_REQUEST_VOLUME, FILTER_PRESENCE_RR. Configs are correct and
    `__SP_REPORTING_DB_REGION__` resolves (→ `_belgium` on test agency 105), but KAM's BQ service account
    is **Access Denied** on `reporting_<region>.os_product_ads_request_report` (the raw request log). Will
    work once KAM is granted BQ access to the region request-log datasets (ledger PR2-B). `__SP_MARKETPLACE_CLIENT_ID__`
    remains unconfirmed (failed earlier on table-access, before the mcid filter mattered).

- **Wave E ✅ 10/10 authored+validated** (6 with live data, 4 clean/0-rows-for-test-scope = data-valid):
  CAMPAIGN_PERF_AGG, CAMPAIGN_PERF_DAILY, CATEGORY_LEVEL, MERCHANT_CATEGORY, CAMPAIGNS_IN_CATEGORY
  (inlined bidding-strategy CASE ✓), CAMPAIGN_KW_TARGETED (34 rows); MERCHANT_KEYWORD, CAMPAIGN_KW_NEGATIVE,
  CAMPAIGN_NETWORKS_BY_ID, CAMPAIGN_NETWORKS_VIA_CTD (0 rows for tested scope).
  - **Cross-cutting fix:** OLTP `os_ads_db_*` tables store keys as INT64 but `reporting.*` is STRING →
    added `SAFE_CAST(... AS STRING)` on joins + filterable id attributes (KW_TARGETED/NEGATIVE, NETWORKS ×2).
  - **Also fixed:** the 2 NETWORKS reports relied on `__CLIENT_ID__` (not injected by agency-level fetch) →
    dropped that predicate; they now scope purely by the required `campaign_id` filter.

- **Waves F+G+H — 11 green, 3 BLOCKED(infra)**:
  - ✅ Wave F (5/5): BUDGET_PACING_BUCKETS, CAMPAIGN_DAILY_BUDGET_AVG (clean/0-rows), CAMPAIGN_DAILY_BUDGET_FLEXI
    (500), MINUTE_CPC (152 rows), MINUTE_CPM (838 rows).
  - ✅ Wave G (4/7): CAMPAIGN_PRODUCT_SELECTION (69 rows — **`__SP_MARKETPLACE_CLIENT_ID__` CONFIRMED** as a
    table-name suffix), RESPONDED_SKUS (48 rows, per-mcid+SP-tz+converted), DISPLAY_QUADRANT (31 rows, OLTP
    `os_ads_db_*` joins resolve), DISPLAY_INVENTORY_CAMPAIGNS (3 rows).
  - ⛔ Wave G (3/7) BLOCKED — infra: BUDGET_CHANGES, CAMPAIGN_STATUS_CHANGES, PRODUCT_SELECTION_CHANGES.
    Configs correct + posted, but KAM BQ account is **Access Denied on `audit.audit_logs_v2`** (ledger PR2-E).
  - ✅ Wave H (2/2): PROBLEM_METRICS (41 rows — trend table populated for wk 2026-07-13), MARKETPLACE_DIRECTORY
    (64 rows, cross-tenant).
  - Fixes applied by orchestrator: 3 audit + 1 intake + 1 shared config had `placeholder_metric` missing
    `externalColumnName` → patched; STORE_LEVEL_RR INTEGER→FLOAT; OLTP SAFE_CAST casts.

## FINAL TALLY (this session)
- **~45 configs authored** (all remaining queries). **~40 validated GREEN** end-to-end against agency 105.
- **5 infra-blocked** (configs correct, need KAM BQ grants): CATEGORY_REQUEST_VOLUME, FILTER_PRESENCE_RR
  (`reporting_<region>.os_product_ads_request_report`); BUDGET_CHANGES, CAMPAIGN_STATUS_CHANGES,
  PRODUCT_SELECTION_CHANGES (`audit.audit_logs_v2`).
- Catalogue diff clean every wave — no rogue reports; subagents authored files only, orchestrator did all posts.
- **(2026-07-27) The 2 formerly-structural reports are now GREEN** — `SEARCH_QUERY_RR_DISPLAY` +
  `SEARCH_QUERY_RR_DISPLAY_AD_UNIT` rebuilt and validated keyword-scoped (iphone). No longer pending.

## POST-CLEANUP (this pass)
- Retired all 16 superseded class-based `KAM_AGENT_*` files (each had a validated INTERNAL_PERF replacement).
  Disk is single-generation.
- **Removed the 7 non-green reports from BOTH disk and the test-env external catalogue** (5 de-listed by
  overwrite-to-inert; 2 were never posted). They are tracked as still-to-build in
  **`TODO_REPORTS_TO_BUILD.md`** (keyed to their source `query_inventory/*.sql`, with the BQ-access
  blocker + rebuild steps). **(2026-07-27) 2 of those rebuilt+green → 65 INTERNAL_PERF_* configs on
  disk, all green; only 5 remain (all infra/BQ-access-blocked).**

## Naming collisions to AVOID (already in prod catalogue)
`SEARCH_QUERY_PERFORMANCE_REPORT`, `CAMPAIGN_PERFORMANCE_REPORT`, `KEYWORD_PERFORMANCE_REPORT`,
`CAMPAIGN_SEARCH_QUERY_PERFORMANCE_REPORT` — do NOT reuse; use the distinct names below.

---

## Proof wave (prove pipeline + safety end-to-end)
| tool | skill | report_type | external_report_type | groups | note |
|---|---|---|---|---|---|
| get_merchant_rr_breakdown | rr | INTERNAL_PERF_MERCHANT_RR | MERCHANT_RR_BREAKDOWN_REPORT | merchant_breakdown, rr | cvcpf; mirrors MERCHANT_CTR |
| check_targeted_keyword_performance_in_campaigns | keyword_delivery | INTERNAL_PERF_KW_PERF_IN_CAMPAIGNS | KW_PERF_IN_CAMPAIGNS_REPORT | keyword | req filters: client_id+campaign_id |
| get_response_rate_by_dimension (PLA) | rr | INTERNAL_PERF_RR_BY_DIMENSION_PLA | RR_BY_DIMENSION_PLA_REPORT | rr | RE-AUTHOR of KAM_AGENT_RR_BY_DIMENSION_PLA |

## Wave B — finish partial waves + re-author 🟡 (low risk)
| tool | skill | report_type | external_report_type | groups |
|---|---|---|---|---|
| get_response_rate_by_dimension (DISPLAY) | rr | INTERNAL_PERF_RR_BY_DIMENSION_DISPLAY | RR_BY_DIMENSION_DISPLAY_REPORT | rr |
| check_response_rate_by_page (PLA) | rr | INTERNAL_PERF_RR_BY_PAGE_PLA | RR_BY_PAGE_PLA_REPORT | rr, page_performance |
| check_response_rate_by_page (DISPLAY) | rr | INTERNAL_PERF_RR_BY_PAGE_DISPLAY | RR_BY_PAGE_DISPLAY_REPORT | rr |
| check_display_page_type_rr | rr | INTERNAL_PERF_RR_DISPLAY_PAGE_TYPE | RR_DISPLAY_PAGE_TYPE_REPORT | rr |
| get_display_ad_unit_performance | bu | INTERNAL_PERF_DISPLAY_AD_UNIT | DISPLAY_AD_UNIT_PERFORMANCE_REPORT | bu |
| check_requests (PLA) | bu | INTERNAL_PERF_BU_REQUESTS_PLA | BU_REQUESTS_PLA_REPORT | bu |
| check_requests (DISPLAY) | bu | INTERNAL_PERF_BU_REQUESTS_DISPLAY | BU_REQUESTS_DISPLAY_REPORT | bu |
| get_merchant_wallet_balance | bu | INTERNAL_PERF_WALLET_BALANCE | WALLET_BALANCE_REPORT | bu, merchant_breakdown |
| get_budget_delivery_mode | budget_pacing | INTERNAL_PERF_BUDGET_DELIVERY_MODE | BUDGET_DELIVERY_MODE_REPORT | budget_pacing |

## Wave C — keyword + CTR search-query
| tool | skill | report_type | external_report_type | groups |
|---|---|---|---|---|
| get_targeted_keyword_competition | keyword_delivery | INTERNAL_PERF_KW_COMPETITION | KW_COMPETITION_REPORT | keyword |
| check_keyword_request_volume | keyword_delivery | INTERNAL_PERF_KW_REQUEST_VOLUME | KW_REQUEST_VOLUME_REPORT | keyword |
| get_search_query_match_performance | ctr | INTERNAL_PERF_SEARCH_QUERY_MATCH | SEARCH_QUERY_MATCH_PERFORMANCE_REPORT | search_query, ctr |
| get_search_query_performance | shared | INTERNAL_PERF_SEARCH_QUERY_PERF | INTERNAL_SEARCH_QUERY_PERFORMANCE_REPORT | search_query |
| get_search_query_campaigns | rr | INTERNAL_PERF_SEARCH_QUERY_CAMPAIGNS | SEARCH_QUERY_CAMPAIGNS_REPORT | search_query, rr |

## Wave D — RR search-query + buckets + hourly (SP-tz)
| tool | skill | report_type | external_report_type | groups |
|---|---|---|---|---|
| get_search_query_response_rates (PLA) | rr | INTERNAL_PERF_SEARCH_QUERY_RR_PLA | SEARCH_QUERY_RR_PLA_REPORT | search_query, rr |
| get_search_query_response_rates (DISPLAY) | rr | INTERNAL_PERF_SEARCH_QUERY_RR_DISPLAY | SEARCH_QUERY_RR_DISPLAY_REPORT | search_query, rr |
| get_search_query_response_rates (DISPLAY_AD_UNIT) | rr | INTERNAL_PERF_SEARCH_QUERY_RR_DISPLAY_AD_UNIT | SEARCH_QUERY_RR_DISPLAY_AD_UNIT_REPORT | search_query, rr |
| get_search_query_rr_buckets | rr | INTERNAL_PERF_SEARCH_QUERY_RR_BUCKETS | SEARCH_QUERY_RR_BUCKETS_REPORT | search_query, rr |
| get_store_level_rr_buckets | rr | INTERNAL_PERF_STORE_LEVEL_RR | STORE_LEVEL_RR_REPORT | rr |
| check_display_hourly_rr (ad_unit) | rr | INTERNAL_PERF_RR_HOURLY_AD_UNIT | RR_HOURLY_AD_UNIT_REPORT | rr |
| check_display_hourly_rr (hourly) | rr | INTERNAL_PERF_RR_HOURLY | RR_HOURLY_REPORT | rr |
| get_category_request_volume | rr | INTERNAL_PERF_CATEGORY_REQUEST_VOLUME | CATEGORY_REQUEST_VOLUME_REPORT | category, rr |
| get_filter_presence_response_rates | rr | INTERNAL_PERF_FILTER_PRESENCE_RR | FILTER_PRESENCE_RR_REPORT | rr |

## Wave E — shared campaign/category/merchant
| tool | skill | report_type | external_report_type | groups |
|---|---|---|---|---|
| get_campaign_performance (aggregated) | shared | INTERNAL_PERF_CAMPAIGN_PERF_AGG | CAMPAIGN_PERF_AGGREGATED_REPORT | campaign |
| get_campaign_performance (daily) | shared | INTERNAL_PERF_CAMPAIGN_PERF_DAILY | CAMPAIGN_PERF_DAILY_REPORT | campaign |
| get_category_level_performance | shared | INTERNAL_PERF_CATEGORY_LEVEL | CATEGORY_LEVEL_PERFORMANCE_REPORT | category |
| get_merchant_category_performance | shared | INTERNAL_PERF_MERCHANT_CATEGORY | MERCHANT_CATEGORY_PERFORMANCE_REPORT | merchant_breakdown, category |
| get_merchant_keyword_performance | shared | INTERNAL_PERF_MERCHANT_KEYWORD | MERCHANT_KEYWORD_PERFORMANCE_REPORT | merchant_breakdown, keyword |
| get_campaigns_in_category | shared | INTERNAL_PERF_CAMPAIGNS_IN_CATEGORY | CAMPAIGNS_IN_CATEGORY_REPORT | category, campaign |
| get_campaign_targeted_keywords (targeted) | shared | INTERNAL_PERF_CAMPAIGN_KW_TARGETED | CAMPAIGN_TARGETED_KEYWORDS_REPORT | campaign, keyword |
| get_campaign_targeted_keywords (negative) | shared | INTERNAL_PERF_CAMPAIGN_KW_NEGATIVE | CAMPAIGN_NEGATIVE_KEYWORDS_REPORT | campaign, keyword |
| get_campaign_targeted_networks (by_campaign_id) | shared | INTERNAL_PERF_CAMPAIGN_NETWORKS_BY_ID | CAMPAIGN_NETWORKS_BY_ID_REPORT | campaign |
| get_campaign_targeted_networks (via_ctd) | shared | INTERNAL_PERF_CAMPAIGN_NETWORKS_VIA_CTD | CAMPAIGN_NETWORKS_VIA_CTD_REPORT | campaign |

## Wave F — budget pacing (SP-tz + audit)
| tool | skill | report_type | external_report_type | groups |
|---|---|---|---|---|
| get_budget_pacing_buckets | budget_pacing | INTERNAL_PERF_BUDGET_PACING_BUCKETS | BUDGET_PACING_BUCKETS_REPORT | budget_pacing |
| get_campaign_daily_budget (avg) | budget_pacing | INTERNAL_PERF_CAMPAIGN_DAILY_BUDGET_AVG | CAMPAIGN_DAILY_BUDGET_AVG_REPORT | budget_pacing |
| get_campaign_daily_budget (flexi) | budget_pacing | INTERNAL_PERF_CAMPAIGN_DAILY_BUDGET_FLEXI | CAMPAIGN_DAILY_BUDGET_FLEXI_REPORT | budget_pacing |
| get_minute_level_cpc_data | budget_pacing | INTERNAL_PERF_MINUTE_CPC | MINUTE_LEVEL_CPC_REPORT | budget_pacing |
| get_minute_level_cpm_data | budget_pacing | INTERNAL_PERF_MINUTE_CPM | MINUTE_LEVEL_CPM_REPORT | budget_pacing |

## Wave G — audit + per-mcid-suffix (highest-risk patterns, do last, extra care)
| tool | skill | report_type | external_report_type | groups | risk |
|---|---|---|---|---|---|
| check_budget_changes_on_date | budget_pacing | INTERNAL_PERF_BUDGET_CHANGES | BUDGET_CHANGES_REPORT | budget_pacing | audit JSON |
| get_campaign_status_changes | shared | INTERNAL_PERF_CAMPAIGN_STATUS_CHANGES | CAMPAIGN_STATUS_CHANGES_REPORT | campaign | audit JSON |
| get_product_selection_changes | shared | INTERNAL_PERF_PRODUCT_SELECTION_CHANGES | PRODUCT_SELECTION_CHANGES_REPORT | campaign | audit JSON |
| get_campaign_product_selection | shared | INTERNAL_PERF_CAMPAIGN_PRODUCT_SELECTION | CAMPAIGN_PRODUCT_SELECTION_REPORT | campaign | per-mcid suffix (__SP_MARKETPLACE_CLIENT_ID__) |
| get_responded_skus | irrelevancy | INTERNAL_PERF_RESPONDED_SKUS | RESPONDED_SKUS_REPORT | irrelevancy, sku | per-mcid suffix + SP-tz |
| get_display_quadrant_performance | bu | INTERNAL_PERF_DISPLAY_QUADRANT | DISPLAY_QUADRANT_REPORT | bu | OLTP config joins |
| get_display_inventory_campaigns | bu | INTERNAL_PERF_DISPLAY_INVENTORY_CAMPAIGNS | DISPLAY_INVENTORY_CAMPAIGNS_REPORT | bu, campaign | OLTP config joins |

## Wave H — intake re-authors (inline+external)
| tool | skill | report_type | external_report_type | groups | note |
|---|---|---|---|---|---|
| get_problem_metrics | shared | INTERNAL_PERF_PROBLEM_METRICS | PROBLEM_METRICS_REPORT | intake | re-author KAM_AGENT_PROBLEM_METRICS |
| fetch_marketplace_info | shared | INTERNAL_PERF_MARKETPLACE_DIRECTORY | MARKETPLACE_DIRECTORY_REPORT | intake | re-author; cross-tenant (no __AGENCY_ID__) |

## Cleanup (orchestrator only, LAST — never delegate)
- ✅ **Retired (deleted from disk)** the 4 superseded class-based dups, each after confirming its
  INTERNAL_PERF replacement exists: `KAM_AGENT_CTR_OVERALL`, `KAM_AGENT_ROAS_GMV_ATTRIBUTION`,
  `KAM_AGENT_PAGE_LEVEL_PERFORMANCE`, `KAM_AGENT_RR_CATEGORY`.
  - Note: their **test-env Mongo records remain** (KAM has no delete API; class-based configs are NOT
    in the external catalogue, so nothing served changes). The LOCAL_DEMO shim reads Mongo, not disk.
- ✅ **Retired the remaining 12 KAM_AGENT_* too** (bu ×4, budget_pacing ×1, rr ×5, shared/intake ×2),
  each after confirming its INTERNAL_PERF replacement exists. **Disk is now single-generation: 0
  KAM_AGENT_*, 70 INTERNAL_PERF_* configs.** Their test-env Mongo records remain (no delete API;
  not in the external catalogue, so nothing served changes).
</content>
