-- =====================================================================
-- id:                       rr.get_response_rate_by_dimension
-- source:                   tools/rr_analysis_tools.py:847  (fn get_response_rate_by_dimension)
-- agent:                    rr
-- description:              Request/response/RR grouped by one or more allowed dimension columns (network, store_id, page_type, categories, ad_unit, ...) for ONE period. Called once per period; comparison mode runs it for current + baseline.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {marketplace_client_id} str  -> __MARKETPLACE_CLIENT_ID__
--   {start_date}            date -> __START_DATE_1__   (baseline call -> __START_DATE_2__)
--   {end_date}              date -> __END_DATE_1__     (baseline call -> __END_DATE_2__)
--   {top_n}                 int  -> __LIMIT__          (default 50)
-- injected_fragments:                                  (SQL spliced in by helper/branch)
--   {select_cols}       <- ", ".join("r.{c} AS {c}" for c in group-by cols)
--   {null_checks}       <- " AND ".join("r.{c} IS NOT NULL AND TRIM(CAST(r.{c} AS STRING)) != ''")
--   {group_by_indices}  <- "1, 2, ..." for the group-by cols
--   {response_col}      <- program_type: pla -> "non_zero_responses" | display -> "responses"
--   {table}             <- program_type: pla -> "os_product_ads_filtered_level_report"
--                          display -> "os_display_ads_filtered_level_performance_facts"
--   {filter_sql}        <- optional AND filters (page_type/network/store_id/ad_unit/category_l1..l3), newline-joined
-- tables:
--   reporting.os_product_ads_filtered_level_report                  (program_type=pla)
--   reporting.os_display_ads_filtered_level_performance_facts       (program_type=display)
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          called once per period (current + baseline)
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   response_rate          = round(response_rate, 2)  (SQL SAFE_DIVIDE, filled 0)
--   dimension_value        = rename of single group-by col (single-column mode only)
--   total_requests         = sum(request)
--   total_responses        = sum(response)
--   overall_response_rate  = total_responses * 100 / total_requests
--   dimension_count        = len(rows)
-- =====================================================================

    SELECT
        {select_cols},
        SUM(r.requests) AS request,
        SUM(r.{response_col}) AS response,
        SAFE_DIVIDE(
            SUM(r.{response_col}) * 100,
            NULLIF(SUM(r.requests), 0)
        ) AS response_rate
    FROM `prj-onlinesales-prod-01.reporting.{table}` r
    WHERE
        r.marketplace_client_id = '{marketplace_client_id}'
        AND r.date >= '{start_date}'
        AND r.date <= '{end_date}'
        AND {null_checks}
        {filter_sql}
    GROUP BY {group_by_indices}
    ORDER BY request DESC
    LIMIT {top_n}
