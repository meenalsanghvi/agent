-- =====================================================================
-- id:                       rr.get_category_response_rates
-- source:                   tools/rr_analysis_tools.py:276  (fn get_category_response_rates)
-- agent:                    rr
-- description:              Category-level (l1/l2/l3) request/response/RR on non-search pages for ONE period, from the aggregated filtered_level_report. Called once per period; comparison mode runs it for current + baseline.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {agency_id}    str    -> __AGENCY_ID__
--   {start_date}   date   -> __START_DATE_1__   (baseline call -> __START_DATE_2__)
--   {end_date}     date   -> __END_DATE_1__     (baseline call -> __END_DATE_2__)
--   {top_n}        int    -> __LIMIT__          (default 100)
-- injected_fragments:                                  (SQL spliced in by helper/branch)
--   {page_type_clause}  <- default "AND r.page_type != 'SEARCH'"
--                          if page_type given -> "AND LOWER(r.page_type) = LOWER('<safe_pt>')"
--   {category_clauses}  <- appended per provided category filter, e.g.
--                          "AND LOWER(r.category_l1) = LOWER('<l1>')" (also l2, l3)
--   {order_col}         <- sort_by mapped: request | response | response_rate
-- tables:
--   reporting.os_product_ads_filtered_level_report
--   reporting.marketplace_clients
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          called once per period (current + baseline)
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   category_path          = " > ".join([category_l1, category_l2, category_l3] non-empty)
--   response_rate          = round(response_rate, 2)  (SQL SAFE_DIVIDE, filled 0)
--   total_requests         = sum(request)
--   total_responses        = sum(response)
--   overall_response_rate  = total_responses * 100 / total_requests
--   category_count         = len(rows)
-- =====================================================================

    SELECT
        r.page_type,
        r.category_l1,
        r.category_l2,
        r.category_l3,
        SUM(r.requests) AS request,
        SUM(r.non_zero_responses) AS response,
        SAFE_DIVIDE(SUM(r.non_zero_responses) * 100, NULLIF(SUM(r.requests), 0)) AS response_rate
    FROM
        `prj-onlinesales-prod-01.reporting.os_product_ads_filtered_level_report` r
    INNER JOIN
        `prj-onlinesales-prod-01.reporting.marketplace_clients` mc
        ON r.marketplace_client_id = mc.marketplace_client_id
    WHERE
        mc.agency_id = '{agency_id}'
        AND r.date >= '{start_date}'
        AND r.date <= '{end_date}'
        AND r.category_l1 IS NOT NULL AND TRIM(r.category_l1) != ''
        AND r.page_type IS NOT NULL AND r.page_type != '' AND r.page_type != 'NA'
        {page_type_clause}{category_clauses}
    GROUP BY 1, 2, 3, 4
    ORDER BY {order_col} DESC
    LIMIT {top_n}
