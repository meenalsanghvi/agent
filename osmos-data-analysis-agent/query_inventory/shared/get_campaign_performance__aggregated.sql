-- =====================================================================
-- id:                       shared.get_campaign_performance.aggregated
-- source:                   tools/common_tools.py:714  (fn get_campaign_performance -> _agg_query)
-- agent:                    shared
-- description:              Campaign-group performance aggregated over a period: per campaign-group impressions, clicks, cost, orders, revenue (currency-converted), plus derived group type/subtype (large CASE) and daily_budget. Called once per period; comparison mode runs it for current + baseline.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {agency_id}  str  -> __AGENCY_ID__   (appears twice: merchant JOIN + WHERE mc.agency_id)
--   {sd}         date -> __START_DATE_1__   (baseline call -> __START_DATE_2__)
--   {ed}         date -> __END_DATE_1__     (baseline call -> __END_DATE_2__)
--   {lim}        int  -> __LIMIT__          (top_n single-mode; max(top_n,300) pool in comparison mode)
-- injected_fragments:                                  (SQL spliced in by a helper/branch)
--   {campaign_type_filter} <- from program_type:
--                             pla     -> "AND mcgd.campaign_type = 'PERFORMANCE'"
--                             display -> "AND mcgd.campaign_type IN ('AWARENESS', 'INVENTORY')"
--                             (none)  -> "AND mcgd.campaign_type IN ('PERFORMANCE', 'INVENTORY', 'OFFSITE')"
--   {extra_filters}        <- newline-joined optional filters:
--                             marketing_campaign_ids -> "AND ctd.marketing_campaign_id IN (...)"
--                             client_ids             -> "AND mcd.client_id IN (...)"
--                             seller_ids             -> "AND mmd.merchant_id IN (...)"
--                             status                 -> "AND mcgd.effective_status = '{status}'"
--   (campaign_group_type / campaign_group_subtype are large inline CASE expressions, NOT helpers)
-- tables:
--   reporting.campaign_performance_facts
--   reporting.campaign_tagging_data
--   reporting.marketing_campaign_dimensions
--   reporting.marketing_campaign_group_dimensions
--   reporting.monetize_merchant_dimensions
--   reporting.marketplace_clients
--   reporting.static_currency_conversion
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          called once per period (current + baseline)
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   ctr = clicks / impressions * 100   (null when impressions <= 0)
--   cpc = cost / clicks                (null when clicks <= 0)
--   roi = revenue / cost               (null when cost <= 0)
--   -- comparison mode (merge current vs baseline on campaign_group_id, merchant_id, os_client_id):
--   status            = active_both | new | churned   (from cost_current>0 / cost_baseline>0)
--   cpc_change        = cur.cpc - base.cpc
--   spend_change      = cur.cost - base.cost
--   ctr_change        = cur.ctr - base.ctr
--   roi_change        = cur.roi - base.roi
--   spend_share_current_pct  / spend_share_baseline_pct = cost / total_cost * 100 (per period)
--   contribution_to_spend_change_pct  = (cur.cost - base.cost) / total_spend_delta * 100
--   contribution_to_clicks_change_pct = (cur.clicks - base.clicks) / total_clicks_delta * 100
--   summary.current_total_cost / baseline_total_cost / total_cost_change
-- =====================================================================

    SELECT
        mcgd.marketing_campaign_group_alias AS campaign_group_name,
        mcgd.marketing_campaign_group_id AS campaign_group_id,
        mmd.merchant_name,
        mmd.merchant_id,
        mcd.client_id AS os_client_id,
        CASE
            WHEN JSON_EXTRACT_SCALAR(mcgd.metadata, '$.isEanEnabled') = 'true'
                AND ctd.vendor IN ('google', 'facebook', 'tiktok') THEN 'Offsite Ad'
            WHEN mcgd.campaign_type = 'PERFORMANCE' THEN 'Sponsored Product Ad'
            WHEN mcgd.campaign_type IN ('AWARENESS', 'INVENTORY') THEN 'Sponsored Display Ad'
            WHEN mcgd.campaign_type IN ('OFFSITE') THEN 'Offsite Ad'
            ELSE 'Other'
        END AS campaign_group_type,
        CASE
            WHEN JSON_EXTRACT_SCALAR(mcgd.metadata, '$.isEanEnabled') = 'true'
                AND ctd.vendor IN ('google', 'facebook', 'tiktok') THEN 'Manual'
            WHEN mcgd.campaign_type = 'PERFORMANCE' AND mcgd.campaign_subtype = 'SMART_SHOPPING'
                AND ((mcgd.bidding_strategy IN ('AUTO_CPC', 'AUTO_CPM')
                    AND mcgd.objective_name IN ('Visitors', 'Visibility'))
                    OR mcgd.objective_name = 'Absolute Revenue') THEN 'Smart Shopping'
            WHEN mcgd.campaign_type = 'PERFORMANCE'
                AND mcgd.objective_name IN ('Visitors', 'Visibility')
                AND mcgd.bidding_strategy IN ('CPC', 'CPM') THEN 'Manual'
            WHEN mcgd.campaign_type = 'PERFORMANCE'
                AND mcgd.campaign_subtype = 'OS_ADS_SEARCH' THEN 'Search-Only'
            WHEN mcgd.campaign_type IN ('AWARENESS', 'INVENTORY')
                AND mcgd.campaign_subtype = 'AUCTION' THEN 'Auction'
            WHEN mcgd.campaign_type IN ('AWARENESS', 'INVENTORY')
                AND mcgd.campaign_subtype = 'BLOCK_BUY' THEN 'Guaranteed'
            WHEN mcgd.campaign_type IN ('AWARENESS', 'INVENTORY')
                AND mcgd.campaign_subtype = 'PRE_AUCTION' THEN 'Auction Packages'
            WHEN mcgd.campaign_type IN ('OFFSITE')
                AND mcgd.campaign_subtype IN ('FACEBOOK_PRODUCT_AD', 'FACEBOOK', 'FACEBOOK_CAROUSEL_AD') THEN 'Facebook'
            WHEN mcgd.campaign_type IN ('OFFSITE')
                AND mcgd.campaign_subtype IN ('FACEBOOK_DPA') THEN 'Facebook DPA'
            WHEN mcgd.campaign_type IN ('OFFSITE')
                AND mcgd.campaign_subtype IN ('GOOGLE_PERFORMANCE_MAX_SHOPPING', 'GOOGLE_PERFORMANCE_MAX') THEN 'Google Performance Max'
            WHEN mcgd.campaign_type IN ('OFFSITE')
                AND mcgd.campaign_subtype IN ('GOOGLE_PRODUCT_AD', 'GOOGLE_SEARCH_TEXT_AD') THEN 'Google'
            WHEN mcgd.campaign_type IN ('OFFSITE')
                AND mcgd.campaign_subtype IN ('TIKTOK_TRAFFIC') THEN 'Tiktok Traffic'
            WHEN mcgd.campaign_type IN ('OFFSITE')
                AND mcgd.campaign_subtype IN ('TIKTOK_REACH') THEN 'Tiktok Reach'
            ELSE mcgd.campaign_subtype
        END AS campaign_group_subtype,
        mcgd.campaign_subtype,
        REPLACE(mcgd.effective_status, '_', ' ') AS campaign_group_status,
        CASE
            WHEN mcgd.budget_type = 'LIFETIME_BUDGET' THEN NULL
            ELSE mcgd.daily_budget
        END AS daily_budget,
        SUM(cpf.impressions) AS impressions,
        SUM(cpf.clicks) AS clicks,
        COALESCE(SUM(cpf.cost * scc.conversion_factor), 0) AS cost,
        COALESCE(SUM(cpf.program_per_click_timestamp_conversions), 0) AS orders,
        COALESCE(SUM(cpf.program_per_click_timestamp_sales * scc.conversion_factor), 0) AS revenue
    FROM `prj-onlinesales-prod-01.reporting.campaign_performance_facts` AS cpf
    JOIN `prj-onlinesales-prod-01.reporting.campaign_tagging_data` AS ctd
        ON cpf.campaign_id = ctd.campaign_id AND cpf.client_id = ctd.client_id
    JOIN `prj-onlinesales-prod-01.reporting.marketing_campaign_dimensions` AS mcd
        ON ctd.marketing_campaign_id = mcd.marketing_campaign_id
        AND ctd.client_id = mcd.client_id
    JOIN `prj-onlinesales-prod-01.reporting.marketing_campaign_group_dimensions` AS mcgd
        ON mcd.marketing_campaign_group_id = mcgd.marketing_campaign_group_id
        AND mcd.client_id = mcgd.client_id
        AND mcgd.marketing_campaign_group_id = ctd.marketing_campaign_group_id
        AND mcgd.client_id = ctd.client_id
    JOIN `prj-onlinesales-prod-01.reporting.monetize_merchant_dimensions` AS mmd
        ON mcgd.client_id = mmd.client_id AND mmd.agency_id = '{agency_id}'
    JOIN `prj-onlinesales-prod-01.reporting.marketplace_clients` AS mc
        ON mc.agency_id = mmd.agency_id AND mc.marketplace_type = 'monetize'
    JOIN `prj-onlinesales-prod-01.reporting.static_currency_conversion` AS scc
        ON scc.from_currency = cpf.currency AND scc.to_currency = mc.currency
    WHERE (cpf.date >= '{sd}' AND cpf.date <= '{ed}')
        {campaign_type_filter}
        AND (mcgd.campaign_origin != 'PACKAGE_BASED' OR mcgd.campaign_origin IS NULL)
        AND mmd.merchant_id NOT LIKE 'NULL'
        AND mc.agency_id = '{agency_id}'
        {extra_filters}
    GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
    ORDER BY cost DESC
    LIMIT {lim}
