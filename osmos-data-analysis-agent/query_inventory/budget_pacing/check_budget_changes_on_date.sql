-- =====================================================================
-- id:                       budget_pacing.check_budget_changes_on_date
-- source:                   tools/budget_pacing_tools.py:419  (fn check_budget_changes_on_date)
-- agent:                    budget_pacing
-- description:              Audit-log lookup of daily-budget change events (action_type_id 17) for a campaign within a single local day, with old/new value, currency, campaign name, and who changed it.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {agency_id}              str   -> __AGENCY_ID__
--   {marketing_campaign_id}  str   -> __MARKETING_CAMPAIGN_ID__
--   {date}                   date  -> __DATE__
--   {timezone}               str   -> __TIMEZONE__
-- injected_fragments:       (none)
-- tables:
--   audit.audit_logs_v2
-- region_specific:          false
-- timezone_aware:           true                        (DATETIME(timestamp, '{timezone}'); TIMESTAMP('{date}', '{timezone}') window)
-- comparison_mode:          single call
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   has_changes  = not df.empty
--   change_count = len(changes)
--   budget_changes = df.to_dict(orient="records")   (change_time, old_budget, new_budget, currency, campaign_name, changed_by, changed_by_type)
-- =====================================================================

SELECT
    DATETIME(timestamp, '{timezone}') AS change_time,
    JSON_EXTRACT_SCALAR(old_state, '$.dailyBudget') AS old_budget,
    JSON_EXTRACT_SCALAR(new_state, '$.dailyBudget') AS new_budget,
    JSON_EXTRACT_SCALAR(old_state, '$.currency') AS currency,
    JSON_EXTRACT_SCALAR(scope_metadata, '$.campaignName') AS campaign_name,
    JSON_EXTRACT_SCALAR(user, '$.name') AS changed_by,
    JSON_EXTRACT_SCALAR(user, '$.type') AS changed_by_type
FROM `prj-onlinesales-prod-01.audit.audit_logs_v2`
WHERE agency_id = '{agency_id}'
    AND action_type_id = 17
    AND scope_id = '{marketing_campaign_id}'
    AND timestamp >= TIMESTAMP('{date}', '{timezone}')
    AND timestamp < TIMESTAMP(DATE_ADD('{date}', INTERVAL 1 DAY), '{timezone}')
ORDER BY timestamp
