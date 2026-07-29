-- =====================================================================
-- id:                       budget_pacing.get_campaign_daily_budget.avg_daily_budget
-- source:                   tools/budget_pacing_tools.py:283  (fn get_campaign_daily_budget -> Path A: avgDailyBudgetEnabled)
-- agent:                    budget_pacing
-- description:              Derived daily budget for a campaign on a date when the marketplace has avgDailyBudgetEnabled. Table date is UTC, so the local date is converted to UTC. Budget in marketplace currency.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {marketplace_client_id}  str   -> __MARKETPLACE_CLIENT_ID__
--   {date}                   date  -> __DATE__
--   {timezone}               str   -> __TIMEZONE__
--   {marketing_campaign_id}  str   -> __MARKETING_CAMPAIGN_ID__
-- injected_fragments:       (none)
-- tables:
--   reporting.os_ads_campaign_avg_daily_budget_projections
-- region_specific:          false
-- timezone_aware:           true                        (DATETIME(TIMESTAMP('{date}', '{timezone}'), 'UTC'))
-- comparison_mode:          single call
-- gating:                   only runs when avgDailyBudgetConfiguration.avgDailyBudgetEnabled == True
--                           (from PropertySettingSvcClient.get_agency_metadata(agency_id))
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   daily_budget  = round(float(df.iloc[0]["derived_daily_budget"]), 2)
--   budget_source = "avg_daily_budget"
-- =====================================================================

SELECT derived_daily_budget
FROM `prj-onlinesales-prod-01.reporting.os_ads_campaign_avg_daily_budget_projections`
WHERE marketplace_client_id = '{marketplace_client_id}'
    AND date = DATETIME(TIMESTAMP('{date}', '{timezone}'), 'UTC')
    AND marketing_campaign_id = '{marketing_campaign_id}'
