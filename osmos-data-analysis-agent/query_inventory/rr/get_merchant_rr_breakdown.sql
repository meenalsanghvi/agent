-- =====================================================================
-- id:                       rr.get_merchant_rr_breakdown
-- source:                   tools/rr_analysis_tools.py:398  (fn get_merchant_rr_breakdown -> _period_query)
-- agent:                    rr
-- description:              Per-merchant spend/clicks/impressions for ONE period (merchant × currency-converted). One query literal; called once (single period) or twice (comparison: current + baseline).
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {agency_id}   str    -> __AGENCY_ID__
--   {sd}          date   -> __START_DATE_1__   (baseline call -> __START_DATE_2__)
--   {ed}          date   -> __END_DATE_1__     (baseline call -> __END_DATE_2__)
-- injected_fragments:                                  (SQL spliced in by a helper)
--   {channel_condition}  <- get_channel_filter(program_type, include_vendor=True)
--                          pla     -> "vendor = 'os_ads' AND channel = 'os_product_ads'"
--                          display -> "vendor = 'os_ads' AND channel IN ('guaranteed_display_ads', 'auction_display_ads')"
--                          all     -> "vendor = 'os_ads' AND channel IN ('os_product_ads', 'guaranteed_display_ads', 'auction_display_ads')"
--   {merchant_filter}    <- optional; "AND clients.client_id IN (...)" or "AND clients.seller_id IN (...)" (empty by default)
-- tables:
--   reporting.monetize_merchant_dimensions
--   reporting.client_vendor_channel_performance_facts
--   reporting.clients
--   reporting.marketplace_clients
--   reporting.static_currency_conversion
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          single call (single period) | called once per period (comparison: current + baseline)
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   ctr                                       = ctr_ratio(clicks, impressions)  (clicks/impressions*100)
--   status                                    = active_both | new | churned  (impressions_current/baseline > 0)
--   impressions_change                        = impressions_current - impressions_baseline
--   impressions_change_pct                    = pct_change(impressions_current, impressions_baseline)
--   clicks_change                             = clicks_current - clicks_baseline
--   ctr_change                                = ctr_current - ctr_baseline
--   impression_share_current_pct              = share_pct(impressions_current, total_impressions_current)
--   impression_share_baseline_pct             = share_pct(impressions_baseline, total_impressions_baseline)
--   contribution_to_impressions_change_pct    = contribution_pct(impressions_delta, total_impressions_delta)
--   contribution_to_clicks_change_pct         = contribution_pct(clicks_delta, total_clicks_delta)
--   high_impact_merchants                     = pareto_high_impact(records)  (top current spenders to 80% of active_both spend)
--   merchants (drivers)                       = sorted by |contribution_to_impressions_change_pct| desc, top_n
--   pre_period_top_contributors               = baseline impressions>0 sorted by impression_share_baseline_pct desc, top_n
--   new_merchants                             = status=='new' sorted by current impressions desc, top_n
-- =====================================================================

        SELECT
            mmd.merchant_name, mmd.merchant_id, mmd.client_id AS os_client_id,
            ROUND(SUM(CASE WHEN {channel_condition} THEN cost * scc.conversion_factor ELSE 0 END), 2) AS spend,
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
        HAVING impressions > 0
