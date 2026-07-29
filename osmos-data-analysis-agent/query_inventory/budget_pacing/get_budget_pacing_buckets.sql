-- =====================================================================
-- id:                       budget_pacing.get_budget_pacing_buckets
-- source:                   tools/budget_pacing_tools.py:187  (fn get_budget_pacing_buckets)
-- agent:                    budget_pacing
-- description:              Fetch the raw budget-pacing JSON (cumulative spend % targets by time-of-day) for a marketplace on a given date.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {marketplace_client_id}  str   -> __MARKETPLACE_CLIENT_ID__
--   {date}                   date  -> __DATE__
-- injected_fragments:       (none)
-- tables:
--   reporting.os_ads_marketplace_budget_pacing_configurations
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          single call
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   pacing_map    = json.loads(budget_pacing_json) if str else budget_pacing_json
--   bucket_pct    = cumulative_pct - prev_cumulative                (per pacing_map entry)
--   start_time    = prev bucket end_time + 1 second (HH:MM:SS)
--   bucket_count  = len(buckets)
-- =====================================================================

SELECT budget_pacing_json
FROM `prj-onlinesales-prod-01.reporting.os_ads_marketplace_budget_pacing_configurations`
WHERE marketplace_client_id = '{marketplace_client_id}'
    AND date = '{date}'
