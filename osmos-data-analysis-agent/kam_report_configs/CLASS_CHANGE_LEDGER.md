# KAM class-change ledger

Triage of **every** data-fetching SOP tool into **config-only** (no kamService
change — author the JSON, post it) vs **needs-class** (a kamService PR + deploy).
Produced by the fan-out defined in `.claude/mcp-class-change-ledger-prompt.md`,
cross-checked against the registered classes in
`kamService/src/utils/schema/schemaRegistry.js`.

**How to read a verdict**
- `config-only` — every metric/attribute/filter/grouping the query needs already
  exists on a registered class. Ship now, no PR.
- `verify` — config-only *except* one unconfirmed attribute/metric; open one class
  file to resolve. Almost all of these are expected to become config-only.
- `needs-class` → `PR1-cvcpf` (the one cvcpf enhancement) or `PR2-*` (a new class /
  new column on another table). Only these need a kamService PR.

---

## 1. Summary counts (60 real tools)

| Verdict | Count | Needs a kamService PR? |
|---|---|---|
| **config-only** | 12 (1 shipped: `check_ctr_overall`) | No — author + post |
| **verify** | 8 | No (pending one class-file check each) |
| **needs-class · PR1-cvcpf** | 8 | Yes — but a config-only MMF substitute exists for all 8 (see §4) |
| **needs-class · PR2 (new class / column)** | 32 | Yes — clustered into thematic PRs in §5 |

**Headline:** ~20 tools (12 config-only + 8 verify) need **no code change at all**,
and another 5 of the 8 cvcpf tools can ship config-only via the MMF substitute. So
**~25 of 60 tools are shippable with zero kamService change** — that's the queue to
run now. The remaining ~35 concentrate into a **small number of cohesive class PRs**.

---

## 2. Config-only queue — author now, no PR (ordered)

Reuse existing classes; author the `KAM_AGENT_*` config, post to test, diff vs legacy.

| # | Tool | Skill | Classes reused | Suggested reportType |
|---|---|---|---|---|
| ✅ | `check_ctr_overall` | ctr | MonetizeMerchantFacts | `KAM_AGENT_CTR_OVERALL` (shipped) |
| 1 | `get_page_level_performance` | shared | OsProductAdsPageNamePerformanceFacts (+scc) | `KAM_AGENT_PAGE_LEVEL_PERFORMANCE` |
| 2 | `check_response_rate_by_page` | rr | OsProductAdsPageNamePerformanceFacts, OsDisplayAdsAdUnitFacts | `KAM_AGENT_RR_BY_PAGE` |
| 3 | `check_display_page_type_rr` | rr | OsDisplayAdsFilteredLevelPerformanceFacts | `KAM_AGENT_RR_DISPLAY_PAGE_TYPE` |
| 4 | `get_category_response_rates` | rr | OsProductAdsSupplyAnalyticsReport | `KAM_AGENT_RR_CATEGORY` |
| 5 | `get_response_rate_by_dimension` | rr | OsProductAdsSupplyAnalyticsReport, OsDisplayAdsFilteredLevelPerformanceFacts | `KAM_AGENT_RR_BY_DIMENSION` |
| 6 | `check_requests` | bu | OsDisplayAdsAdUnitFacts, OsProductAdsPageNamePerformanceFacts | `KAM_AGENT_BU_REQUESTS` |
| 7 | `get_display_ad_unit_performance` | bu | OsDisplayAdsAdUnitFacts (+scc) | `KAM_AGENT_BU_DISPLAY_AD_UNIT` |
| 8 | `get_merchant_wallet_balance` | bu | Clients, MarketplaceClients (+scc) | `KAM_AGENT_BU_WALLET_BALANCE` |
| 9 | `get_budget_delivery_mode` | budget_pacing | MarketingCampaignDimensions | `KAM_AGENT_BUDGET_DELIVERY_MODE` |
| 10 | `check_targeted_keyword_performance_in_campaigns` | keyword_delivery | OsAdsKeywordPerformanceReport (+scc) | `KAM_AGENT_KW_PERF_IN_CAMPAIGNS` |
| 11 | `get_targeted_keyword_competition` | keyword_delivery | OsAdsKeywordPerformanceReport, MarketingCampaignDimensions | `KAM_AGENT_KW_COMPETITION` |

