-- =====================================================================
-- id:                       bu.get_display_quadrant_performance
-- source:                   tools/bu_analysis_tools.py:990  (fn get_display_quadrant_performance)
-- agent:                    bu
-- description:              Display inventory-level (page_type + ad_unit) quadrant for ONE date range: avg request count, response rate, impression/response ratio, spend, BU%, unique campaigns/merchants.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {agency_id}    str    -> __AGENCY_ID__
--   {start_date}   date   -> __START_DATE_1__
--   {end_date}     date   -> __END_DATE_1__
--   {top_n}        int    -> __TOP_N__
--   {page_type_filter} str -> __PAGE_TYPE__   (optional; see injected_fragments)
-- injected_fragments:                                  (SQL spliced in by a helper)
--   {page_filter}  <- page_type_filter set -> "AND LOWER(page_type) = LOWER('{page_type_filter}')"  else ""
-- tables:
--   reporting.os_display_ads_daily_quadrant_report
--   reporting.agencies
--   reporting.static_currency_conversion
--   reporting.os_display_ads_ad_targeting_report
--   reporting.os_ads_db_campaigns
--   reporting.os_ads_db_campaign_types
--   reporting.os_ads_db_campaign_inventory_configurations
--   reporting.os_ads_db_status_types
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          single call (agent calls once per period to compare)
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   (none numeric; all metrics computed in SQL) rows passed through; total_inventories = len(rows)
-- =====================================================================

SELECT
    quadrant_data.page_type,
    quadrant_data.ad_unit_name AS inventory_name,
    ROUND(AVG(quadrant_data.request_count), 2) AS request_count,
    CASE
        WHEN ROUND(AVG(quadrant_data.response_percentage), 2) > 100 THEN 100
        ELSE ROUND(AVG(quadrant_data.response_percentage), 2)
    END AS response_rate,
    CASE
        WHEN ROUND(AVG(quadrant_data.impression_responses_ratio), 2) > 100 THEN 100
        ELSE ROUND(AVG(quadrant_data.impression_responses_ratio), 2)
    END AS impression_responses_ratio,
    ROUND(AVG(quadrant_data.cost), 2) AS spend,
    CASE
        WHEN AVG(quadrant_data.daily_budget) < AVG(quadrant_data.cost)
            OR ROUND(AVG(quadrant_data.budget_utilisation_perc), 2) > 100 THEN 100
        ELSE ROUND(AVG(quadrant_data.budget_utilisation_perc), 2)
    END AS budget_utilisation_perc,
    COUNT(DISTINCT CASE WHEN spends_data.spend > 0 THEN spends_data.campaign_id END) AS uniq_campaigns_count,
    COUNT(DISTINCT CASE WHEN spends_data.spend > 0 THEN spends_data.merchant_id END) AS uniq_merchant_count
FROM (
    SELECT
        page_type,
        ad_unit_name,
        SUM(quadrant_data.requests) AS request_count,
        SUM(quadrant_data.responses) AS response_count,
        CASE
            WHEN SUM(quadrant_data.requests) > 0
                THEN SUM(quadrant_data.responses) * 100.0 / SUM(quadrant_data.requests)
            ELSE 0
        END AS response_percentage,
        COALESCE(
            SAFE_DIVIDE(SUM(quadrant_data.impressions), SUM(quadrant_data.responses)), 0
        ) AS impression_responses_ratio,
        SUM(quadrant_data.cost_usd * static_currency_conversion.conversion_factor) AS cost,
        SUM(quadrant_data.daily_budget_usd * static_currency_conversion.conversion_factor) AS daily_budget,
        CASE
            WHEN SUM(quadrant_data.daily_budget_usd) > 0
                THEN SUM(quadrant_data.cost_usd) * 100.0 / SUM(quadrant_data.daily_budget_usd)
            ELSE 0
        END AS budget_utilisation_perc
    FROM `prj-onlinesales-prod-01.reporting.os_display_ads_daily_quadrant_report` quadrant_data
    INNER JOIN `prj-onlinesales-prod-01.reporting.agencies` agencies
        ON agencies.marketplace_client_id = quadrant_data.marketplace_client_id
        AND agencies.agency_id = '{agency_id}'
    INNER JOIN `prj-onlinesales-prod-01.reporting.static_currency_conversion` static_currency_conversion
        ON static_currency_conversion.from_currency = 'USD'
        AND static_currency_conversion.to_currency = agencies.currency
    WHERE quadrant_data.date >= '{start_date}' AND quadrant_data.date <= '{end_date}'
        AND page_type IS NOT NULL
        {page_filter}
    GROUP BY 1, 2
    HAVING SUM(quadrant_data.requests) > 1000
) quadrant_data
LEFT JOIN (
    SELECT
        os_display_ads_ad_targeting_report.page_type,
        os_display_ads_ad_targeting_report.ad_unit_name,
        os_display_ads_ad_targeting_report.merchant_id,
        os_display_ads_ad_targeting_report.campaign_id,
        SUM(cost) AS spend
    FROM `prj-onlinesales-prod-01.reporting.os_display_ads_ad_targeting_report`
    INNER JOIN `prj-onlinesales-prod-01.reporting.agencies`
        ON agencies.marketplace_client_id = os_display_ads_ad_targeting_report.marketplace_client_id
        AND agencies.agency_id = '{agency_id}'
    INNER JOIN `prj-onlinesales-prod-01.reporting.os_ads_db_campaigns`
        ON os_display_ads_ad_targeting_report.campaign_id = SAFE_CAST(os_ads_db_campaigns.id AS STRING)
        AND os_display_ads_ad_targeting_report.client_id = SAFE_CAST(os_ads_db_campaigns.client_id AS STRING)
    INNER JOIN `prj-onlinesales-prod-01.reporting.os_ads_db_campaign_types` AS campaign_types
        ON os_ads_db_campaigns.campaign_type_id = campaign_types.id
    LEFT JOIN `prj-onlinesales-prod-01.reporting.os_ads_db_campaign_inventory_configurations`
        ON SAFE_CAST(os_ads_db_campaign_inventory_configurations.marketplace_client_id AS STRING) = agencies.marketplace_client_id
        AND SAFE_CAST(os_ads_db_campaign_inventory_configurations.marketplace_client_id AS STRING) = os_display_ads_ad_targeting_report.marketplace_client_id
        AND SAFE_CAST(os_ads_db_campaign_inventory_configurations.client_id AS STRING) = os_display_ads_ad_targeting_report.client_id
        AND SAFE_CAST(os_ads_db_campaign_inventory_configurations.campaign_id AS STRING) = os_display_ads_ad_targeting_report.campaign_id
        AND os_ads_db_campaign_inventory_configurations.campaign_id = os_ads_db_campaigns.id
    INNER JOIN `prj-onlinesales-prod-01.reporting.os_ads_db_status_types` AS status_types
        ON os_ads_db_campaign_inventory_configurations.status_type_id = status_types.id
    WHERE os_display_ads_ad_targeting_report.date >= '{start_date}'
        AND os_display_ads_ad_targeting_report.date <= '{end_date}'
        AND (campaign_types.name = 'BLOCK_BUY' OR status_types.name = 'ACTIVE')
    GROUP BY 1, 2, 3, 4
) spends_data
    ON LOWER(quadrant_data.page_type) = LOWER(spends_data.page_type)
    AND LOWER(quadrant_data.ad_unit_name) = LOWER(spends_data.ad_unit_name)
WHERE quadrant_data.page_type IS NOT NULL
GROUP BY 1, 2
ORDER BY request_count DESC
LIMIT {top_n}
