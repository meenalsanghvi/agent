-- =====================================================================
-- id:                       rr.get_search_query_response_rates.pla
-- source:                   tools/rr_analysis_tools.py:1318  (fn get_search_query_response_rates, PLA branch)
-- agent:                    rr
-- description:              Keyword-level request/response/RR on search pages for PLA (timezone-aware search query request report) for ONE period. Called once per period; comparison mode runs it for current + baseline.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {marketplace_client_id} str  -> __MARKETPLACE_CLIENT_ID__
--   {timezone}              str  -> __TIMEZONE__       (required for PLA)
--   {start_date}            date -> __START_DATE_1__   (baseline call -> __START_DATE_2__)
--   {end_date}              date -> __END_DATE_1__     (baseline call -> __END_DATE_2__)
--   {top_n}                 int  -> __LIMIT__          (default 500)
-- injected_fragments:                                  (SQL spliced in by helper)
--   {kw_filter_sql}  <- optional; when keywords_filter given ->
--                       "AND LOWER(TRIM(r.search_query, '[],\",')) IN (LOWER('kw'), ...)" (empty otherwise)
-- tables:
--   reporting.os_product_ads_search_query_request_report
-- region_specific:          false
-- timezone_aware:           true   (DATE(TIMESTAMP(r.date, 'UTC'), '{timezone}'))
-- comparison_mode:          called once per period (current + baseline)
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   pareto_keywords          = top keywords by request cumulatively covering ~80% (skipped when keywords_filter given -> filtered_keywords)
--   total_requests           = sum(request)
--   total_responses          = sum(response)
--   overall_response_rate    = total_responses * 100 / total_requests
--   request_coverage_pct      = result_requests * 100 / total_requests
--   keyword_count            = len(all keyword rows)
-- =====================================================================

        SELECT
            LOWER(TRIM(r.search_query, '[],",')) AS keywords,
            SUM(r.request) AS request,
            SUM(r.response) AS response,
            SAFE_DIVIDE(SUM(r.response) * 100, NULLIF(SUM(r.request), 0)) AS response_rate
        FROM
            `prj-onlinesales-prod-01.reporting.os_product_ads_search_query_request_report` r
        WHERE
            r.marketplace_client_id = '{marketplace_client_id}'
            AND DATE(TIMESTAMP(r.date, 'UTC'), '{timezone}') >= '{start_date}'
            AND DATE(TIMESTAMP(r.date, 'UTC'), '{timezone}') <= '{end_date}'
            AND r.search_query IS NOT NULL
            {kw_filter_sql}
        GROUP BY 1
        ORDER BY request DESC
        LIMIT {top_n}
