-- =====================================================================
-- id:                       rr.get_store_level_rr_buckets
-- source:                   tools/rr_analysis_tools.py:1139  (fn get_store_level_rr_buckets)
-- agent:                    rr
-- description:              Store × category × day × hour request/response grain (single period) used to bucket store-hours into zero/partial/full response and compute an eligibility-adjusted RR. Single call.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {marketplace_client_id} str  -> __MARKETPLACE_CLIENT_ID__
--   {start_date}            date -> __START_DATE_1__
--   {end_date}              date -> __END_DATE_1__
-- injected_fragments:                                  (SQL spliced in by branch on program_type)
--   {store_col}     <- pla -> "store_id"  |  display -> "filter_store_id"
--   {response_col}  <- pla -> "non_zero_responses"  |  display -> "responses"
--   {table}         <- pla -> "os_product_ads_filtered_level_report"
--                      display -> "os_display_ads_filtered_level_performance_facts"
--   {safe_pt}       <- page_type_filter with single-quotes stripped (default "category")
-- tables:
--   reporting.os_product_ads_filtered_level_report                  (program_type=pla)
--   reporting.os_display_ads_filtered_level_performance_facts       (program_type=display)
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          single call
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   rr                                    = responses / requests * 100  (per store-hour row)
--   bucket                                = zero_response(<1%) | partial_response(1-99%) | full_response(>99%)
--   rr_buckets                            = groupby(bucket): sum(requests), sum(responses), response_rate
--   overall_rr                            = total_responses / total_requests * 100
--   adjusted_rr_excluding_ineligible      = eligible_responses / eligible_requests * 100  (bucket != zero_response)
--   ineligible_request_pct                = zero_bucket requests / total_requests * 100
--   has_store_eligibility_issue           = ineligible_request_pct > 10
--   diagnosis                             = templated string from the above
-- =====================================================================

    SELECT
        r.{store_col} AS store_id,
        CONCAT(
            COALESCE(r.category_l1, 'na'), ' > ',
            COALESCE(r.category_l2, 'na'), ' > ',
            COALESCE(r.category_l3, 'na')
        ) AS category,
        EXTRACT(DAY FROM r.date_hour) AS day,
        EXTRACT(HOUR FROM r.date_hour) AS hour,
        SUM(r.requests) AS requests,
        SUM(r.{response_col}) AS responses
    FROM `prj-onlinesales-prod-01.reporting.{table}` r
    WHERE r.marketplace_client_id = '{marketplace_client_id}'
        AND r.date BETWEEN '{start_date}' AND '{end_date}'
        AND LOWER(r.page_type) = LOWER('{safe_pt}')
    GROUP BY 1, 2, 3, 4
