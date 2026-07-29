-- =====================================================================
-- id:                       bu.check_requests.display
-- source:                   tools/bu_analysis_tools.py:171  (fn check_requests -> _check_requests_display)
-- agent:                    bu
-- description:              Daily Display ad request / non-zero-response volume and response % for ONE date range (per-day rows).
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {agency_id}    str    -> __AGENCY_ID__
--   {start_date}   date   -> __START_DATE_1__
--   {end_date}     date   -> __END_DATE_1__
--   {page_type}    str    -> __PAGE_TYPE__   (optional; only present when page_type given)
-- injected_fragments:                                  (SQL spliced in by a helper)
--   {page_type_filter}  <- inline in _check_requests_display
--                        page_type set -> "AND LOWER(auf.page_type) = LOWER('{page_type}')"
--                        else          -> ""
-- tables:
--   reporting.os_display_ads_ad_unit_facts
--   reporting.marketplace_clients
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          single call (agent calls once per period to compare)
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates; _process_request_results)
--   total_requests          = SUM(request_count)
--   total_responses         = SUM(response_count)
--   avg_response_percentage = total_responses * 100 / total_requests
--   days_count              = number of daily rows
-- =====================================================================

SELECT
    auf.date AS date,
    SUM(auf.requests) AS request_count,
    SUM(auf.non_zero_responses) AS response_count,
    SAFE_DIVIDE(
        SUM(auf.non_zero_responses) * 100,
        NULLIF(SUM(auf.requests), 0)
    ) AS response_percentage
FROM
    `prj-onlinesales-prod-01.reporting.os_display_ads_ad_unit_facts` AS auf
JOIN
    `prj-onlinesales-prod-01.reporting.marketplace_clients` AS mc
    ON mc.marketplace_client_id = auf.marketplace_client_id
WHERE
    auf.date >= '{start_date}' AND auf.date <= '{end_date}'
    AND mc.agency_id = '{agency_id}'
    AND auf.page_type IS NOT NULL
    AND TRIM(auf.page_type) NOT IN ('', 'NA')
    {page_type_filter}
GROUP BY 1
ORDER BY 1