---

## 3. Verify queue — one class-file check flips each to config-only

| Tool | Skill | The single check | Likely outcome |
|---|---|---|---|
| `get_category_level_performance` | shared | category_l1/l2/l3 + merchant_id/date grouping attrs on `MarketplaceCategoryLevelPerformanceFactsV2AttributesClass` | config-only |
| `get_merchant_keyword_performance` | shared | `matched_keyword`+`keyword_match_type` attrs & `ad_revenue` metric on `OsAdsKeywordPerformanceReport` | config-only |
| `get_campaign_performance__aggregated` | shared | orders/revenue metrics + `daily_budget` attr on `CampaignPerformanceFacts`; `campaign_type` on group-dims | config-only |
| `get_campaign_performance__daily` | shared | same as aggregated + `date` grouping attr | config-only |
| `get_campaigns_in_category` | shared | category_l1/l2/l3 + spend/cpc/cpm on `OsProductAdsCampaignCategoryReportPla`; `campaign_setting_metadata`+`campaign_subtype` for the bidding-strategy CASE | config-only |
| `get_merchant_category_cpc_comparison` | cpc | `agency_id` filter attr on `MarketplaceCategoryLevelPerformanceFactsV2AttributesClass` | config-only, else 1 attr add |
| `get_target_roi` | roas | column `target_roi` vs `onsite_target_roi` on `AgenciesAttributesClass` | config-only via `onsite_target_roi`, else 1 attr add |
| `get_sku_level_ctr_performance` | ctr | whether the join framework needs `account_id` exposed on `OsProductAdsSkuCampaignFacts` (base fact class lacks it) | config-only, else add `account_id` (folds into PR3) |

---

## 4. PR1 — `ClientVendorChannelPerformanceFacts` (cvcpf) enhancement

**The single highest-leverage class change.** Unblocks 8 tools across 5 skills.

**Class additions (checklist):**
- [ ] channel/vendor **filter attribute** for the PLA/Display split
  (`vendor='os_ads' AND channel IN (...)`) — the `channel_condition` fragment.
- [ ] **converted-spend metric** (`SUM(cost * conversion_factor)`) — current `spend`
  is `SUM(cost)`, unconverted.
- [ ] **per-click-timestamp program metrics**
  (`program_per_click_timestamp_{sales,conversions,viewproduct,add_to_cart}`, +
  `pla_`/`display_` variants).

**Tools unblocked & their config-only substitute:**

| Tool | Skill | Clean MMF substitute? |
|---|---|---|
| `check_program_spend` | bu | ✅ clicks/impr/spend per program — MMF merchant/marketplace grain |
| `get_merchant_bu_breakdown` | bu | ✅ MMF merchant-grain |
| `get_merchant_ctr_breakdown` | ctr | ✅ MMF merchant-grain (same pattern as shipped `check_ctr_overall`) |
| `get_merchant_cpc_breakdown` | cpc | ⚠️ spend/clicks ✅ via MMF, but program funnel = attribution change |
| `get_merchant_rr_breakdown` | rr | ✅ MMF merchant-grain (spend used only for Pareto) |
| `check_gmv_attribution` | roas | ❌ MMF has only native `program_orders`/`program_revenue` — **different attribution** |
| `get_daily_order_trends` | roas | ❌ same ROAS attribution fork |
| `get_merchant_breakdown` | roas | ❌ same ROAS attribution fork |

**Decision this PR forces (already open):** the **3 ROAS tools** need the
per-click-timestamp attribution — MMF's native program figures are a *different
definition*. So either (a) do the cvcpf PR to stay faithful, or (b) accept MMF-native
attribution for ROAS (numbers differ from legacy). The **5 non-ROAS tools** have a
*clean* MMF substitute (just clicks/impr/spend per merchant) and can ship
**config-only today** — validate each against the legacy cvcpf query, as we did for
`check_ctr_overall`.

> **So PR1 is really only mandatory for the 3 ROAS program-funnel tools.** If we
> take the MMF substitute for the other 5, PR1 shrinks to "unblock faithful ROAS."

---

## 5. PR2 — new classes, clustered by data domain

The 32 PR2 tools concentrate into these class changes. Grouped so each ships as one
cohesive, individually-testable PR (ordered by tools-unblocked / value).

