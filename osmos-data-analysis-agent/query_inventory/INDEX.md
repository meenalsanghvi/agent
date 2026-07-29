# INDEX — extracted query inventory

Generated from the `.sql` headers. **76 queries** + 1 shared SQL fragment, across **45 distinct BigQuery tables**, extracted from the ADK agent's tool functions.

See `README.md` for the file format and the rationale.

## Counts by agent

| Agent | Source file | Queries |
|---|---|---|
| ROAS / ROI | `roi_analysis_tools.py` | 6 |
| CPC | `cpc_analysis_tools.py` | 6 |
| CTR | `ctr_analysis_tools.py` | 5 |
| Budget Utilisation (BU) | `bu_analysis_tools.py` | 11 |
| Response Rate (RR) | `rr_analysis_tools.py` | 15 |
| Budget Pacing | `budget_pacing_tools.py` | 7 |
| Keyword Delivery | `keyword_delivery_tools.py` | 3 |
| Irrelevancy | `irrelevancy_tools.py` | 1 |
| Keyword Low-RR | `(none — composes other tools)` | 0 |
| Shared (common_tools / state_tools) | `common_tools.py + state_tools.py` | 22 |
| **Total** |  | **76** |

Region-specific queries (`reporting_{region}`): 2 — `get_category_request_volume.sql`, `get_filter_presence_response_rates.sql`

Timezone-aware queries (`DATE(TIMESTAMP(...), tz)`): 14 — `check_budget_changes_on_date.sql`, `check_keyword_request_volume.sql`, `get_campaign_daily_budget__avg_daily_budget.sql`, `get_campaign_status_changes.sql`, `get_category_request_volume.sql`, `get_filter_presence_response_rates.sql`, `get_keyword_seller_breakdown.sql`, `get_minute_level_cpc_data.sql`, `get_minute_level_cpm_data.sql`, `get_product_selection_changes.sql`, `get_responded_skus.sql`, `get_search_query_performance.sql`, `get_search_query_response_rates__pla.sql`, `get_search_query_rr_buckets.sql`

## ROAS / ROI  ·  `roi_analysis_tools.py`

