-- =====================================================================
-- id:                       cpc.get_sku_level_cpc_performance
-- source:                   tools/cpc_analysis_tools.py:644  (fn get_sku_level_cpc_performance -> _sku_query)
-- agent:                    cpc
-- description:              SKU-level PROGRAM (PLA performance campaigns: os_ads_search, smart_shopping) funnel for ONE period joined to the SITE/organic SKU funnel: per SKU spend, impressions, clicks, program & site viewproducts/add2carts/orders/GMV. Called once per period; comparison mode runs it for current + baseline.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {agency_id}   str   -> __AGENCY_ID__
--   {sd}          date  -> __START_DATE_1__   (baseline call -> __START_DATE_2__)
--   {ed}          date  -> __END_DATE_1__     (baseline call -> __END_DATE_2__)
-- injected_fragments:                                  (SQL spliced in by a helper)
--   {client_filter}  <- built inline from client_ids (required): ", ".join("'{c}'" ...)
--                       "AND os_product_ads_device_product_facts.client_id IN ('c1', 'c2', ...)"
--   {org_join}       <- built only when mkt_client_id resolved (else empty string); the SITE/organic LEFT JOIN:
--                       """
--                       LEFT JOIN (
--                           SELECT merchant_id, sku_id,
--                               SUM(sok_viewproducts) AS site_viewproducts,
--                               SUM(sok_add2carts) AS site_add2carts,
--                               SUM(sok_salecompletes) AS site_orders,
--                               SUM(sok_sales_usd) AS site_gmv
--                           FROM `prj-onlinesales-prod-01.reporting.os_merchandise_product_performance_facts`
--                           WHERE client_id = '{mkt_client_id}' AND date >= '{sd}' AND date <= '{ed}'
--                           GROUP BY 1, 2
--                       ) org
--                           ON CAST(org.merchant_id AS STRING) = CAST(prog.seller_id AS STRING)
--                           AND CAST(org.sku_id AS STRING) = CAST(prog.product_id AS STRING)"""
--                       (when omitted, org.* columns COALESCE to 0)
-- tables:
--   reporting.merchant_merchandise_product_dimensions
--   reporting.os_product_ads_device_product_facts
--   reporting.campaign_tagging_data
--   reporting.marketing_campaign_dimensions
--   reporting.marketing_campaign_group_dimensions
--   reporting.clients
--   reporting.os_merchandise_product_performance_facts   (via {org_join}, when marketplace_client_id resolved)
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          called once per period (current + baseline)
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   cpc              = spend / clicks
--   ctr              = clicks / impressions * 100
--   cpm              = spend * 1000 / impressions
--   roi              = program_gmv / spend
--   attributed_cvr   = program_orders / program_viewproducts * 100
--   site_cvr         = site_orders / site_viewproducts * 100
--   cpc_change       = cur.cpc - base.cpc
--   spend_change / spend_change_pct / clicks_change = current - baseline (and pct)
--   roi_change / attributed_cvr_change / site_cvr_change = current - baseline
--   status           = active_both | new | churned   (from spend_current>0 / spend_baseline>0)
--   contribution_to_spend_change_pct = (cur.spend - base.spend) / total_spend_delta * 100  (SKUs ranked by |this| per merchant)
--   sku_rank         = rank(spend desc) per client_id  (non-comparison: top skus_per_merchant)
--   overall_cpc      = total_spend / total_clicks   (per period) ; spend_change_pct = pct_change(total)
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
