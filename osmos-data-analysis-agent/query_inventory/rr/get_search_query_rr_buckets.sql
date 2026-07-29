-- =====================================================================
-- id:                       rr.get_search_query_rr_buckets
-- source:                   tools/rr_analysis_tools.py:1463  (fn get_search_query_rr_buckets)
-- agent:                    rr
-- description:              Per-keyword request/response totals on search pages (PLA only, timezone-aware) for ONE period, filtered to keywords with >= min_requests, for Pareto + zero/partial/full RR bucketing. Single call.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {marketplace_client_id} str  -> __MARKETPLACE_CLIENT_ID__
--   {timezone}              str  -> __TIMEZONE__
--   {start_date}            date -> __START_DATE_1__
--   {end_date}              date -> __END_DATE_1__
--   {min_requests}          int  -> __MIN_REQUESTS__  (HAVING threshold, default 50)
-- injected_fragments:       none
-- tables:
--   reporting.os_product_ads_search_query_request_report
-- region_specific:          false
-- timezone_aware:           true   (DATE(TIMESTAMP(r.date, 'UTC'), '{timezone}'))
-- comparison_mode:          single call
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   pareto_df                              = top keywords by requests cumulatively covering ~pareto_coverage (default 0.80)
--   rr                                     = responses / requests * 100  (per keyword)
--   bucket                                 = zero_response(<1%) | partial_response(1-91%) | full_response(>91%)
--   rr_buckets                             = groupby(bucket): keyword_count, requests, responses, response_rate
--   overall_rr                             = total_responses / total_requests * 100  (within Pareto set)
--   adjusted_rr_excluding_zero             = eligible_responses / eligible_requests * 100  (bucket != zero_response)
--   zero_response_request_pct              = zero_requests / total_requests * 100
--   has_keyword_eligibility_issue          = zero_response_request_pct > 10
--   pareto_request_coverage_pct            = total_requests / pre_pareto_total_requests * 100
--   diagnosis                              = templated string from the above
-- =====================================================================

    SELECT
        LOWER(TRIM(r.search_query, '[],",')) AS keyword,
        SUM(r.request) AS requests,
        SUM(r.response) AS responses
    FROM
        `prj-onlinesales-prod-01.reporting.os_product_ads_search_query_request_report` r
    WHERE
        r.marketplace_client_id = '{marketplace_client_id}'
        AND DATE(TIMESTAMP(r.date, 'UTC'), '{timezone}') >= '{start_date}'
        AND DATE(TIMESTAMP(r.date, 'UTC'), '{timezone}') <= '{end_date}'
        AND r.search_query IS NOT NULL
    GROUP BY 1
    HAVING SUM(r.request) >= {min_requests}
    ORDER BY requests DESC
