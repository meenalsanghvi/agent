-- =====================================================================
-- id:                       rr.check_display_hourly_rr.hourly
-- source:                   tools/rr_analysis_tools.py:1684  (fn check_display_hourly_rr -> hourly_query)
-- agent:                    rr
-- description:              Display requests/responses aggregated per hour-of-day (from date_hour) for ONE period, to surface low-activity hours dragging down RR. Single call.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {marketplace_client_id} str  -> __MARKETPLACE_CLIENT_ID__
--   {start_date}            date -> __START_DATE_1__
--   {end_date}              date -> __END_DATE_1__
-- injected_fragments:       none
-- tables:
--   reporting.os_display_ads_filtered_level_performance_facts
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          single call
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   rr                        = responses / requests * 100  (per hour)
--   overall_rr                = total_responses / total_requests * 100
--   low_activity_hours        = hours where rr < 10
--   adjusted_rr_active_hours  = active_responses / active_requests * 100  (hours with rr >= 10)
--   low_activity_request_pct  = low_hour_requests / total_requests * 100
--   has_hourly_pattern        = len(low_activity_hours) >= 3 AND low_activity_request_pct > 5
-- =====================================================================

    SELECT
        EXTRACT(HOUR FROM r.date_hour) AS hour,
        SUM(r.requests) AS requests,
        SUM(r.responses) AS responses
    FROM `prj-onlinesales-prod-01.reporting.os_display_ads_filtered_level_performance_facts` r
    WHERE r.marketplace_client_id = '{marketplace_client_id}'
        AND r.date BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY 1
    ORDER BY 1
