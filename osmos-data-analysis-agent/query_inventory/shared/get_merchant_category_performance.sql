-- =====================================================================
-- id:                       shared.get_merchant_category_performance
-- source:                   tools/common_tools.py:2689  (fn get_merchant_category_performance -> _cat_query)
-- agent:                    shared
-- description:              A merchant's PLA performance (os_ads_search, smart_shopping) broken down by product CATEGORY (e_product_type) × campaign for one period: spend, impressions, clicks, orders, ad_revenue (NOT currency-converted). Called once per period; comparison mode runs it for current + baseline.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {agency_id}  str  -> __AGENCY_ID__
--   {sd}         date -> __START_DATE_1__   (baseline call -> __START_DATE_2__)
--   {ed}         date -> __END_DATE_1__     (baseline call -> __END_DATE_2__)
--   {top_n}      int  -> __LIMIT__
-- injected_fragments:                                  (SQL spliced in by a helper/branch)
--   {client_in}  <- ", ".join("'{c}'" for c in client_ids.split(","))   (os_client_ids) -> "AND f.client_id IN (...)"
--   {cat_expr}   <- "CASE WHEN mmpd.e_product_type IS NULL OR mmpd.e_product_type = '' OR
--                   LOWER(mmpd.e_product_type) = 'na' THEN 'Unknown' ELSE mmpd.e_product_type END" -> category
-- tables:
--   reporting.merchant_merchandise_product_dimensions
--   reporting.os_product_ads_device_product_facts
--   reporting.campaign_tagging_data
--   reporting.marketing_campaign_dimensions
--   reporting.marketing_campaign_group_dimensions
--   reporting.clients
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          called once per period (current + baseline)
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   ctr  = clicks / impressions * 100
--   cpc  = spend / clicks
--   cpm  = spend * 1000 / impressions
--   roas = ad_revenue / spend
--   -- comparison mode (merge on category, campaign_name, marketing_campaign_id, os_client_id):
--   status             = active_both | new | churned   (from spend_current>0 / spend_baseline>0)
--   spend_change / cpc_change / ctr_change / roas_change / orders_change = current - baseline
--   spend_share_current_pct / spend_share_baseline_pct = spend / total_spend * 100
--   contribution_to_spend_change_pct / contribution_to_clicks_change_pct
--   note: spend/revenue are raw (no FX conversion)
-- =====================================================================

        SELECT
            {cat_expr} AS category,
            mcd.alias AS campaign_name,
            ctd.marketing_campaign_id AS marketing_campaign_id,
            ctd.marketing_campaign_group_id AS marketing_campaign_group_id,
            f.client_id AS os_client_id,
            COALESCE(SUM(f.cost), 0) AS spend,
            COALESCE(SUM(f.impressions), 0) AS impressions,
            COALESCE(SUM(f.clicks), 0) AS clicks,
            COALESCE(SUM(f.program_per_click_timestamp_conversions), 0) AS orders_sku,
            COALESCE(SUM(f.program_per_click_timestamp_sales), 0) AS ad_revenue
        FROM `prj-onlinesales-prod-01.reporting.merchant_merchandise_product_dimensions` mmpd
        JOIN `prj-onlinesales-prod-01.reporting.os_product_ads_device_product_facts` f
            ON f.client_id = mmpd.client_id AND f.sku_id = mmpd.sku_id
        LEFT JOIN `prj-onlinesales-prod-01.reporting.campaign_tagging_data` ctd
            ON ctd.account_id = f.account_id AND ctd.campaign_id = f.campaign_id AND ctd.client_id = f.client_id
        JOIN `prj-onlinesales-prod-01.reporting.marketing_campaign_dimensions` mcd
            ON ctd.marketing_campaign_id = mcd.marketing_campaign_id AND mcd.client_id = f.client_id
            AND mcd.campaign_origin != 'PACKAGE_BASED'
        JOIN `prj-onlinesales-prod-01.reporting.marketing_campaign_group_dimensions` mcgd
            ON ctd.client_id = mcgd.client_id AND ctd.marketing_campaign_group_id = mcgd.marketing_campaign_group_id
        JOIN `prj-onlinesales-prod-01.reporting.clients` c
            ON c.client_id = f.client_id
        WHERE c.agency_id = '{agency_id}'
            AND f.client_id IN ({client_in})
            AND f.date >= '{sd}' AND f.date <= '{ed}'
            AND LOWER(mcgd.campaign_type) IN ('performance')
            AND LOWER(mcgd.campaign_subtype) IN ('os_ads_search', 'smart_shopping')
        GROUP BY 1, 2, 3, 4, 5
        HAVING COALESCE(SUM(f.cost), 0) > 0
        ORDER BY spend DESC
        LIMIT {top_n}