### PR2-A · Search-query & keyword facts (unblocks ~9 tools)
New classes for the search-query report family:
- [ ] `os_ads_search_query_performance_report` (search_query, client/merchant_id, keyword_match_type, clicks/impr/cost) → `get_keyword_seller_breakdown` (ctr), `get_search_query_match_performance` (ctr, partial), `get_search_query_campaigns` (rr), `get_search_query_performance` (shared)
- [ ] `os_product_ads_search_query_request_report` (search_query/request grain, tz-aware) → `check_keyword_request_volume` (kw), `get_search_query_response_rates` PLA branch (rr), `get_search_query_rr_buckets` (rr)
- [ ] `os_marketplace_search_query_performance_facts` + `agencies.is_impression_ad_position_enabled` attr + top-of-search impression metrics → completes `get_search_query_match_performance`

### PR2-B · Request-log facts, region/tz-aware (unblocks 2 tools)
- [ ] `os_product_ads_request_report` (raw request log: `rid`, `f_cat1..3`, filter cols `f_brands/f_zone/f_storeid/f_network/f_city/f_state/f_country/device`, `timestamp_utc`; region-specific dataset + tz-aware date cast) → `get_category_request_volume` (rr), `get_filter_presence_response_rates` (rr)

### PR2-C · SKU / device-product facts (unblocks 3 tools)
- [ ] `os_product_ads_device_product_facts` (SKU×device PLA fact: spend/impr/clicks/orders/ad_revenue + program funnel) → `get_sku_level_performance` (roas), `get_sku_level_cpc_performance` (cpc), `get_merchant_category_performance` (shared)
- [ ] (if the verify flips) add `account_id` to `OsProductAdsSkuCampaignFacts` → `get_sku_level_ctr_performance` (ctr)

### PR2-D · Minute-level response mappings (unblocks 3 tools)
- [ ] `os_product_ads_response_to_clicks_mapping` (per-minute: `unique_click`, `bid`, `page_type`, `response_timestamp_utc`) → `get_minute_level_cpc_data`
- [ ] `os_product_ads_response_to_impressions_mapping` (per-minute: `unique_impressions`, `cache_type`, `sku_id`, `search_query`, `bid`) → `get_minute_level_cpm_data`, `get_responded_skus`

### PR2-E · Audit-log (JSON extraction) (unblocks 3 tools)
- [ ] `audit.audit_logs_v2` (JSON `old_state`/`new_state`/`scope_metadata`/`user`, `action_type_id` filter) → `check_budget_changes_on_date` (action 17), `get_campaign_status_changes` (16), `get_product_selection_changes` (50/51)
  - ⚠️ verify the class framework can express `JSON_EXTRACT_SCALAR` selectors — this shape is atypical for KAM.

### PR2-F · OLTP config/status lookups (unblocks 4 tools)
- [ ] `os_ads_db_campaign_level_keywords` (text, bidding_value, is_negative/is_deleted) → `get_campaign_targeted_keywords` (targeted+negative)
- [ ] `os_ads_db_campaign_targeting_mapping` (target_type, target_details JSON) → `get_campaign_targeted_networks` (by_campaign_id + via_ctd)
- [ ] `os_ads_db_campaign_inventory_configurations`, `os_ads_db_status_types`, `os_ads_db_campaigns`, `os_ads_db_campaign_types` → `get_display_inventory_campaigns` (bu), `get_display_quadrant_performance` (bu)

### PR2-G · Budget history / pacing (unblocks 3 tools)
- [ ] `marketing_campaign_dimensions_daily` (daily_budget/cost/effective_status history) — shared by `get_true_bu_campaign_data` (bu) + `get_campaign_daily_budget` (budget)
- [ ] `client_budget_snapshot` (point-in-time wallet balance) — same two tools
- [ ] `os_ads_campaign_avg_daily_budget_projections` (`derived_daily_budget`) → `get_campaign_daily_budget`
- [ ] `os_ads_marketplace_budget_pacing_configurations` (raw `budget_pacing_json`) → `get_budget_pacing_buckets`

