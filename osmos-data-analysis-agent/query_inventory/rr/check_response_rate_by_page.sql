-- =====================================================================
-- id:                       rr.check_response_rate_by_page
-- source:                   tools/rr_analysis_tools.py:79  (fn check_response_rate_by_page)
-- agent:                    rr
-- description:              Response rate (responses/requests) broken down by page type for ONE period. Called once per period; comparison mode runs it for current + baseline.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {agency_id}    str    -> __AGENCY_ID__
--   {start_date}   date   -> __START_DATE_1__   (baseline call -> __START_DATE_2__)
--   {end_date}     date   -> __END_DATE_1__     (baseline call -> __END_DATE_2__)
-- injected_fragments:                                  (SQL spliced in by branch on program_type)
--   {table}         <- program_type branch
--                      pla     -> "`prj-onlinesales-prod-01.reporting.os_product_ads_page_name_performance_facts`"
--                      display -> "`prj-onlinesales-prod-01.reporting.os_display_ads_ad_unit_facts`"
--   {extra_filters} <- program_type branch
--                      pla     -> "AND auf.page_type IS NOT NULL AND auf.page_type NOT IN ('', 'NA')"
--                      display -> "AND auf.page_type IS NOT NULL AND TRIM(auf.page_type) NOT IN ('', 'NA')"
-- tables:
--   reporting.os_product_ads_page_name_performance_facts   (program_type=pla)
--   reporting.os_display_ads_ad_unit_facts                 (program_type=display)
--   reporting.marketplace_clients
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          called once per period (current + baseline)
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   total_requests         = sum(requests)
--   total_responses        = sum(responses)
--   overall_response_rate  = total_responses * 100 / total_requests
-- =====================================================================

    SELECT
        auf.page_type,
        SUM(auf.requests) AS requests,
        SUM(auf.non_zero_responses) AS responses,
        ROUND(SAFE_DIVIDE(SUM(auf.non_zero_responses) * 100, NULLIF(SUM(auf.requests), 0)), 2) AS response_rate
    FROM {table} AS auf
    JOIN `prj-onlinesales-prod-01.reporting.marketplace_clients` AS mc
        ON auf.marketplace_client_id = mc.marketplace_client_id
    WHERE
        auf.date >= '{start_date}' AND auf.date <= '{end_date}'
        AND mc.agency_id = '{agency_id}'
        {extra_filters}
    GROUP BY 1
    ORDER BY requests DESC
