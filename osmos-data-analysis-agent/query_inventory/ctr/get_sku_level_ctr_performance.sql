-- =====================================================================
-- id:                       ctr.get_sku_level_ctr_performance
-- source:                   tools/ctr_analysis_tools.py:561  (fn get_sku_level_ctr_performance -> _sku_query)
-- agent:                    ctr
-- description:              SKU-level raw spend / impressions / clicks per product for PLA performance campaigns only (os_ads_search, smart_shopping), scoped to given os_client_ids. Called once per period; comparison mode runs it for current + baseline.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {agency_id}   str    -> __AGENCY_ID__
--   {sd}          date   -> __START_DATE_1__   (baseline call -> __START_DATE_2__)
--   {ed}          date   -> __END_DATE_1__     (baseline call -> __END_DATE_2__)
-- injected_fragments:                                  (SQL spliced in by a helper)
--   {client_filter}  <- built inline from client_ids (required arg)
--                     -> "AND os_product_ads_device_product_facts.client_id IN ('<id>', ...)"
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
--   spend                = round(spend, 2)
--   ctr                  = ctr_ratio(clicks, impressions) = round(clicks * 100 / impressions, 2)   (0 when impressions = 0)
--   cpc                  = cpc_ratio(spend, clicks) = round(spend / clicks, 4)                      (0 when clicks = 0)
--   cpm                  = round(spend * 1000 / impressions, 4)                                     (0 when impressions = 0)
--   sku_rank             = (single period) rank of SKU within client_id by impressions desc; keep top skus_per_merchant
--   status               = active_both (imp cur>0 & base>0) | new (cur>0 only) | churned (base>0 only)
--   ctr_change           = current.ctr - baseline.ctr
--   clicks_change        = current.clicks - baseline.clicks
--   impressions_change   = current.impressions - baseline.impressions
--   contribution_to_impressions_change_pct = contribution_pct(impressions_change, total_impressions_delta)
--   contribution_to_clicks_change_pct      = contribution_pct(clicks_change, total_clicks_delta)
--   (comparison) SKUs ranked per merchant by |contribution_to_impressions_change_pct|, keep top skus_per_merchant
--   current_overall_ctr  = ctr_ratio(total_clicks_current, total_impressions_current)
--   baseline_overall_ctr = ctr_ratio(total_clicks_baseline, total_impressions_baseline)
-- =====================================================================

        SELECT
            product_id, client_id, seller_id, seller_name,
            MAX(product) AS product, STRING_AGG(DISTINCT campaign_name, ', ') AS campaign_name,
            MAX(brand) AS brand, MAX(category) AS category,
            SUM(spend) AS spend, SUM(impressions) AS impressions, SUM(clicks) AS clicks
        FROM (
            SELECT
                merchant_merchandise_product_dimensions.sku_id AS product_id,
                os_product_ads_device_product_facts.client_id AS client_id,
                clients.seller_id AS seller_id,
                clients.seller_name AS seller_name,
                merchant_merchandise_product_dimensions.e_name AS product,
                marketing_campaign_dimensions.alias AS campaign_name,
                merchant_merchandise_product_dimensions.e_brand AS brand,
                merchant_merchandise_product_dimensions.e_product_type AS category,
                COALESCE(SUM(os_product_ads_device_product_facts.cost), 0) AS spend,
                COALESCE(SUM(os_product_ads_device_product_facts.impressions), 0) AS impressions,
                COALESCE(SUM(os_product_ads_device_product_facts.clicks), 0) AS clicks
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
            GROUP BY 1, 2, 3, 4, 5, 6, 7, 8
        ) per_campaign
        GROUP BY 1, 2, 3, 4
