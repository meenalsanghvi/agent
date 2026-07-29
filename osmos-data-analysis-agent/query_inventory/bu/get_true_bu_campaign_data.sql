-- =====================================================================
-- id:                       bu.get_true_bu_campaign_data
-- source:                   tools/bu_analysis_tools.py:655  (fn get_true_bu_campaign_data -> _build_query)
-- agent:                    bu
-- description:              Campaign-level budget vs spend vs wallet-balance + BU% for ONE period (daily_budget = most-recent-day budget, total_budget = period sum). Called once per period; comparison runs current + baseline.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {agency_id}    str    -> __AGENCY_ID__
--   {start_date}   date   -> __START_DATE_1__   (baseline call -> __START_DATE_2__)
--   {end_date}     date   -> __END_DATE_1__     (baseline call -> __END_DATE_2__)
-- injected_fragments:                                  (SQL spliced in by a helper)
--   {campaign_type_filter}  <- by program_type
--                        pla     -> "AND mcd.campaign_type = 'PERFORMANCE' AND mcd.campaign_subtype IN ('SMART_SHOPPING', 'OS_ADS_SEARCH', 'VIDEO_MIDROLL', 'CAMPAIGN_V2')"
--                        display -> "AND mcd.campaign_type = 'INVENTORY' AND mcd.campaign_subtype = 'AUCTION'"
--                        both    -> "AND mcd.campaign_type IN ('PERFORMANCE', 'INVENTORY') AND mcd.campaign_subtype IN ('SMART_SHOPPING', 'OS_ADS_SEARCH', 'VIDEO_MIDROLL', 'CAMPAIGN_V2', 'AUCTION')"
--   {seller_filter}    <- seller_id set -> "AND cl.seller_id = '{seller_id}'"  else ""
--   {campaign_filter}  <- marketing_campaign_id set -> "AND mcdd.marketing_campaign_id = '{marketing_campaign_id}'"  else ""
--   {status_filter}    <- status set -> "AND mcdd.effective_status = '{status}'"  else ""
-- tables:
--   reporting.marketing_campaign_dimensions_daily
--   reporting.marketing_campaign_dimensions
--   reporting.clients
--   reporting.agencies
--   reporting.static_currency_conversion
--   reporting.client_budget_snapshot
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          called once per period (current + baseline; baseline optional)
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   new / old / paused campaigns              = current_keys - baseline_keys / intersection / baseline_keys - current_keys  (key = client_id+marketing_campaign_id)
--   budget_change                             = daily_budget_current - daily_budget_baseline
--   budget_change_pct                         = budget_change / daily_budget_baseline * 100
--   spend_change                              = ad_spend_current - ad_spend_baseline
--   spend_change_pct                          = spend_change / ad_spend_baseline * 100
--   bu_change                                 = budget_utilization_current - budget_utilization_baseline
--   sellers_with_zero_spend                   = per-seller total_spend == 0
--   budget_drop_net_lost                      = SUM(baseline_daily_budget) - SUM(current_daily_budget) over dropped campaigns
--   overall_budget_change_pct                 = (current_total_budget - baseline_total_budget) / baseline_total_budget * 100
--   overall_spend_change_pct                  = (current_total_spend - baseline_total_spend) / baseline_total_spend * 100
--   baseline_bu_pct                           = baseline_total_spend / baseline_total_budget * 100
--   current_bu_pct                            = current_total_spend / current_total_budget * 100
--   bu_change_pp                              = current_bu_pct - baseline_bu_pct
-- =====================================================================

