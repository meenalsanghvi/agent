-- =====================================================================
-- id:                       budget_pacing.get_campaign_daily_budget.flexi_budget
-- source:                   tools/budget_pacing_tools.py:313  (fn get_campaign_daily_budget -> Path B: flexi budget fallback)
-- agent:                    budget_pacing
-- description:              Flexi daily budget for a campaign on a date (when avgDailyBudget is disabled): campaign daily budget capped by the merchant wallet's remaining balance. Budget in marketplace currency.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {agency_id}              str   -> __AGENCY_ID__
--   {date}                   date  -> __DATE__
--   {marketing_campaign_id}  str   -> __MARKETING_CAMPAIGN_ID__
-- injected_fragments:       (none)
-- tables:
--   reporting.marketing_campaign_dimensions_daily
--   reporting.marketing_campaign_dimensions
--   reporting.clients
--   reporting.marketplace_clients
--   reporting.static_currency_conversion
--   reporting.client_budget_snapshot
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          single call
-- gating:                   fallback path when avgDailyBudgetConfiguration.avgDailyBudgetEnabled == False
--                           (or PropertySettingSvcClient lookup failed)
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   daily_budget  = round(float(df.iloc[0]["daily_budget"]), 2)
--   budget_source = "flexi_budget"
-- =====================================================================

WITH camp_bud AS (
    SELECT
        cl.client_id,
        mcdd.marketing_campaign_id,
        mcdd.currency,
        ROUND(SUM(CASE
            WHEN mcdd.effective_status = 'ACTIVE'
                THEN mcdd.daily_budget * scc.conversion_factor
            WHEN mcdd.effective_status != 'ACTIVE' AND mcdd.cost > 0
                THEN mcdd.cost * scc.conversion_factor
            ELSE 0
        END), 2) AS daily_budget,
        ROUND(SUM(mcdd.cost * scc.conversion_factor), 2) AS daily_spend
    FROM `prj-onlinesales-prod-01.reporting.marketing_campaign_dimensions_daily` mcdd
    INNER JOIN `prj-onlinesales-prod-01.reporting.marketing_campaign_dimensions` mcd
        ON mcd.client_id = mcdd.client_id
        AND mcd.marketing_campaign_id = mcdd.marketing_campaign_id
    INNER JOIN `prj-onlinesales-prod-01.reporting.clients` cl
        ON cl.client_id = mcdd.client_id
        AND cl.agency_id = '{agency_id}'
    INNER JOIN `prj-onlinesales-prod-01.reporting.marketplace_clients` mc
        ON mc.agency_id = cl.agency_id
        AND cl.client_id != mc.marketplace_client_id
    INNER JOIN `prj-onlinesales-prod-01.reporting.static_currency_conversion` scc
        ON scc.from_currency = mcdd.currency
        AND scc.to_currency = mc.currency
    WHERE mcdd.date = '{date}'
        AND mcdd.marketing_campaign_id = '{marketing_campaign_id}'
        AND mcd.campaign_type IN ('PERFORMANCE', 'INVENTORY')
        AND mcd.campaign_subtype IN (
            'SMART_SHOPPING', 'OS_ADS_SEARCH', 'VIDEO_MIDROLL',
            'CAMPAIGN_V2', 'AUCTION')
        AND mcd.campaign_origin != 'PACKAGE_BASED'
    GROUP BY cl.client_id, mcdd.marketing_campaign_id, mcdd.currency
)
SELECT
    cb.marketing_campaign_id,
    COALESCE(ROUND(SUM(CASE
        WHEN cbs.remaining_budget_usd IS NOT NULL
            AND cb.daily_spend IS NOT NULL
            AND cb.daily_spend > (cbs.remaining_budget_usd * scc_usd.conversion_factor)
            THEN cb.daily_spend
        WHEN cbs.remaining_budget_usd IS NOT NULL
            AND (cbs.remaining_budget_usd * scc_usd.conversion_factor) <= cb.daily_budget
            THEN (cbs.remaining_budget_usd * scc_usd.conversion_factor)
        ELSE cb.daily_budget
    END), 2), 0) AS daily_budget
FROM camp_bud cb
INNER JOIN `prj-onlinesales-prod-01.reporting.marketplace_clients` mc
    ON mc.agency_id = '{agency_id}'
INNER JOIN `prj-onlinesales-prod-01.reporting.static_currency_conversion` scc_usd
    ON scc_usd.from_currency = 'USD'
    AND scc_usd.to_currency = mc.currency
INNER JOIN `prj-onlinesales-prod-01.reporting.client_budget_snapshot` cbs
    ON cbs.agency_id = '{agency_id}'
    AND cbs.client_id = cb.client_id
    AND cbs.date = '{date}'
    AND cbs.status = 'ACTIVE'
GROUP BY cb.marketing_campaign_id
HAVING daily_budget > 0
