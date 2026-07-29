-- =====================================================================
-- id:                       roas.get_sku_level_performance
-- source:                   tools/roi_analysis_tools.py:736  (fn get_sku_level_performance -> _SKU_QUERY_TEMPLATE, org_join built in _build_sku_query:718)
-- agent:                    roas
-- description:              SKU-level PROGRAM (PLA performance campaigns only) + SITE (organic) funnel for ONE period, one row per SKU/merchant. Same query issued once per period; comparison mode runs current + baseline. Filtered to campaign_type=performance and subtype in (os_ads_search, smart_shopping).
-- proposed_kam_report_type: KAM_AGENT_ROAS_SKU_PERFORMANCE
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {agency_id}      str    -> __AGENCY_ID__
--   {sd}             date   -> __START_DATE_1__   (baseline call -> __START_DATE_2__)
--   {ed}             date   -> __END_DATE_1__     (baseline call -> __END_DATE_2__)
--   {mkt_client_id}  str    -> __MARKETPLACE_CLIENT_ID__  (resolved by get_sku_level_performance__resolve_marketplace_client; inside org_join only)
-- injected_fragments:                                  (SQL spliced in by a helper)
--   {client_filter}  <- built inline from client_ids (os_client_ids, comma-separated; required)
--                       "AND os_product_ads_device_product_facts.client_id IN ('id1', 'id2', ...)"   (-> __CLIENT_IDS__)
--   {org_join}       <- built inline in _build_sku_query; empty string when mkt_client_id is None,
--                       otherwise the organic-SKU LEFT JOIN below (adds table os_merchandise_product_performance_facts):
--                         LEFT JOIN (
--                             SELECT merchant_id, sku_id,
--                                 SUM(sok_viewproducts) AS site_viewproducts,
--                                 SUM(sok_add2carts) AS site_add2carts,
--                                 SUM(sok_salecompletes) AS site_orders,
--                                 SUM(sok_sales_usd) AS site_gmv
--                             FROM `prj-onlinesales-prod-01.reporting.os_merchandise_product_performance_facts`
--                             WHERE client_id = '{mkt_client_id}' AND date >= '{sd}' AND date <= '{ed}'
--                             GROUP BY 1, 2
--                         ) org
--                             ON CAST(org.merchant_id AS STRING) = CAST(prog.seller_id AS STRING)
--                             AND CAST(org.sku_id AS STRING) = CAST(prog.product_id AS STRING)
-- tables:
--   reporting.merchant_merchandise_product_dimensions
--   reporting.os_product_ads_device_product_facts
--   reporting.campaign_tagging_data
--   reporting.marketing_campaign_dimensions
--   reporting.marketing_campaign_group_dimensions
--   reporting.clients
--   reporting.os_merchandise_product_performance_facts   (only via {org_join} when mkt_client_id resolves)
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          called once per period (current + baseline)
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   per-SKU (_sku_metrics):
--     cpc             = spend / clicks
--     ctr             = clicks / impressions * 100
--     roi             = program_gmv / spend
--     attributed_cvr  = program_orders / program_viewproducts * 100
--     site_cvr        = site_orders / site_viewproducts * 100
--   single period: sku_rank = RANK by spend desc within client_id; keep top skus_per_merchant per merchant
--   comparison:
--     status          = active_both (spend_current>0 & spend_baseline>0) | new (cur only) | churned (base only)
--     changes.<m>_change      = current - baseline   (program_gmv, program_orders, spend, roi, attributed_cvr, site_cvr)
--     changes.<m>_change_pct  = (current - baseline)/baseline * 100   (program_gmv)
--     contribution_to_program_gmv_change_pct = sku program_gmv delta / total program_gmv delta * 100
--       (SKUs ranked per merchant by |contribution_to_program_gmv_change_pct|, top skus_per_merchant kept)
--   summary.overall_roi   = total_program_gmv / total_spend        (single period)
--   summary.current_roi   = current total program_gmv / current total spend
--   summary.baseline_roi  = baseline total program_gmv / baseline total spend
--   summary.program_gmv_change      = current total program_gmv - baseline total program_gmv
--   summary.program_gmv_change_pct  = (current - baseline)/baseline * 100
--   (note: SKU program_gmv / site_gmv are NOT currency-converted)
-- =====================================================================

