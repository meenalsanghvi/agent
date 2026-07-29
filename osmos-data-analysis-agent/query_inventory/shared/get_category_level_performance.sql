-- =====================================================================
-- id:                       shared.get_category_level_performance
-- source:                   tools/common_tools.py:1231  (fn get_category_level_performance -> _cat_query)
-- agent:                    shared
-- description:              PLA category-level (L1/L2/L3) raw additive metrics for one period: spend, impressions, clicks, program orders/revenue/viewproducts/add-to-carts, site viewproducts/add-to-carts/orders/revenue. Optional per-merchant and/or per-date breakdown. Called once per period; comparison mode runs it for current + baseline.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {agency_id}  str  -> __AGENCY_ID__
--   {sd}         date -> __START_DATE_1__   (baseline call -> __START_DATE_2__)
--   {ed}         date -> __END_DATE_1__     (baseline call -> __END_DATE_2__)
--   {top_n}      int  -> __LIMIT__
-- injected_fragments:                                  (SQL spliced in by a helper/branch)
--   {dim_select} / {dim_group}  <- category CASE columns (see _CAT_L1/_CAT_L2/_CAT_L3 below) at the
--                                  requested level, plus (if group_by_merchant) f.merchant_id,
--                                  mmd.merchant_name, c.client_id AS os_client_id, plus (if group_by_date) f.date
--   _CAT_L1 = "CASE WHEN f.category_l1 IS NOT NULL AND f.category_l1 != '' AND LOWER(f.category_l1) != 'na' THEN f.category_l1 ELSE 'Unknown' END"
--   _CAT_L2 = "CASE WHEN f.category_l2 IS NOT NULL AND f.category_l2 != '' AND LOWER(f.category_l2) != 'na' THEN f.category_l2 ELSE '-' END"
--   _CAT_L3 = "CASE WHEN f.category_l3 IS NOT NULL AND f.category_l3 != '' AND LOWER(f.category_l3) != 'na' THEN f.category_l3 ELSE '-' END"
--   {joins}          <- merchant JOINs (monetize_merchant_dimensions + clients), present when group_by_merchant OR client_ids set (else empty)
--   {extra_metrics}  <- ",\n COUNT(DISTINCT f.merchant_id) AS unique_merchants" (only when NOT group_by_merchant)
--   {cat_filters}    <- "AND LOWER(f.category_lN) = LOWER('{value}')" per provided level filter
--   {merchant_filters} <- client_ids -> "AND c.client_id IN (...)"; else seller_ids -> "AND f.merchant_id IN (...)"
-- tables:
--   reporting.marketplace_category_level_performance_facts_v2
--   reporting.monetize_merchant_dimensions   (only when {joins} active)
--   reporting.clients                         (only when {joins} active)
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          called once per period (current + baseline)
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   cpc = spend / clicks
--   cpm = spend * 1000 / impressions
--   ctr = clicks / impressions * 100
--   roi = program_revenue / spend
--   -- comparison mode (merge on category level keys + merchant + date):
--   status            = active_both | new | churned   (from spend_current>0 / spend_baseline>0)
--   spend_change / cpc_change / ctr_change / roi_change = current - baseline
--   spend_share_current_pct / spend_share_baseline_pct = spend / total_spend * 100
--   contribution_to_spend_change_pct       = (cur.spend - base.spend) / total_spend_delta * 100
--   contribution_to_clicks_change_pct      = (cur.clicks - base.clicks) / total_clicks_delta * 100
--   contribution_to_impressions_change_pct = (cur.impr - base.impr) / total_impr_delta * 100
--   summary.current_total_spend / baseline_total_spend / total_spend_change
-- =====================================================================

    SELECT
        {dim_select},
        COALESCE(SUM(f.pla_cost), 0) AS spend,
        COALESCE(SUM(f.pla_impressions), 0) AS impressions,
        COALESCE(SUM(f.pla_clicks), 0) AS clicks,
        COALESCE(SUM(f.program_per_click_timestamp_conversions), 0) AS program_orders,
        COALESCE(SUM(f.program_per_click_timestamp_sales), 0) AS program_revenue,
        COALESCE(SUM(f.program_per_click_timestamp_viewproduct), 0) AS program_viewproducts,
        COALESCE(SUM(f.program_per_click_timestamp_add_to_cart), 0) AS program_add_to_carts,
        COALESCE(SUM(f.site_viewproducts), 0) AS site_viewproducts,
        COALESCE(SUM(f.site_add2carts), 0) AS site_add_to_carts,
        COALESCE(SUM(f.site_orders), 0) AS site_orders,
        COALESCE(SUM(f.site_revenue), 0) AS site_revenue{extra_metrics}
    FROM `prj-onlinesales-prod-01.reporting.marketplace_category_level_performance_facts_v2` f{joins}
    WHERE f.agency_id = '{agency_id}'
        AND f.date >= '{sd}' AND f.date <= '{ed}'{cat_filters}{merchant_filters}
    GROUP BY
        {dim_group}
    ORDER BY spend DESC
    LIMIT {top_n}
