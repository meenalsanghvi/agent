-- =====================================================================
-- id:                       rr.get_search_query_response_rates.display_ad_unit
-- source:                   tools/rr_analysis_tools.py:1399  (fn get_search_query_response_rates, Display keyword x ad_unit breakdown)
-- agent:                    rr
-- description:              Follow-up query (Display only): keyword x ad_unit request/response/RR for the keywords surfaced by the main Display query. Single call after the main Display query.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {marketplace_client_id} str  -> __MARKETPLACE_CLIENT_ID__
--   {start_date}            date -> __START_DATE_1__
--   {end_date}              date -> __END_DATE_1__
-- injected_fragments:                                  (SQL spliced in by helper)
--   {matched_kws}  <- ", ".join("LOWER('<kw>')" for kw in result keyword rows)  -> LOWER(r.filter_keywords) IN (...)
--   {ad_unit_sql}  <- optional; when ad_unit_filter given -> "AND r.ad_unit = '<safe_au>'" (empty otherwise)
-- tables:
--   reporting.os_display_ads_filtered_level_performance_facts
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          single call
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   response_rate                = round(response_rate, 2)  (SQL SAFE_DIVIDE, filled 0)
--   keyword_ad_unit_breakdown    = rows[keywords, ad_unit, request, response, response_rate]
-- =====================================================================

        SELECT
            LOWER(r.filter_keywords) AS keywords,
            r.ad_unit,
            SUM(r.requests) AS request,
            SUM(r.responses) AS response,
            SAFE_DIVIDE(SUM(r.responses) * 100, NULLIF(SUM(r.requests), 0)) AS response_rate
        FROM
            `prj-onlinesales-prod-01.reporting.os_display_ads_filtered_level_performance_facts` r
        WHERE
            r.marketplace_client_id = '{marketplace_client_id}'
            AND r.date >= '{start_date}'
            AND r.date <= '{end_date}'
            AND LOWER(r.filter_keywords) IN ({matched_kws})
            {ad_unit_sql}
        GROUP BY 1, 2
        ORDER BY request DESC
