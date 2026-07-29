-- =====================================================================
-- id:                       shared.get_campaign_performance.daily
-- source:                   tools/common_tools.py:644  (fn get_campaign_performance, daily_mode branch)
-- agent:                    shared
-- description:              Date-level (daily) campaign-group performance for SPECIFIC campaigns in one period: per date+campaign impressions, clicks, cost, orders, revenue (currency-converted). Single call (daily_mode=True with marketing_campaign_ids).
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {agency_id}   str   -> __AGENCY_ID__   (appears twice: merchant JOIN + WHERE mc.agency_id)
--   {start_date}  date  -> __START_DATE_1__   (inside {date_filter})
--   {end_date}    date  -> __END_DATE_1__     (inside {date_filter})
-- injected_fragments:                                  (SQL spliced in by a helper/branch)
--   {date_filter}          <- "(cpf.date >= '{start_date}' AND cpf.date <= '{end_date}')"
--   {campaign_type_filter} <- from program_type:
--                             pla     -> "AND mcgd.campaign_type = 'PERFORMANCE'"
--                             display -> "AND mcgd.campaign_type IN ('AWARENESS', 'INVENTORY')"
--                             (none)  -> "AND mcgd.campaign_type IN ('PERFORMANCE', 'INVENTORY', 'OFFSITE')"
--   {extra_filters}        <- newline-joined optional filters:
--                             marketing_campaign_ids -> "AND ctd.marketing_campaign_id IN (...)"
--                             client_ids             -> "AND mcd.client_id IN (...)"
--                             seller_ids             -> "AND mmd.merchant_id IN (...)"
--                             status                 -> "AND mcgd.effective_status = '{status}'"
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
-- comparison_mode:          single call (daily rows for one period)
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   ctr = clicks / impressions * 100   (null when impressions <= 0)
--   cpc = cost / clicks                (null when clicks <= 0)
--   roi = revenue / cost               (null when cost <= 0)
--   summary.total_rows / unique_campaigns (nunique campaign_group_id) / total_cost
-- =====================================================================

        SELECT
            cpf.date,
            mcgd.marketing_campaign_group_alias AS campaign_group_name,
            mcgd.marketing_campaign_group_id AS campaign_group_id,
            mmd.merchant_name,
            mmd.merchant_id,
            mcd.client_id AS os_client_id,
            mcgd.campaign_subtype,
            REPLACE(mcgd.effective_status, '_', ' ') AS campaign_group_status,
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
        WHERE {date_filter}
            {campaign_type_filter}
            AND (mcgd.campaign_origin != 'PACKAGE_BASED' OR mcgd.campaign_origin IS NULL)
            AND mmd.merchant_id NOT LIKE 'NULL'
            AND mc.agency_id = '{agency_id}'
            {extra_filters}
        GROUP BY 1, 2, 3, 4, 5, 6, 7, 8
        ORDER BY cpf.date, cost DESC
