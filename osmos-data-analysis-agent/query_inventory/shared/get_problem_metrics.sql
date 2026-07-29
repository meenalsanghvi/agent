-- =====================================================================
-- id:                       shared.get_problem_metrics
-- source:                   tools/common_tools.py:1038  (fn get_problem_metrics)
-- agent:                    shared
-- description:              Auto-flagged weekly trend metrics for a marketplace/week from the trend-analysis report: metric, old/new value, change_perc, severity, primary_reason. Single call (one Sunday-Saturday week).
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {marketplace_client_id}  str  -> __MARKETPLACE_CLIENT_ID__
--   {week_start}             date -> __START_DATE_1__   (Sunday; defaults to last completed Sunday)
--   {week_end}               date -> __END_DATE_1__     (Saturday; defaults to last completed Saturday)
-- injected_fragments:                                  (none)
-- tables:
--   reporting.os_ads_performance_trend_analysis_report
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          single call   (side effect: stores current + prior-week baseline into session state)
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   metrics          = all rows
--   flagged_metrics  = rows where lower(severity) != 'normal'
--   severity_breakdown = value_counts(severity)
--   summary.total_metrics / flagged_count
--   baseline_week    = [week_start-7, week_start-1]   (derived in Python, stored to state)
-- =====================================================================

    SELECT
        metric,
        old_value,
        new_value,
        change_perc,
        severity,
        primary_reason
    FROM `prj-onlinesales-prod-01.reporting.os_ads_performance_trend_analysis_report`
    WHERE marketplace_client_id = '{marketplace_client_id}'
        AND DATE(start_date) = '{week_start}'
        AND DATE(end_date) = '{week_end}'
    ORDER BY marketplace_client_id