SELECT
    prog.product_id, prog.client_id, prog.seller_id, prog.seller_name,
    prog.product, prog.campaign_names, prog.brand, prog.category,
    prog.spend, prog.impressions, prog.clicks, prog.program_viewproducts,
    prog.program_add2carts, prog.program_orders, prog.program_gmv,
    COALESCE(org.site_viewproducts, 0) AS site_viewproducts,
    COALESCE(org.site_add2carts, 0) AS site_add2carts,
    COALESCE(org.site_orders, 0) AS site_orders,
    COALESCE(org.site_gmv, 0) AS site_gmv
FROM (
    SELECT
        merchant_merchandise_product_dimensions.sku_id AS product_id,
        os_product_ads_device_product_facts.client_id AS client_id,
        clients.seller_id AS seller_id,
        clients.seller_name AS seller_name,
        MAX(merchant_merchandise_product_dimensions.e_name) AS product,
        STRING_AGG(DISTINCT marketing_campaign_dimensions.alias, ', ') AS campaign_names,
        MAX(merchant_merchandise_product_dimensions.e_brand) AS brand,
        MAX(merchant_merchandise_product_dimensions.e_product_type) AS category,
        COALESCE(SUM(os_product_ads_device_product_facts.cost), 0) AS spend,
        COALESCE(SUM(os_product_ads_device_product_facts.impressions), 0) AS impressions,
        COALESCE(SUM(os_product_ads_device_product_facts.clicks), 0) AS clicks,
        COALESCE(SUM(os_product_ads_device_product_facts.program_per_click_timestamp_viewproduct), 0) AS program_viewproducts,
        COALESCE(SUM(os_product_ads_device_product_facts.program_per_click_timestamp_add_to_cart), 0) AS program_add2carts,
        COALESCE(SUM(os_product_ads_device_product_facts.program_per_click_timestamp_conversions), 0) AS program_orders,
        COALESCE(SUM(os_product_ads_device_product_facts.program_per_click_timestamp_sales), 0) AS program_gmv
    FROM `prj-onlinesales-prod-01.reporting.merchant_merchandise_product_dimensions` merchant_merchandise_product_dimensions
    JOIN `prj-onlinesales-prod-01.reporting.os_product_ads_device_product_facts` os_product_ads_device_product_facts
        ON os_product_ads_device_product_facts.client_id = merchant_merchandise_product_dimensions.client_id
        AND os_product_ads_device_product_facts.sku_id = merchant_merchandise_product_dimensions.sku_id
    LEFT JOIN `prj-onlinesales-prod-01.reporting.campaign_tagging_data` campaign_tagging_data
        ON campaign_tagging_data.account_id = os_product_ads_device_product_facts.account_id
        AND campaign_tagging_data.campaign_id = os_product_ads_device_product_facts.campaign_id
        AND campaign_tagging_data.client_id = os_product_ads_device_product_facts.client_id
    JOIN `prj-onlinesales-prod-01.reporting.marketing_campaign_dimensions` marketing_campaign_dimensions
        ON campaign_tagging_data.marketing_campaign_id = marketing_campaign_dimensions.marketing_campaign_id
        AND marketing_campaign_dimensions.client_id = os_product_ads_device_product_facts.client_id
        AND marketing_campaign_dimensions.campaign_origin != 'PACKAGE_BASED'
    JOIN `prj-onlinesales-prod-01.reporting.marketing_campaign_group_dimensions` marketing_campaign_group_dimensions
        ON campaign_tagging_data.client_id = marketing_campaign_group_dimensions.client_id
        AND campaign_tagging_data.marketing_campaign_group_id = marketing_campaign_group_dimensions.marketing_campaign_group_id
    JOIN `prj-onlinesales-prod-01.reporting.clients` clients
        ON clients.client_id = os_product_ads_device_product_facts.client_id
    WHERE clients.agency_id = '{agency_id}'
        {client_filter}
        AND os_product_ads_device_product_facts.date >= '{sd}'
        AND os_product_ads_device_product_facts.date <= '{ed}'
        AND LOWER(marketing_campaign_group_dimensions.campaign_type) IN ('performance')
        AND LOWER(marketing_campaign_group_dimensions.campaign_subtype) IN ('os_ads_search', 'smart_shopping')
    GROUP BY 1, 2, 3, 4
) prog{org_join}
