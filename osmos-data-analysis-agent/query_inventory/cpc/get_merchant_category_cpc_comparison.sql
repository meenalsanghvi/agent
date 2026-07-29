-- =====================================================================
-- id:                       cpc.get_merchant_category_cpc_comparison
-- source:                   tools/cpc_analysis_tools.py:493  (fn get_merchant_category_cpc_comparison -> _cat_query)
-- agent:                    cpc
-- description:              Per-category (l1/l2/l3) marketplace aggregate vs the analyzed merchant(s) subtotal for ONE period: category & merchant cost/clicks/GMV/orders (+ merchant views), for PLA. Called once per period; comparison mode runs it for current + baseline.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {agency_id}   str   -> __AGENCY_ID__
--   {sd}          date  -> __START_DATE_1__   (baseline call -> __START_DATE_2__)
--   {ed}          date  -> __END_DATE_1__     (baseline call -> __END_DATE_2__)
-- injected_fragments:                                  (SQL spliced in by a helper)
--   {cat_expr}   <- built from category_level; cat_col = category_l1 | category_l2 | category_l3
--                  "CASE WHEN {cat_col} IS NOT NULL AND {cat_col} != '' AND LOWER({cat_col}) != 'na' THEN {cat_col} ELSE 'Unknown' END"
--   {seller_in}  <- resolved seller_ids: ", ".join("'{s}'" ...)  ->  "'s1', 's2', ..."
-- tables:
--   reporting.marketplace_category_level_performance_facts_v2
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          called once per period (current + baseline) — required
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   merch_cpc  = merch_cost / merch_clicks         (current & baseline)
--   merch_roi  = merch_gmv / merch_cost            (current & baseline)
--   merch_cvr  = merch_orders / merch_views * 100  (current & baseline)
--   cat_cpc    = cat_cost / cat_clicks             (current & baseline)
--   cat_roi    = cat_gmv / cat_cost                (current & baseline)
--   merch_cpc_change = merch_cpc_cur - merch_cpc_base
--   merch_roi_change = merch_roi_cur - merch_roi_base ; merch_roi_change_pct = pct_change
--   cat_cpc_change   = cat_cpc_cur - cat_cpc_base ; cat_cpc_change_pct / cat_roi_change
--   gmv_share_current_pct    = merch_gmv / cat_gmv * 100      (current & baseline)
--   spend_share_current_pct  = merch_cost / cat_cost * 100    (current & baseline)
--   clicks_share_current_pct = merch_clicks / cat_clicks * 100 (current & baseline)
--   high_contributor = gmv_share_current_pct >= 30.0
--   roi_held         = merch_roi_change_pct is None OR >= -10
--   cat_cpc_dropped  = cat_cpc_change < 0
--   verdict = merchant_cpc_concern (not roi_held) | cpc_benign (high_contributor) | competition_reduced (cat_cpc_dropped) | inconclusive
--   (top_categories selected by merch_gmv_cur desc, filtered merch_gmv_cur > 0)
-- =====================================================================

        SELECT
            {cat_expr} AS category,
            COUNT(DISTINCT merchant_id) AS cat_merchants,
            COALESCE(SUM(pla_cost), 0) AS cat_cost,
            COALESCE(SUM(pla_clicks), 0) AS cat_clicks,
            COALESCE(SUM(program_per_click_timestamp_sales), 0) AS cat_gmv,
            COALESCE(SUM(program_per_click_timestamp_conversions), 0) AS cat_orders,
            COALESCE(SUM(CASE WHEN merchant_id IN ({seller_in}) THEN pla_cost ELSE 0 END), 0) AS merch_cost,
            COALESCE(SUM(CASE WHEN merchant_id IN ({seller_in}) THEN pla_clicks ELSE 0 END), 0) AS merch_clicks,
            COALESCE(SUM(CASE WHEN merchant_id IN ({seller_in}) THEN program_per_click_timestamp_sales ELSE 0 END), 0) AS merch_gmv,
            COALESCE(SUM(CASE WHEN merchant_id IN ({seller_in}) THEN program_per_click_timestamp_conversions ELSE 0 END), 0) AS merch_orders,
            COALESCE(SUM(CASE WHEN merchant_id IN ({seller_in}) THEN program_per_click_timestamp_viewproduct ELSE 0 END), 0) AS merch_views
        FROM `prj-onlinesales-prod-01.reporting.marketplace_category_level_performance_facts_v2`
        WHERE agency_id = '{agency_id}' AND date >= '{sd}' AND date <= '{ed}'
        GROUP BY 1