WITH camp_bud AS (
    SELECT
        mcdd.date, ag.agency_id, cl.client_id,
        mcd.marketing_campaign_id, mcd.alias AS marketing_campaign_name,
        mcdd.effective_status, mcdd.currency,
        ROUND(SUM(CASE
            WHEN mcdd.effective_status = 'ACTIVE'
                THEN mcdd.daily_budget * scc.conversion_factor
            WHEN mcdd.effective_status != 'ACTIVE' AND mcdd.cost > 0
                THEN mcdd.cost * scc.conversion_factor
            ELSE 0
        END), 2) AS daily_budget,
        ROUND(SUM(mcdd.cost * scc.conversion_factor), 2) AS daily_spend
    FROM `prj-onlinesales-prod-01.reporting.marketing_campaign_dimensions_daily` AS mcdd
    JOIN `prj-onlinesales-prod-01.reporting.marketing_campaign_dimensions` AS mcd
        ON mcd.client_id = mcdd.client_id AND mcd.marketing_campaign_id = mcdd.marketing_campaign_id
    JOIN `prj-onlinesales-prod-01.reporting.clients` AS cl
        ON cl.client_id = mcdd.client_id AND cl.agency_id = '{agency_id}'
    JOIN `prj-onlinesales-prod-01.reporting.agencies` AS ag
        ON ag.agency_id = cl.agency_id AND ag.marketplace_client_id != cl.client_id AND ag.agency_id = '{agency_id}'
    JOIN `prj-onlinesales-prod-01.reporting.static_currency_conversion` AS scc
        ON scc.from_currency = mcdd.currency AND scc.to_currency = mcdd.currency
    WHERE 1=1
        {campaign_type_filter}
        AND mcd.campaign_origin != 'PACKAGE_BASED'
        AND mcdd.date >= DATE('{start_date}') AND mcdd.date <= DATE('{end_date}')
        {seller_filter} {campaign_filter} {status_filter}
    GROUP BY 1, 2, 3, 4, 5, 6, 7
)
SELECT
    clients.client_id, clients.seller_id, clients.alias AS merchant_name,
    camp_bud.marketing_campaign_id, camp_bud.marketing_campaign_name, camp_bud.effective_status,
    COALESCE(ROUND(MAX_BY(CASE
        WHEN cbs.remaining_budget_usd IS NOT NULL AND camp_bud.daily_spend IS NOT NULL
            AND camp_bud.daily_spend > (cbs.remaining_budget_usd * scc2.conversion_factor)
            THEN camp_bud.daily_spend
        WHEN cbs.remaining_budget_usd IS NOT NULL
            AND (cbs.remaining_budget_usd * scc2.conversion_factor) <= camp_bud.daily_budget
            THEN (cbs.remaining_budget_usd * scc2.conversion_factor)
        ELSE camp_bud.daily_budget
    END, camp_bud.date), 2), 0) AS daily_budget,
    COALESCE(ROUND(SUM(CASE
        WHEN cbs.remaining_budget_usd IS NOT NULL AND camp_bud.daily_spend IS NOT NULL
            AND camp_bud.daily_spend > (cbs.remaining_budget_usd * scc2.conversion_factor)
            THEN camp_bud.daily_spend
        WHEN cbs.remaining_budget_usd IS NOT NULL
            AND (cbs.remaining_budget_usd * scc2.conversion_factor) <= camp_bud.daily_budget
            THEN (cbs.remaining_budget_usd * scc2.conversion_factor)
        ELSE camp_bud.daily_budget
    END), 2), 0) AS total_budget,
    COALESCE(ROUND(SUM(camp_bud.daily_spend), 2), 0) AS ad_spend,
    COALESCE(ROUND(MAX_BY(cbs.remaining_budget_usd * scc2.conversion_factor, cbs.date), 2), 0) AS wallet_balance,
    COALESCE(ROUND(SAFE_DIVIDE(
        SUM(camp_bud.daily_spend),
        SUM(CASE
            WHEN cbs.remaining_budget_usd IS NOT NULL AND camp_bud.daily_spend IS NOT NULL
                AND camp_bud.daily_spend > (cbs.remaining_budget_usd * scc2.conversion_factor)
                THEN camp_bud.daily_spend
            WHEN cbs.remaining_budget_usd IS NOT NULL
                AND (cbs.remaining_budget_usd * scc2.conversion_factor) <= camp_bud.daily_budget
                THEN (cbs.remaining_budget_usd * scc2.conversion_factor)
            ELSE camp_bud.daily_budget
        END)
    ), 2), 0) AS budget_utilization
FROM camp_bud
JOIN `prj-onlinesales-prod-01.reporting.static_currency_conversion` AS scc2
    ON scc2.from_currency = 'USD' AND scc2.to_currency = camp_bud.currency
JOIN `prj-onlinesales-prod-01.reporting.client_budget_snapshot` AS cbs
    ON cbs.agency_id = camp_bud.agency_id AND cbs.client_id = camp_bud.client_id AND cbs.date = camp_bud.date
JOIN `prj-onlinesales-prod-01.reporting.clients` AS clients
    ON clients.client_id = cbs.client_id AND clients.agency_id = cbs.agency_id
WHERE cbs.date >= DATE('{start_date}') AND cbs.date <= DATE('{end_date}') AND cbs.status = 'ACTIVE'
GROUP BY 1, 2, 3, 4, 5, 6
HAVING daily_budget > 0
ORDER BY ad_spend DESC
