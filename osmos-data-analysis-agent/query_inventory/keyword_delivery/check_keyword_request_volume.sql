-- =====================================================================
-- id:                       keyword_delivery.check_keyword_request_volume
-- source:                   tools/keyword_delivery_tools.py:47  (fn check_keyword_request_volume)
-- agent:                    keyword_delivery
-- description:              Per-keyword request volume over the trailing 7-day window for a marketplace, used to decide if a keyword has enough demand (>100 requests) to warrant a category.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {marketplace_client_id}  str    -> __MARKETPLACE_CLIENT_ID__
--   {timezone}               str    -> __TIMEZONE__
--   {end_date}               date   -> __END_DATE_1__   (start = end_date - 6 days, via DATE_SUB in SQL)
-- injected_fragments:                                  (SQL spliced in by a helper)
--   {in_clause}  <- ", ".join(f"LOWER('{q}')" for q in sanitized)
--                   where sanitized = [q.replace("'", "\\'") for q in search_queries]
--                   e.g. "LOWER('running shoes'), LOWER('yoga mat')"
-- tables:
--   reporting.os_product_ads_search_query_request_report
-- region_specific:          false
-- timezone_aware:           true   (DATE(TIMESTAMP(r.date, 'UTC'), '{timezone}'))
-- comparison_mode:          single call
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   meets_threshold          = total_requests > 100                     (THRESHOLD = 100)
--   found_keywords           = set of keyword values returned by the query
--   not_found                = {q.lower() for q in search_queries} - found_keywords   (each emitted with total_requests=0, days_with_requests=0, meets_threshold=False)
--   above_threshold          = list of keywords where meets_threshold is True
--   below_threshold          = list of keywords where meets_threshold is False (includes not_found)
--   keywords_above_threshold = len(above_threshold)
--   keywords_below_threshold = len(below_threshold)
-- =====================================================================

    SELECT
        LOWER(TRIM(r.search_query, '[],",')) AS keyword,
        SUM(r.request) AS total_requests,
        COUNT(DISTINCT DATE(TIMESTAMP(r.date, 'UTC'), '{timezone}')) AS days_with_requests
    FROM `prj-onlinesales-prod-01.reporting.os_product_ads_search_query_request_report` r
    WHERE r.marketplace_client_id = '{marketplace_client_id}'
        AND DATE(TIMESTAMP(r.date, 'UTC'), '{timezone}') >= DATE_SUB('{end_date}', INTERVAL 6 DAY)
        AND DATE(TIMESTAMP(r.date, 'UTC'), '{timezone}') <= '{end_date}'
        AND LOWER(TRIM(r.search_query, '[],",')) IN ({in_clause})
    GROUP BY 1
    ORDER BY total_requests DESC
