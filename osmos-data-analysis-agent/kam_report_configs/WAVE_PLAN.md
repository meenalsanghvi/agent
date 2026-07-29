# Query-inventory batch plan — inline + external, in waves by skill

> **Superseded in part by the consolidation pass.** The per-tool 1:1 mapping this plan
> assumes ("author every real query as a report") is what produced 70 configs, 42 of them
> near-duplicates. Those are now merged into 15 reports — see `MERGE_ANALYSIS.md` and
> `MERGE_MAP.md`. The ✅/🟡/⬜ status below still records which *queries* have been ported;
> read it alongside `MERGE_MAP.md` to find which report now serves each one.
>
> **For the remaining ⬜ items: check `MERGE_MAP.md` first.** Several are already covered
> by a merged report (a different grouping of a table that is now consolidated) and need
> no new config — e.g. the RR by-dimension/hourly/store-level and search-query-request
> families. Author a new report only when the query needs a table or join set no active
> config has.

Author every real query as an **inline + external** report (per
`.claude/kam-inline-external-authoring-prompt.md`), validate with `post_external.py`.
Legend: ✅ done (inline+external) · 🟡 done class-based only (needs inline+external re-author) ·
⬜ to do · ⚙️ helper/fragment (fold into parent, not a standalone report).

**Approach flags:** `cvcpf`=converted spend inline (proven) · `audit`=JSON_EXTRACT_SCALAR inline ·
`SP`=needs `__SP_REPORTING_DB_REGION__`/`__SP_TIMEZONE__`/`__SP_MARKETPLACE_CLIENT_ID__` (de-risk first) ·
`split`=author per-branch · `suffix`=per-marketplace/region table name (SP-region/mcid candidate).

## De-risk sub-wave (do before SP-flagged tools)
Prove `__SP_REPORTING_DB_REGION__` + `__SP_TIMEZONE__` + `__SP_MARKETPLACE_CLIENT_ID__` on ONE
timezone/region query. If they resolve, the region/tz/suffix tools are inline-able (not blockers).

## Wave 1 — ROAS (flagship) ✅ DONE (5/5 green)
- ✅ check_gmv_attribution → GMV_ATTRIBUTION_REPORT (⚠️ site/organic metrics returned 0 — verify vs test-env mmf `total_sok_*` data; program side correct, ZAR-converted)
- ✅ get_daily_order_trends → DAILY_ORDER_TRENDS_REPORT (organic reconciles)
- ✅ get_merchant_breakdown → MERCHANT_ROAS_BREAKDOWN_REPORT (churned/organic-only merchants absent from program rows — INNER on cvcpf)
- ✅ get_sku_level_performance → SKU_ROAS_PERFORMANCE_REPORT (`externalRequiredFilters: [os_client_id]` — unscoped scan too heavy)
- ✅ get_target_roi → TARGET_ROI_REPORT (physical col `target_roi`)
- ⚙️ get_sku_level_performance__resolve_marketplace_client (folded)

## Wave 2 — CPC ✅ DONE (4/4 green)
- ✅ get_merchant_cpc_breakdown → MERCHANT_CPC_BREAKDOWN_REPORT (cvcpf converted; cpc=spend/clicks)
- ✅ get_campaign_subtype_cpc_breakdown → CAMPAIGN_SUBTYPE_CPC_REPORT (raw spend per source)
- ✅ get_merchant_category_cpc_comparison → MERCHANT_CATEGORY_CPC_COMPARISON_REPORT (raw spend per source; agg-vs-subtotal = 2 calls)
- ✅ get_sku_level_cpc_performance → SKU_CPC_PERFORMANCE_REPORT (`externalRequiredFilters:[os_client_id]`)
- ⚙️ 2 resolvers folded

## Wave 3 — CTR (2 done)
- 🟡 check_ctr_overall · ✅ get_merchant_ctr_breakdown · ⬜ get_sku_level_ctr_performance · ⬜ get_keyword_seller_breakdown `SP-tz` · ⬜ get_search_query_match_performance

## Wave 4 — BU ✅ MOSTLY DONE
- ✅ check_program_spend · 🟡 check_requests (pla/display) · 🟡 get_display_ad_unit_performance · 🟡 get_merchant_wallet_balance  (🟡 = class-based, re-author inline+external in cleanup)
- ✅ get_merchant_bu_breakdown → MERCHANT_BU_BREAKDOWN_REPORT (cvcpf converted)
- ✅ get_true_bu_campaign_data → TRUE_BU_CAMPAIGN_REPORT (daily budget + wallet, native currency)
- ✅ get_category_quadrant_performance → CATEGORY_QUADRANT_REPORT (converted; AVG fan-out trick)
- ✅ get_campaign_inventory_performance → CAMPAIGN_INVENTORY_REPORT (raw spend per source)
- ⬜ get_display_quadrant_performance `OLTP` · ⬜ get_display_inventory_campaigns `OLTP` (held — os_ads_db_* config-table joins)

## Wave 5 — RR (5 done)
- ✅ category · 🟡 by_page(pla/display) · 🟡 display_page_type · 🟡 by_dimension(pla/display)
- ⬜ get_merchant_rr_breakdown `cvcpf` · ⬜ get_search_query_campaigns · ⬜ get_search_query_response_rates `split` (pla `SP-tz`/display/display_ad_unit) · ⬜ get_search_query_rr_buckets `SP-tz` · ⬜ get_store_level_rr_buckets · ⬜ check_display_hourly_rr `split`(ad_unit/hourly)
- ⬜ get_category_request_volume `SP suffix` · ⬜ get_filter_presence_response_rates `SP suffix`

## Wave 6 — shared (3 done)
- ✅ page_level · ✅ problem_metrics(intake) · ✅ marketplace_directory(intake)
- ⬜ get_campaign_performance `split`(aggregated/daily) · ⬜ get_category_level_performance · ⬜ get_merchant_category_performance · ⬜ get_merchant_keyword_performance · ⬜ get_search_query_performance `SP-tz` · ⬜ get_campaigns_in_category · ⬜ get_campaign_targeted_keywords `split`(targeted/negative) · ⬜ get_campaign_targeted_networks `split`(by_campaign_id/via_ctd) · ⬜ get_campaign_product_selection `SP suffix` · ⬜ get_campaign_status_changes `audit SP-tz` · ⬜ get_product_selection_changes `audit SP-tz` · ⚙️ resolvers, _fragment_bidding_strategy_type, lookup_campaign, lookup_merchant

## Wave 7 — keyword_delivery / keyword_low_rr / irrelevancy / budget_pacing
- ⬜ check_targeted_keyword_performance_in_campaigns · ⬜ get_targeted_keyword_competition · ⬜ check_keyword_request_volume `SP-tz`
- keyword_low_rr: no SQL (composes others) — skill-only
- ⬜ get_responded_skus `SP-tz suffix`
- ✅ get_budget_delivery_mode · ⬜ get_budget_pacing_buckets · ⬜ get_campaign_daily_budget `split`(avg`SP-tz`/flexi) · ⬜ get_minute_level_cpc_data `SP-tz` · ⬜ get_minute_level_cpm_data `SP-tz` · ⬜ check_budget_changes_on_date `audit SP-tz`

## Note on the 🟡 class-based configs
The 12 `KAM_AGENT_*` class-based configs are functionally validated but NOT external-exposed
(external fields need `externalColumnName` on columns, awkward on class-inflated columns). Plan:
re-author them inline+external within their skill's wave (reuse the validated SQL logic).
