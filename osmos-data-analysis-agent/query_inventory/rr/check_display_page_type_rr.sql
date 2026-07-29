-- =====================================================================
-- id:                       rr.check_display_page_type_rr
-- source:                   tools/rr_analysis_tools.py:1611  (fn check_display_page_type_rr)
-- agent:                    rr
-- description:              Display ad response rate broken down by page type for ONE period. Called once per period; comparison mode runs it for current + baseline.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {marketplace_client_id} str  -> __MARKETPLACE_CLIENT_ID__
--   {start_date}            date -> __START_DATE_1__   (baseline call -> __START_DATE_2__)
--   {end_date}              date -> __END_DATE_1__     (baseline call -> __END_DATE_2__)
-- injected_fragments:       none
-- tables:
--   reporting.os_display_ads_filtered_level_performance_facts
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          called once per period (current + baseline)
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   total_requests   = sum(total_requests)
--   total_responses  = sum(total_responses)
--   overall_rr       = total_responses * 100 / total_requests
-- =====================================================================

    SELECT
        r.page_type,
        SUM(r.requests) AS total_requests,
        SUM(r.responses) AS total_responses,
        ROUND(
            SAFE_DIVIDE(SUM(r.responses) * 100, NULLIF(SUM(r.requests), 0)),
            2
        ) AS response_rate
    FROM
        `prj-onlinesales-prod-01.reporting.os_display_ads_filtered_level_performance_facts` r
    WHERE
        r.marketplace_client_id = '{marketplace_client_id}'
        AND r.date >= '{start_date}'
        AND r.date <= '{end_date}'
        AND r.page_type IS NOT NULL
        AND TRIM(r.page_type) != ''
    GROUP BY 1
    ORDER BY total_requests DESC