### PR2-H · Quadrant & brand-inventory facts (unblocks 3 tools)
- [ ] `os_product_ads_daily_category_quadrant_report_pla` → `get_category_quadrant_performance` (bu)
- [ ] `os_display_ads_daily_quadrant_report` → `get_display_quadrant_performance` (bu)
- [ ] `os_brand_ads_network_level_facts` → `get_campaign_inventory_performance` (bu)

### PR2-I · Trend analysis & product selection (unblocks 2 tools)
- [ ] `os_ads_performance_trend_analysis_report` (row-level passthrough) → `get_problem_metrics` (shared)
- [ ] per-marketplace suffixed tables `os_product_ads_product_selection_{mcid}` + `oltp_merchandise_product_dimensions_{mcid}` — needs a **templated-table strategy** (fixed-name classes can't take a runtime `{marketplace_client_id}` suffix) → `get_campaign_product_selection` (shared), completes `get_responded_skus`

### PR2-lite · Cheap adds on EXISTING classes (fold into the nearest PR)
- [ ] `date_hour` / hour-of-day attr on `OsDisplayAdsFilteredLevelPerformanceFacts` (+ SupplyAnalytics) → `check_display_hourly_rr`, `get_store_level_rr_buckets`
- [ ] `filter_keywords` attr on `OsDisplayAdsFilteredLevelPerformanceFactsAttributesClass` → `get_search_query_response_rates` display branch
- [ ] `program_per_click_timestamp_conversions_multi_channel_onsite_offsite` metric on `CampaignPerformanceFactsMetricsClass` → `get_campaign_subtype_cpc_breakdown` (config-only alt: use existing plain `_conversions`)

---

## 6. Recommended sequencing

1. **Now (no PR):** run the §2 config-only queue (11 tools) + resolve the §3 verify
   queue (8 tools, ~all become config-only). ≈19 tools shippable this pass.
2. **Now (no PR):** ship the **5 non-ROAS cvcpf tools** via the MMF substitute
   (validate each vs legacy). ≈24 tools with zero kamService change.
3. **PR1 (cvcpf):** only if we want *faithful* ROAS — else take the MMF/native-
   attribution decision for the 3 ROAS tools and defer.
4. **PR2-A → PR2-I:** batch by domain, in the §5 order (search-query first — most
   tools). Each PR carries its config validation evidence + a kamService CI test, is
   tested against a **branch build** before merge, and re-validated on shared test
   after (see the per-change loop in the project notes).

---

## 7. Full per-tool table (by skill)

### roas
| tool | tables | verdict | pr | gap / note |
|---|---|---|---|---|
| check_gmv_attribution | cvcpf, mmf, clients, mc, scc | needs-class | PR1-cvcpf | per-click-timestamp program funnel; MMF = different attribution (ROAS fork) |
| get_daily_order_trends | cvcpf, mmf, … | needs-class | PR1-cvcpf | same, per date |
| get_merchant_breakdown | cvcpf, mmd, mmf, … | needs-class | PR1-cvcpf | same, per merchant |
| get_sku_level_performance | os_product_ads_device_product_facts, mmpd, ctd, mcd, mcgd, clients, ompf | needs-class | PR2-C | device-product fact has no class |
| get_target_roi | agencies | verify | — | `target_roi` vs `onsite_target_roi` |

### cpc
| tool | tables | verdict | pr | gap / note |
|---|---|---|---|---|
| get_campaign_subtype_cpc_breakdown | campaign_performance_facts, ctd, mcgd, clients | needs-class | PR2-lite | new `_conversions_multi_channel_onsite_offsite` metric; alt = plain `_conversions` |
| get_merchant_category_cpc_comparison | marketplace_category_level_performance_facts_v2, clients | verify | — | `agency_id` filter attr on V2 |
| get_merchant_cpc_breakdown | cvcpf, mmd, mmf, clients, mc, scc | needs-class | PR1-cvcpf | MMF ok for spend/clicks; program funnel = attribution change |
| get_sku_level_cpc_performance | os_product_ads_device_product_facts, … | needs-class | PR2-C | device-product fact class |

### ctr
| tool | tables | verdict | pr | gap / note |
|---|---|---|---|---|
| check_ctr_overall | (mmf) | config-only | — | ✅ shipped, validated agency 105 |
| get_merchant_ctr_breakdown | cvcpf, mmd, clients, mc, scc | needs-class | PR1-cvcpf | clean MMF substitute (ship config-only, validate) |
| get_keyword_seller_breakdown | os_ads_search_query_performance_report, clients | needs-class | PR2-A | search-query report class |
| get_search_query_match_performance | os_marketplace_search_query_performance_facts, os_ads_search_query_performance_report, … | needs-class | PR2-A | two search-query tables + agencies attr |
| get_sku_level_ctr_performance | os_product_ads_device_product_facts→OsProductAdsSkuCampaignFacts, … | verify | (PR2-C) | `account_id` join key on SKU class |

### bu
| tool | tables | verdict | pr | gap / note |
|---|---|---|---|---|
| check_program_spend | cvcpf, clients, mc, scc | needs-class | PR1-cvcpf | channel filter only; clean MMF substitute |
| check_requests | os_display_ads_ad_unit_facts, os_product_ads_page_name_performance_facts, mc | config-only | — | — |
| get_campaign_inventory_performance | os_brand_ads_network_level_facts, ctd, mcgd, brand_ads_dimensions | needs-class | PR2-H | brand network fact has no class |
| get_category_quadrant_performance | os_product_ads_daily_category_quadrant_report_pla, agencies, scc, catpla | needs-class | PR2-H | quadrant report has no class |
| get_display_ad_unit_performance | os_display_ads_ad_unit_facts, mc, scc | config-only | — | — |
| get_display_inventory_campaigns | os_display_ads_ad_targeting_report, …, os_ads_db_campaign_inventory_configurations, os_ads_db_status_types | needs-class | PR2-F | 2 OLTP lookups lack classes |
| get_display_quadrant_performance | os_display_ads_daily_quadrant_report, …, 4× os_ads_db_* | needs-class | PR2-F/H | quadrant report + 4 OLTP lookups |
| get_merchant_bu_breakdown | cvcpf, mmd, clients, mc, scc | needs-class | PR1-cvcpf | clean MMF substitute |
| get_merchant_wallet_balance | clients, mc, scc | config-only | — | `clients_remaining_budget_amount_usd` confirmed |
| get_true_bu_campaign_data | marketing_campaign_dimensions_daily, …, client_budget_snapshot | needs-class | PR2-G | daily-budget history + snapshot classes |

### rr
| tool | tables | verdict | pr | gap / note |
|---|---|---|---|---|
| check_display_hourly_rr | os_display_ads_filtered_level_performance_facts | needs-class | PR2-lite | add `date_hour` attr (ad_unit branch is config-only) |
| check_display_page_type_rr | os_display_ads_filtered_level_performance_facts | config-only | — | — |
| check_response_rate_by_page | os_product_ads_page_name_performance_facts, os_display_ads_ad_unit_facts, mc | config-only | — | — |
| get_category_request_volume | os_product_ads_request_report | needs-class | PR2-B | raw request log, region/tz |
| get_category_response_rates | os_product_ads_filtered_level_report→OsProductAdsSupplyAnalyticsReport, mc | config-only | — | — |
| get_filter_presence_response_rates | os_product_ads_request_report | needs-class | PR2-B | raw request log, present/absent conditional agg |
| get_merchant_rr_breakdown | cvcpf, mmd, clients, mc, scc | needs-class | PR1-cvcpf | clean MMF substitute (spend for Pareto) |
| get_response_rate_by_dimension | os_product_ads_filtered_level_report, os_display_ads_filtered_level_performance_facts | config-only | — | ad_unit grouping is display-only |
| get_search_query_campaigns | os_ads_search_query_performance_report, ctd, mcd | needs-class | PR2-A | search-query report class |
| get_search_query_response_rates | os_product_ads_search_query_request_report (pla), os_display_ads_filtered_level_performance_facts (display) | needs-class | PR2-A + lite | pla class + `filter_keywords` attr for display |
| get_search_query_rr_buckets | os_product_ads_search_query_request_report | needs-class | PR2-A | search-query request class |
| get_store_level_rr_buckets | os_product_ads_filtered_level_report, os_display_ads_filtered_level_performance_facts | needs-class | PR2-lite | add hour-of-day attr (store/category/page all exist) |

### budget_pacing
| tool | tables | verdict | pr | gap / note |
|---|---|---|---|---|
| check_budget_changes_on_date | audit.audit_logs_v2 | needs-class | PR2-E | audit JSON class (action 17) |
| get_budget_delivery_mode | marketing_campaign_dimensions | config-only | — | `budget_delivery_mode` confirmed |
| get_budget_pacing_buckets | os_ads_marketplace_budget_pacing_configurations | needs-class | PR2-G | raw `budget_pacing_json` |
| get_campaign_daily_budget | avg_daily_budget_projections, marketing_campaign_dimensions_daily, client_budget_snapshot, … | needs-class | PR2-G | 3 tables lack classes |
| get_minute_level_cpc_data | os_product_ads_response_to_clicks_mapping, … | needs-class | PR2-D | minute-level mapping class |
| get_minute_level_cpm_data | os_product_ads_response_to_impressions_mapping, … | needs-class | PR2-D | minute-level mapping class |

### keyword_delivery
| tool | tables | verdict | pr | gap / note |
|---|---|---|---|---|
| check_keyword_request_volume | os_product_ads_search_query_request_report | needs-class | PR2-A/B | search-query request class |
| check_targeted_keyword_performance_in_campaigns | os_ads_keyword_performance_report, … | config-only | — | attrs+metrics confirmed |
| get_targeted_keyword_competition | os_ads_keyword_performance_report, mcd, … | config-only | — | confirm mcd `campaign_creation_date`/`effective_status` (standard) |

### irrelevancy
| tool | tables | verdict | pr | gap / note |
|---|---|---|---|---|
| get_responded_skus | os_product_ads_response_to_impressions_mapping, oltp_merchandise_product_dimensions_{mcid}, … | needs-class | PR2-D + I | minute-level mapping + per-mcid product dims |

### shared
| tool | tables | verdict | pr | gap / note |
|---|---|---|---|---|
| get_page_level_performance | os_product_ads_page_name_performance_facts, mc, scc | config-only | — | — |
| get_category_level_performance | marketplace_category_level_performance_facts_v2, mmd, clients | verify | — | category/merchant/date grouping attrs on V2 |
| get_merchant_category_performance | os_product_ads_device_product_facts, … | needs-class | PR2-C | device-product fact class |
| get_merchant_keyword_performance | os_ads_keyword_performance_report, … | verify | — | matched_keyword/keyword_match_type/ad_revenue |
| get_search_query_performance | os_ads_search_query_performance_report, ctd, mcd | needs-class | PR2-A | search-query report class |
| get_campaign_performance__aggregated | campaign_performance_facts, …, scc | verify | — | orders/revenue/daily_budget + campaign_type |
| get_campaign_performance__daily | (same) | verify | — | + date grouping |
| get_campaigns_in_category | os_product_ads_campaign_category_report_pla, agencies, mcd, mcgd, mmd | verify | — | category attrs + bidding-strategy CASE inputs |
| get_problem_metrics | os_ads_performance_trend_analysis_report | needs-class | PR2-I | row-level passthrough class |
| get_campaign_product_selection | os_product_ads_product_selection_{mcid}, ctd, oltp_..._{mcid} | needs-class | PR2-I | per-marketplace templated tables |
| get_campaign_status_changes | audit.audit_logs_v2 | needs-class | PR2-E | audit JSON class (action 16) |
| get_campaign_targeted_keywords (targeted/negative) | os_ads_db_campaign_level_keywords | needs-class | PR2-F | OLTP keywords lookup class |
| get_campaign_targeted_networks (by_campaign_id/via_ctd) | os_ads_db_campaign_targeting_mapping, ctd | needs-class | PR2-F | OLTP targeting-mapping class |
| get_product_selection_changes | audit.audit_logs_v2 | needs-class | PR2-E | audit JSON class (action 50/51) |

**Helpers (no verdict; fold into parent):** `_fragment_bidding_strategy_type`,
`fetch_marketplace_info(__all)`, `get_campaigns_in_category__resolve_ids`,
`get_product_selection_changes__product_names`, `lookup_campaign`, `lookup_merchant`,
`*__resolve_sellers`, `*__resolve_marketplace_client`, `check_requests__{pla,display}`,
`check_display_hourly_rr__{ad_unit,hourly}`,
`get_search_query_response_rates__{pla,display,display_ad_unit}`,
`get_campaign_daily_budget__{avg_daily_budget,flexi_budget}`.
