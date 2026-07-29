-- =====================================================================
-- id:                       bu.get_display_ad_unit_performance
-- source:                   tools/bu_analysis_tools.py:1125  (fn get_display_ad_unit_performance)
-- agent:                    bu
-- description:              Display ad-unit-level breakdown for ONE date range: requests, responses, RR, impressions, clicks, CTR, cost, CPM, ROI, impression/response ratio, funnel events.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {agency_id}    str    -> __AGENCY_ID__
--   {start_date}   date   -> __START_DATE_1__
--   {end_date}     date   -> __END_DATE_1__
--   {top_n}        int    -> __TOP_N__
-- injected_fragments:       (none)
-- tables:
--   reporting.os_display_ads_ad_unit_facts
--   reporting.marketplace_clients
--   reporting.static_currency_conversion
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          single call (agent calls once per period to compare)
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   (all metrics computed in SQL) float columns rounded to 2dp; rows passed through
--   total_ad_units_analyzed = len(rows);  total_cost = SUM(cost)
-- =====================================================================

SELECT
    auf.ad_unit_name,
    auf.page_type,
    SUM(auf.requests) AS request_count,
    SUM(auf.non_zero_responses) AS response_count,
    SAFE_DIVIDE(SUM(auf.non_zero_responses) * 100, NULLIF(SUM(auf.requests), 0)) AS response_percentage,
    SUM(auf.impressions) AS impressions,
    SUM(auf.clicks) AS clicks,
    SAFE_DIVIDE(SUM(auf.clicks) * 100, NULLIF(SUM(auf.impressions), 0)) AS ctr,
    SUM(auf.cost * scc.conversion_factor) AS cost,
    SAFE_DIVIDE(SUM(auf.cost * scc.conversion_factor) * 1000, NULLIF(SUM(auf.impressions), 0)) AS cpm,
    SAFE_DIVIDE(SUM(auf.program_per_click_timestamp_sales * scc.conversion_factor), NULLIF(SUM(auf.cost * scc.conversion_factor), 0)) AS roi,
    SAFE_DIVIDE(SUM(auf.impressions), NULLIF(SUM(auf.non_zero_responses), 0)) AS impression_response_ratio,
    SUM(auf.program_per_click_timestamp_viewproduct) AS view_product,
    SUM(auf.program_per_click_timestamp_add_to_cart) AS add_to_cart,
    SUM(auf.program_per_click_timestamp_conversions) AS conversions,
    SUM(auf.program_per_click_timestamp_sales * scc.conversion_factor) AS sales
FROM `prj-onlinesales-prod-01.reporting.os_display_ads_ad_unit_facts` auf
INNER JOIN `prj-onlinesales-prod-01.reporting.marketplace_clients` mc
    ON mc.marketplace_client_id = auf.marketplace_client_id
INNER JOIN `prj-onlinesales-prod-01.reporting.static_currency_conversion` scc
    ON scc.from_currency = 'USD'
    AND scc.to_currency = mc.currency
WHERE auf.date >= '{start_date}' AND auf.date <= '{end_date}'
    AND mc.agency_id = '{agency_id}'
GROUP BY 1, 2
ORDER BY response_count DESC
LIMIT {top_n}
