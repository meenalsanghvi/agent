-- =====================================================================
-- id:                       bu.get_merchant_bu_breakdown
-- source:                   tools/bu_analysis_tools.py:451  (fn get_merchant_bu_breakdown -> _period_query)
-- agent:                    bu
-- description:              Per-merchant spend / clicks / impressions for ONE period (spend > 0). Called once per period; comparison mode runs it for current + baseline.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {agency_id}   str    -> __AGENCY_ID__
--   {sd}          date   -> __START_DATE_1__   (baseline call -> __START_DATE_2__)
--   {ed}          date   -> __END_DATE_1__     (baseline call -> __END_DATE_2__)
-- injected_fragments:                                  (SQL spliced in by a helper)
--   {channel_condition}  <- get_channel_filter(program_type, include_vendor=True)  (appears 3x inside CASE WHEN)
--                        pla     -> "vendor = 'os_ads' AND channel = 'os_product_ads'"
--                        display -> "vendor = 'os_ads' AND channel IN ('guaranteed_display_ads', 'auction_display_ads')"
--                        all     -> "vendor = 'os_ads' AND channel IN ('os_product_ads', 'guaranteed_display_ads', 'auction_display_ads')"
--   {merchant_filter}    <- optional merchant scope from client_ids / seller_ids
--                        client_ids -> "AND clients.client_id IN ('id', ...)"
--                        seller_ids -> "AND clients.seller_id IN ('id', ...)"
--                        else       -> ""
-- tables:
--   reporting.monetize_merchant_dimensions
--   reporting.client_vendor_channel_performance_facts
--   reporting.clients
--   reporting.marketplace_clients
--   reporting.static_currency_conversion
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          called once per period (current + baseline)
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   status                                    = active_both | new | churned (spend_current/baseline > 0)
--   spend_change                              = spend_current - spend_baseline
--   spend_change_pct                          = pct_change(spend_current, spend_baseline)
--   impressions_change                        = impressions_current - impressions_baseline
--   clicks_change                             = clicks_current - clicks_baseline
--   spend_share_current_pct                   = share_pct(spend_current, total_current_spend)
--   spend_share_baseline_pct                  = share_pct(spend_baseline, total_baseline_spend)
--   contribution_to_spend_change_pct          = contribution_pct(spend_current - spend_baseline, total_spend_delta)
--   contribution_to_impressions_change_pct    = contribution_pct(impressions_current - impressions_baseline, total_impressions_delta)
--   high_impact_merchants                     = pareto_high_impact(records)  (top current spenders cumulatively to 80%)
--   drivers                                   = records sorted by |contribution_to_spend_change_pct| desc
--   summary.spend_change_pct                  = pct_change(total_current_spend, total_baseline_spend)
-- =====================================================================

SELECT
    merchant_data.merchant_name, merchant_data.merchant_id, merchant_data.os_client_id,
    merchant_data.spend, merchant_data.clicks, merchant_data.impressions
FROM (
    SELECT
        mmd.merchant_name AS merchant_name,
        mmd.merchant_id AS merchant_id,
        mmd.client_id AS os_client_id,
        SUM(CASE WHEN {channel_condition} THEN cost * scc.conversion_factor ELSE 0 END) AS spend,
        SUM(CASE WHEN {channel_condition} THEN clicks ELSE 0 END) AS clicks,
        SUM(CASE WHEN {channel_condition} THEN impressions ELSE 0 END) AS impressions
    FROM `prj-onlinesales-prod-01.reporting.monetize_merchant_dimensions` mmd
    LEFT JOIN (
        SELECT
            clients.agency_id AS agency_id, clients.seller_id AS merchant_id,
            cvcpf.date, cvcpf.vendor, cvcpf.channel, cost, clicks, impressions, cvcpf.currency
        FROM `prj-onlinesales-prod-01.reporting.client_vendor_channel_performance_facts` cvcpf
        INNER JOIN `prj-onlinesales-prod-01.reporting.clients` clients
            ON clients.client_id = cvcpf.client_id AND clients.agency_id = '{agency_id}'
        INNER JOIN `prj-onlinesales-prod-01.reporting.marketplace_clients` mc
            ON mc.agency_id = clients.agency_id
            AND clients.client_id != mc.marketplace_client_id AND mc.agency_id = '{agency_id}'
        WHERE cvcpf.date >= '{sd}' AND cvcpf.date <= '{ed}'
        {merchant_filter}
    ) cvcpf
        ON mmd.merchant_id = cvcpf.merchant_id AND mmd.agency_id = cvcpf.agency_id
    LEFT JOIN `prj-onlinesales-prod-01.reporting.marketplace_clients` mc
        ON mmd.agency_id = mc.agency_id AND mc.agency_id = '{agency_id}'
    LEFT JOIN `prj-onlinesales-prod-01.reporting.static_currency_conversion` scc
        ON scc.from_currency = cvcpf.currency AND scc.to_currency = mc.currency
    WHERE mmd.agency_id = '{agency_id}'
    GROUP BY 1, 2, 3
) merchant_data
WHERE merchant_data.spend > 0