| Query file | Src line | Proposed KAM reportType | What it returns |
|---|---|---|---|
| `check_gmv_attribution.sql` | 154 | KAM_AGENT_ROAS_GMV_ATTRIBUTION | Marketplace-level PROGRAM (ad-attributed) vs SITE (organic) funnel for ONE period. Called once per period; comparison mode runs it for current + baseline. |
| `get_daily_order_trends.sql` | 285 | KAM_AGENT_ROAS_DAILY_ORDER_TRENDS | Date-level PROGRAM (ad-attributed) vs SITE (organic) funnel for ONE period, one row per date. Called once per period; comparison runs it for current + baseline. |
| `get_merchant_breakdown.sql` | 415 | KAM_AGENT_ROAS_MERCHANT_BREAKDOWN | Merchant-level PROGRAM (ad-attributed) + SITE (organic) funnel for ONE period, one row per merchant. Same query string is issued once per period; comparison … |
| `get_sku_level_performance.sql` | 736 | KAM_AGENT_ROAS_SKU_PERFORMANCE | SKU-level PROGRAM (PLA performance campaigns only) + SITE (organic) funnel for ONE period, one row per SKU/merchant. Same query issued once per period; compa… |
| `get_sku_level_performance__resolve_marketplace_client.sql` | 712 | TBD | Resolve the marketplace_client_id for an agency (the marketplace's own client record). Used to scope/join the organic SKU facts in the main SKU query. |
| `get_target_roi.sql` | 120 | KAM_AGENT_ROAS_TARGET_ROI | Marketplace target ROI benchmark for one agency (single scalar lookup). |

## CPC  ·  `cpc_analysis_tools.py`

| Query file | Src line | Proposed KAM reportType | What it returns |
|---|---|---|---|
| `get_campaign_subtype_cpc_breakdown.sql` | 334 | TBD | Marketplace-level PLA campaign-subtype BUCKETS (os_ads_search vs smart_shopping vs ...) for ONE period: campaign count, spend, clicks, impressions, program G… |
| `get_merchant_category_cpc_comparison.sql` | 493 | TBD | Per-category (l1/l2/l3) marketplace aggregate vs the analyzed merchant(s) subtotal for ONE period: category & merchant cost/clicks/GMV/orders (+ merchant vie… |
| `get_merchant_category_cpc_comparison__resolve_sellers.sql` | 477 | TBD | Resolve the given os_client_ids to their seller_ids (merchant_id used in the category facts table). Runs only when client_ids are passed and seller_ids are not. |
| `get_merchant_cpc_breakdown.sql` | 76 | TBD | Merchant-level PROGRAM (ad) vs SITE (organic) funnel for ONE period, one row per merchant (spend, clicks, impressions, program & site viewproducts/add2carts/… |
| `get_sku_level_cpc_performance.sql` | 644 | TBD | SKU-level PROGRAM (PLA performance campaigns: os_ads_search, smart_shopping) funnel for ONE period joined to the SITE/organic SKU funnel: per SKU spend, impr… |
| `get_sku_level_cpc_performance__resolve_marketplace_client.sql` | 623 | TBD | Look up the marketplace's own client record (marketplace_client_id) for the agency, used to attach the SITE/organic SKU funnel in the main SKU query. |

## CTR  ·  `ctr_analysis_tools.py`

| Query file | Src line | Proposed KAM reportType | What it returns |
|---|---|---|---|
| `check_ctr_overall.sql` | 80 | TBD | Marketplace-level CTR for ONE period, decomposed into raw clicks / impressions / spend (CTR itself computed in Python). Optional per-merchant filter. Called … |
| `get_keyword_seller_breakdown.sql` | 777 | TBD | Per-(search_query x seller) impressions / clicks / spend / CTR (SQL) plus auto vs manual match-type impression split, from os_ads_search_query_performance_re… |
| `get_merchant_ctr_breakdown.sql` | 223 | TBD | Merchant-level clicks / impressions / spend / CTR / CPC / CPM for ONE period (CTR/CPC/CPM computed in SQL). Called once per period; comparison mode runs it f… |
| `get_search_query_match_performance.sql` | 1027 | TBD | Per-(search_query x matched_keyword x match_type) performance inside specific advertiser campaign(s): spend, impressions, clicks, CTR, CPC, CPM, top-of-searc… |
| `get_sku_level_ctr_performance.sql` | 561 | TBD | SKU-level raw spend / impressions / clicks per product for PLA performance campaigns only (os_ads_search, smart_shopping), scoped to given os_client_ids. Cal… |

## Budget Utilisation (BU)  ·  `bu_analysis_tools.py`

| Query file | Src line | Proposed KAM reportType | What it returns |
|---|---|---|---|
| `check_program_spend.sql` | 44 | TBD | Total program spend (marketplace currency) for ONE date range, single scalar. Spend stable does NOT imply BU stable. |
| `check_requests__display.sql` | 171 | TBD | Daily Display ad request / non-zero-response volume and response % for ONE date range (per-day rows). |
| `check_requests__pla.sql` | 128 | TBD | Daily PLA ad request / non-zero-response volume and response % for ONE date range (per-day rows). |
| `get_campaign_inventory_performance.sql` | 1445 | TBD | Inventory/ad-unit slots selected by Display campaigns (filtered by client_id(s) and/or campaign_group_id(s)) for ONE date range: spend, impressions, clicks, … |
| `get_category_quadrant_performance.sql` | 307 | TBD | PLA category-level (L1/L2/L3) quadrant for ONE date range: avg request count, response rate, spend, daily budget, BU%, unique campaigns/merchants. |
| `get_display_ad_unit_performance.sql` | 1125 | TBD | Display ad-unit-level breakdown for ONE date range: requests, responses, RR, impressions, clicks, CTR, cost, CPM, ROI, impression/response ratio, funnel events. |
| `get_display_inventory_campaigns.sql` | 1216 | TBD | Campaigns running under a specific Display inventory slot (ad unit, optional page type) for ONE date range: merchant, campaign-group name/type/status/subtype… |
| `get_display_quadrant_performance.sql` | 990 | TBD | Display inventory-level (page_type + ad_unit) quadrant for ONE date range: avg request count, response rate, impression/response ratio, spend, BU%, unique ca… |
| `get_merchant_bu_breakdown.sql` | 451 | TBD | Per-merchant spend / clicks / impressions for ONE period (spend > 0). Called once per period; comparison mode runs it for current + baseline. |
| `get_merchant_wallet_balance.sql` | 900 | TBD | Per-merchant remaining wallet balance (remaining_budget_amount_usd -> marketplace currency) for the marketplace. Point-in-time; no date range. |
| `get_true_bu_campaign_data.sql` | 655 | TBD | Campaign-level budget vs spend vs wallet-balance + BU% for ONE period (daily_budget = most-recent-day budget, total_budget = period sum). Called once per per… |

## Response Rate (RR)  ·  `rr_analysis_tools.py`

| Query file | Src line | Proposed KAM reportType | What it returns |
|---|---|---|---|
| `check_display_hourly_rr__ad_unit.sql` | 1697 | TBD | Display requests/responses aggregated per ad_unit for ONE period, to flag ad units with zero responses (no active campaigns). Single call alongside the hourl… |
| `check_display_hourly_rr__hourly.sql` | 1684 | TBD | Display requests/responses aggregated per hour-of-day (from date_hour) for ONE period, to surface low-activity hours dragging down RR. Single call. |
| `check_display_page_type_rr.sql` | 1611 | TBD | Display ad response rate broken down by page type for ONE period. Called once per period; comparison mode runs it for current + baseline. |
| `check_response_rate_by_page.sql` | 79 | TBD | Response rate (responses/requests) broken down by page type for ONE period. Called once per period; comparison mode runs it for current + baseline. |
| `get_category_request_volume.sql` | 586 | TBD | Raw request volume (COUNT of rid) by category (l1/l2/l3) from the region-specific request log for ONE period. Called once per period; comparison mode runs it… |
| `get_category_response_rates.sql` | 276 | TBD | Category-level (l1/l2/l3) request/response/RR on non-search pages for ONE period, from the aggregated filtered_level_report. Called once per period; comparis… |
| `get_filter_presence_response_rates.sql` | 1015 | TBD | Single-scan conditional aggregation over the raw region-specific request log: present vs absent request/response counts for each client-sent filter over a re… |
| `get_merchant_rr_breakdown.sql` | 398 | TBD | Per-merchant spend/clicks/impressions for ONE period (merchant × currency-converted). One query literal; called once (single period) or twice (comparison: cu… |
| `get_response_rate_by_dimension.sql` | 847 | TBD | Request/response/RR grouped by one or more allowed dimension columns (network, store_id, page_type, categories, ad_unit, ...) for ONE period. Called once per… |
| `get_search_query_campaigns.sql` | 157 | TBD | Distinct campaigns (+ current effective_status) responding to a set of search queries for ONE period, for RR-drop root-cause. Called once per period; compari… |
| `get_search_query_response_rates__display.sql` | 1295 | TBD | Keyword-level (filter_keywords) request/response/RR for Display (filtered_level_performance_facts) for ONE period. Called once per period; comparison mode ru… |
| `get_search_query_response_rates__display_ad_unit.sql` | 1399 | TBD | Follow-up query (Display only): keyword x ad_unit request/response/RR for the keywords surfaced by the main Display query. Single call after the main Display… |
| `get_search_query_response_rates__pla.sql` | 1318 | TBD | Keyword-level request/response/RR on search pages for PLA (timezone-aware search query request report) for ONE period. Called once per period; comparison mod… |
| `get_search_query_rr_buckets.sql` | 1463 | TBD | Per-keyword request/response totals on search pages (PLA only, timezone-aware) for ONE period, filtered to keywords with >= min_requests, for Pareto + zero/p… |
| `get_store_level_rr_buckets.sql` | 1139 | TBD | Store × category × day × hour request/response grain (single period) used to bucket store-hours into zero/partial/full response and compute an eligibility-ad… |

## Budget Pacing  ·  `budget_pacing_tools.py`

| Query file | Src line | Proposed KAM reportType | What it returns |
|---|---|---|---|
| `check_budget_changes_on_date.sql` | 419 | TBD | Audit-log lookup of daily-budget change events (action_type_id 17) for a campaign within a single local day, with old/new value, currency, campaign name, and… |
| `get_budget_delivery_mode.sql` | 486 | TBD | Budget delivery (pacing) mode — ACCELERATED vs STANDARD — for one or more PLA campaigns. |
| `get_budget_pacing_buckets.sql` | 187 | TBD | Fetch the raw budget-pacing JSON (cumulative spend % targets by time-of-day) for a marketplace on a given date. |
| `get_campaign_daily_budget__avg_daily_budget.sql` | 283 | TBD | Derived daily budget for a campaign on a date when the marketplace has avgDailyBudgetEnabled. Table date is UTC, so the local date is converted to UTC. Budge… |
| `get_campaign_daily_budget__flexi_budget.sql` | 313 | TBD | Flexi daily budget for a campaign on a date (when avgDailyBudget is disabled): campaign daily budget capped by the merchant wallet's remaining balance. Budge… |
| `get_minute_level_cpc_data.sql` | 40 | TBD | Per-minute clicks and spend for CPC-strategy PLA campaigns on a single day, split by campaign and page_type (SEARCH vs NON-SEARCH). Spend converted USD -> ma… |
| `get_minute_level_cpm_data.sql` | 119 | TBD | Per-minute impressions and spend for CPM-strategy PLA campaigns on a single day, grouped by marketing_campaign_group_id. Spend converted USD -> marketplace c… |

## Keyword Delivery  ·  `keyword_delivery_tools.py`

| Query file | Src line | Proposed KAM reportType | What it returns |
|---|---|---|---|
| `check_keyword_request_volume.sql` | 47 | TBD | Per-keyword request volume over the trailing 7-day window for a marketplace, used to decide if a keyword has enough demand (>100 requests) to warrant a categ… |
| `check_targeted_keyword_performance_in_campaigns.sql` | 290 | TBD | Targeted-keyword performance (spend, impressions, clicks, CTR, CPC, CPM, attributed sales, ROI) for specific advertiser client_ids + marketing_campaign_ids o… |
| `get_targeted_keyword_competition.sql` | 435 | TBD | Per-campaign competition on a targeted keyword across the whole marketplace for ONE period: every campaign that served the keyword with spend, impressions, c… |

## Irrelevancy  ·  `irrelevancy_tools.py`

| Query file | Src line | Proposed KAM reportType | What it returns |
|---|---|---|---|
| `get_responded_skus.sql` | 69 | TBD | For SEARCH-page search queries, list the SKUs that were responded/served (product name, brand, e_product_type category, serving cache_type/algorithm) with sp… |

## Keyword Low-RR

No SQL of its own — composes tools from `common_tools`, `keyword_delivery_tools`, `rr_analysis_tools`, `bu_analysis_tools`.

## Shared (common_tools / state_tools)  ·  `common_tools.py + state_tools.py`

| Query file | Src line | Proposed KAM reportType | What it returns |
|---|---|---|---|
| `_fragment_bidding_strategy_type.sql` _(fragment)_ | 1855 | — | Large CASE expression that derives campaign_group_bidding_strategy_type |
| `fetch_marketplace_info.sql` | 23 | TBD | Look up active 'monetize' marketplaces whose name matches a user-supplied substring (case-insensitive LIKE), returning agency/region/currency/timezone contex… |
| `fetch_marketplace_info__all.sql` | 38 | TBD | Fuzzy-fallback: fetch ALL active 'monetize' marketplaces (name + agency/region/currency/timezone context) so the app can rapidfuzz-match the user's input whe… |
| `get_campaign_performance__aggregated.sql` | 714 | TBD | Campaign-group performance aggregated over a period: per campaign-group impressions, clicks, cost, orders, revenue (currency-converted), plus derived group t… |
| `get_campaign_performance__daily.sql` | 644 | TBD | Date-level (daily) campaign-group performance for SPECIFIC campaigns in one period: per date+campaign impressions, clicks, cost, orders, revenue (currency-co… |
| `get_campaign_product_selection.sql` | 492 | TBD | Currently-active (in-stock) products selected in a specific campaign: merchant_id, product_id, name, availability, brand, category L1/L2/L3. Single call. Per… |
| `get_campaign_status_changes.sql` | 244 | TBD | Campaign status-change audit log (action_type_id=16) for specific merchants/campaigns in a period: old_status -> new_status, who + when. Single call. |
| `get_campaign_targeted_keywords__negative.sql` | 1435 | TBD | Negative keywords (is_negative=1, is_deleted=0) explicitly excluded by a SEARCH campaign: text only. Single call. (Paired with the targeted-keyword query.) |
| `get_campaign_targeted_keywords__targeted.sql` | 1424 | TBD | Active TARGETED keywords (is_negative=0, is_deleted=0) a SEARCH campaign bids on: text + merchant-set bidding_value. Single call. (Paired with the negative-k… |
| `get_campaign_targeted_networks__by_campaign_id.sql` | 1520 | TBD | Targeted NETWORK mappings for a campaign, filtered DIRECTLY on the internal numeric campaign_id (target_type='NETWORK', is_deleted=0). Single call. Used when… |
| `get_campaign_targeted_networks__via_ctd.sql` | 1533 | TBD | Targeted NETWORK mappings for a campaign resolved through campaign_tagging_data when the caller holds a non-campaign_id key (marketing_campaign_id / campaign… |
| `get_campaigns_in_category.sql` | 1868 | TBD | PLA campaigns competing in a category for one period, each with category-level spend/cpc/cpm, daily budget, campaign_subtype and derived bid model (bidding_s… |
| `get_campaigns_in_category__resolve_ids.sql` | 1820 | TBD | Resolve any marketing_campaign_group_ids passed in marketing_campaign_ids to their marketing_campaign_ids, so the main category query can filter uniformly. S… |
| `get_category_level_performance.sql` | 1231 | TBD | PLA category-level (L1/L2/L3) raw additive metrics for one period: spend, impressions, clicks, program orders/revenue/viewproducts/add-to-carts, site viewpro… |
| `get_merchant_category_performance.sql` | 2689 | TBD | A merchant's PLA performance (os_ads_search, smart_shopping) broken down by product CATEGORY (e_product_type) × campaign for one period: spend, impressions, … |
| `get_merchant_keyword_performance.sql` | 2504 | TBD | A merchant's TARGETED keywords across all its PLA performance campaigns (os_ads_search, smart_shopping) for one period: keyword×campaign spend, impressions, … |
| `get_page_level_performance.sql` | 1585 | TBD | PLA page-type (search/category/product/...) raw aggregates for one period: requests, responses, impressions, clicks, cost (currency-converted). Called once p… |
| `get_problem_metrics.sql` | 1038 | TBD | Auto-flagged weekly trend metrics for a marketplace/week from the trend-analysis report: metric, old/new value, change_perc, severity, primary_reason. Single… |
| `get_product_selection_changes.sql` | 353 | TBD | Product selection audit log (action_type_id 50=added / 51=removed) for specific merchants/campaigns in a period: sku_id, action, who + when. Single call. (SK… |
| `get_product_selection_changes__product_names.sql` | 399 | TBD | Batch SKU -> product_name (e_name) lookup for the (client_id, sku_id) pairs surfaced by get_product_selection_changes. Single call, follow-up to the main aud… |
| `get_search_query_performance.sql` | 2223 | TBD | PLA search-query (what users TYPED) performance for one period from os_ads_search_query_performance_report: impressions, clicks, spend, ctr, and AUTO-vs-manu… |
| `lookup_campaign.sql` | 141 | TBD | Resolve one campaign ID of a KNOWN type to all 4 ID types plus client_id, campaign_name (alias), type/subtype, bidding_strategy and status. Called once per r… |
| `lookup_merchant.sql` | 60 | TBD | Resolve a merchant within a marketplace by client_id (os_client_id) OR merchant_id (seller_id); returns merchant_id, client_id, merchant_name. Single call. |

## Table → query cross-reference

Which extracted queries touch each BigQuery table — the starting point for mapping tables to KAM registry classes. Sorted by fan-in.

| BigQuery table (prj-onlinesales-prod-01.*) | #queries | Queries |
|---|---|---|
| `reporting.marketplace_clients` | 29 | `check_ctr_overall.sql`, `check_gmv_attribution.sql`, `check_program_spend.sql`, `check_requests__display.sql`, `check_requests__pla.sql`, `check_response_rate_by_page.sql`, `check_targeted_keyword_performance_in_campaigns.sql`, `fetch_marketplace_info.sql`, `fetch_marketplace_info__all.sql`, `ge… |
| `reporting.static_currency_conversion` | 25 | `check_ctr_overall.sql`, `check_gmv_attribution.sql`, `check_program_spend.sql`, `check_targeted_keyword_performance_in_campaigns.sql`, `get_campaign_daily_budget__flexi_budget.sql`, `get_campaign_performance__aggregated.sql`, `get_campaign_performance__daily.sql`, `get_category_quadrant_performa… |
| `reporting.campaign_tagging_data` | 21 | `check_targeted_keyword_performance_in_campaigns.sql`, `get_campaign_inventory_performance.sql`, `get_campaign_performance__aggregated.sql`, `get_campaign_performance__daily.sql`, `get_campaign_product_selection.sql`, `get_campaign_subtype_cpc_breakdown.sql`, `get_campaign_targeted_networks__via_… |
| `reporting.clients` | 21 | `check_ctr_overall.sql`, `check_gmv_attribution.sql`, `check_program_spend.sql`, `get_campaign_daily_budget__flexi_budget.sql`, `get_campaign_subtype_cpc_breakdown.sql`, `get_category_level_performance.sql`, `get_daily_order_trends.sql`, `get_keyword_seller_breakdown.sql`, `get_merchant_breakdown… |
| `reporting.marketing_campaign_dimensions` | 18 | `check_targeted_keyword_performance_in_campaigns.sql`, `get_budget_delivery_mode.sql`, `get_campaign_daily_budget__flexi_budget.sql`, `get_campaign_performance__aggregated.sql`, `get_campaign_performance__daily.sql`, `get_campaigns_in_category.sql`, `get_display_inventory_campaigns.sql`, `get_mer… |
| `reporting.agencies` | 11 | `fetch_marketplace_info.sql`, `fetch_marketplace_info__all.sql`, `get_campaigns_in_category.sql`, `get_category_quadrant_performance.sql`, `get_display_inventory_campaigns.sql`, `get_display_quadrant_performance.sql`, `get_search_query_match_performance.sql`, `get_sku_level_cpc_performance__resol… |
| `reporting.marketing_campaign_group_dimensions` | 11 | `get_campaign_inventory_performance.sql`, `get_campaign_performance__aggregated.sql`, `get_campaign_performance__daily.sql`, `get_campaign_subtype_cpc_breakdown.sql`, `get_campaigns_in_category.sql`, `get_display_inventory_campaigns.sql`, `get_merchant_category_performance.sql`, `get_merchant_key… |
| `reporting.monetize_merchant_dimensions` | 11 | `get_campaign_performance__aggregated.sql`, `get_campaign_performance__daily.sql`, `get_campaigns_in_category.sql`, `get_category_level_performance.sql`, `get_display_inventory_campaigns.sql`, `get_merchant_breakdown.sql`, `get_merchant_bu_breakdown.sql`, `get_merchant_cpc_breakdown.sql`, `get_me… |
| `reporting.client_vendor_channel_performance_facts` | 9 | `check_ctr_overall.sql`, `check_gmv_attribution.sql`, `check_program_spend.sql`, `get_daily_order_trends.sql`, `get_merchant_breakdown.sql`, `get_merchant_bu_breakdown.sql`, `get_merchant_cpc_breakdown.sql`, `get_merchant_ctr_breakdown.sql`, `get_merchant_rr_breakdown.sql` |
| `reporting.os_display_ads_filtered_level_performance_facts` | 7 | `check_display_hourly_rr__ad_unit.sql`, `check_display_hourly_rr__hourly.sql`, `check_display_page_type_rr.sql`, `get_response_rate_by_dimension.sql`, `get_search_query_response_rates__display.sql`, `get_search_query_response_rates__display_ad_unit.sql`, `get_store_level_rr_buckets.sql` |
| `reporting.merchant_merchandise_product_dimensions` | 5 | `get_merchant_category_performance.sql`, `get_product_selection_changes__product_names.sql`, `get_sku_level_cpc_performance.sql`, `get_sku_level_ctr_performance.sql`, `get_sku_level_performance.sql` |
| `reporting.monetize_merchant_facts` | 4 | `check_gmv_attribution.sql`, `get_daily_order_trends.sql`, `get_merchant_breakdown.sql`, `get_merchant_cpc_breakdown.sql` |
| `reporting.os_ads_search_query_performance_report` | 4 | `get_keyword_seller_breakdown.sql`, `get_search_query_campaigns.sql`, `get_search_query_match_performance.sql`, `get_search_query_performance.sql` |
| `reporting.os_product_ads_device_product_facts` | 4 | `get_merchant_category_performance.sql`, `get_sku_level_cpc_performance.sql`, `get_sku_level_ctr_performance.sql`, `get_sku_level_performance.sql` |
| `audit.audit_logs_v2` | 3 | `check_budget_changes_on_date.sql`, `get_campaign_status_changes.sql`, `get_product_selection_changes.sql` |
| `reporting.campaign_performance_facts` | 3 | `get_campaign_performance__aggregated.sql`, `get_campaign_performance__daily.sql`, `get_campaign_subtype_cpc_breakdown.sql` |
| `reporting.os_ads_keyword_performance_report` | 3 | `check_targeted_keyword_performance_in_campaigns.sql`, `get_merchant_keyword_performance.sql`, `get_targeted_keyword_competition.sql` |
| `reporting.os_display_ads_ad_unit_facts` | 3 | `check_requests__display.sql`, `check_response_rate_by_page.sql`, `get_display_ad_unit_performance.sql` |
| `reporting.os_product_ads_filtered_level_report` | 3 | `get_category_response_rates.sql`, `get_response_rate_by_dimension.sql`, `get_store_level_rr_buckets.sql` |
| `reporting.os_product_ads_page_name_performance_facts` | 3 | `check_requests__pla.sql`, `check_response_rate_by_page.sql`, `get_page_level_performance.sql` |
| `reporting.os_product_ads_search_query_request_report` | 3 | `check_keyword_request_volume.sql`, `get_search_query_response_rates__pla.sql`, `get_search_query_rr_buckets.sql` |
| `reporting.client_budget_snapshot` | 2 | `get_campaign_daily_budget__flexi_budget.sql`, `get_true_bu_campaign_data.sql` |
| `reporting.marketing_campaign_dimensions_daily` | 2 | `get_campaign_daily_budget__flexi_budget.sql`, `get_true_bu_campaign_data.sql` |
| `reporting.marketplace_category_level_performance_facts_v2` | 2 | `get_category_level_performance.sql`, `get_merchant_category_cpc_comparison.sql` |
| `reporting.oltp_merchandise_product_dimensions_{marketplace_client_id}` | 2 | `get_campaign_product_selection.sql`, `get_responded_skus.sql` |
| `reporting.os_ads_db_campaign_inventory_configurations` | 2 | `get_display_inventory_campaigns.sql`, `get_display_quadrant_performance.sql` |
| `reporting.os_ads_db_campaign_level_keywords` | 2 | `get_campaign_targeted_keywords__negative.sql`, `get_campaign_targeted_keywords__targeted.sql` |
| `reporting.os_ads_db_campaign_targeting_mapping` | 2 | `get_campaign_targeted_networks__by_campaign_id.sql`, `get_campaign_targeted_networks__via_ctd.sql` |
| `reporting.os_ads_db_status_types` | 2 | `get_display_inventory_campaigns.sql`, `get_display_quadrant_performance.sql` |
| `reporting.os_display_ads_ad_targeting_report` | 2 | `get_display_inventory_campaigns.sql`, `get_display_quadrant_performance.sql` |
| `reporting.os_merchandise_product_performance_facts` | 2 | `get_sku_level_cpc_performance.sql`, `get_sku_level_performance.sql` |
| `reporting.os_product_ads_campaign_category_report_pla` | 2 | `get_campaigns_in_category.sql`, `get_category_quadrant_performance.sql` |
| `reporting.os_product_ads_response_to_impressions_mapping` | 2 | `get_minute_level_cpm_data.sql`, `get_responded_skus.sql` |
| `reporting.brand_ads_dimensions` | 1 | `get_campaign_inventory_performance.sql` |
| `reporting.os_ads_campaign_avg_daily_budget_projections` | 1 | `get_campaign_daily_budget__avg_daily_budget.sql` |
| `reporting.os_ads_db_campaign_types` | 1 | `get_display_quadrant_performance.sql` |
| `reporting.os_ads_db_campaigns` | 1 | `get_display_quadrant_performance.sql` |
| `reporting.os_ads_marketplace_budget_pacing_configurations` | 1 | `get_budget_pacing_buckets.sql` |
| `reporting.os_ads_performance_trend_analysis_report` | 1 | `get_problem_metrics.sql` |
| `reporting.os_brand_ads_network_level_facts` | 1 | `get_campaign_inventory_performance.sql` |
| `reporting.os_display_ads_daily_quadrant_report` | 1 | `get_display_quadrant_performance.sql` |
| `reporting.os_marketplace_search_query_performance_facts` | 1 | `get_search_query_match_performance.sql` |
| `reporting.os_product_ads_daily_category_quadrant_report_pla` | 1 | `get_category_quadrant_performance.sql` |
| `reporting.os_product_ads_product_selection_{marketplace_client_id}` | 1 | `get_campaign_product_selection.sql` |
| `reporting.os_product_ads_response_to_clicks_mapping` | 1 | `get_minute_level_cpc_data.sql` |
