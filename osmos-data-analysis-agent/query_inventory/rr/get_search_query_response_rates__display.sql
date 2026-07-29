-- =====================================================================
-- id:                       rr.get_search_query_response_rates.display
-- source:                   tools/rr_analysis_tools.py:1295  (fn get_search_query_response_rates, Display branch)
-- agent:                    rr
-- description:              Keyword-level (filter_keywords) request/response/RR for Display (filtered_level_performance_facts) for ONE period. Called once per period; comparison mode runs it for current + baseline.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {marketplace_client_id} str  -> __MARKETPLACE_CLIENT_ID__
--   {start_date}            date -> __START_DATE_1__   (baseline call -> __START_DATE_2__)
--   {end_date}              date -> __END_DATE_1__     (baseline call -> __END_DATE_2__)
--   {top_n}                 int  -> __LIMIT__          (default 500)
-- injected_fragments:                                  (SQL spliced in by helper)
--   {kw_filter_sql}  <- optional; when keywords_filter given ->
--                       "AND LOWER(r.filter_keywords) IN (LOWER('kw'), ...)" (empty otherwise)
--   {ad_unit_sql}    <- optional; when ad_unit_filter given -> "AND r.ad_unit = '<safe_au>'" (empty otherwise)
-- tables:
--   reporting.os_display_ads_filtered_level_performance_facts
-- region_specific:          false
-- timezone_aware:           false
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
            LOWER(r.filter_keywords) AS keywords,
            SUM(r.requests) AS request,
            SUM(r.responses) AS response,
            SAFE_DIVIDE(SUM(r.responses) * 100, NULLIF(SUM(r.requests), 0)) AS response_rate
        FROM
            `prj-onlinesales-prod-01.reporting.os_display_ads_filtered_level_performance_facts` r
        WHERE
            r.marketplace_client_id = '{marketplace_client_id}'
            AND r.date >= '{start_date}'
            AND r.date <= '{end_date}'
            AND r.filter_keywords IS NOT NULL
            AND TRIM(r.filter_keywords) != ''
            {kw_filter_sql}
            {ad_unit_sql}
        GROUP BY 1
        ORDER BY request DESC
        LIMIT {top_n}
