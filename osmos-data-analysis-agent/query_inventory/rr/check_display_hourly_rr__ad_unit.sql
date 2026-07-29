-- =====================================================================
-- id:                       rr.check_display_hourly_rr.ad_unit
-- source:                   tools/rr_analysis_tools.py:1697  (fn check_display_hourly_rr -> ad_unit_query)
-- agent:                    rr
-- description:              Display requests/responses aggregated per ad_unit for ONE period, to flag ad units with zero responses (no active campaigns). Single call alongside the hourly query.
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
--   rr                            = responses / requests * 100  (per ad_unit)
--   ad_units_without_campaigns    = rows where responses == 0  [ad_unit, requests]
-- =====================================================================

    SELECT
        r.ad_unit,
        SUM(r.requests) AS requests,
        SUM(r.responses) AS responses
    FROM `prj-onlinesales-prod-01.reporting.os_display_ads_filtered_level_performance_facts` r
    WHERE r.marketplace_client_id = '{marketplace_client_id}'
        AND r.date BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY 1
    ORDER BY requests DESC
