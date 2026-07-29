-- =====================================================================
-- id:                       ctr.get_merchant_ctr_breakdown
-- source:                   tools/ctr_analysis_tools.py:223  (fn get_merchant_ctr_breakdown -> _build_period_query)
-- agent:                    ctr
-- description:              Merchant-level clicks / impressions / spend / CTR / CPC / CPM for ONE period (CTR/CPC/CPM computed in SQL). Called once per period; comparison mode runs it for current + baseline. Single-period mode appends the ORDER BY / LIMIT tail shown at the bottom.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {agency_id}     str    -> __AGENCY_ID__
--   {period_start}  date   -> __START_DATE_1__   (baseline call -> __START_DATE_2__)
--   {period_end}    date   -> __END_DATE_1__     (baseline call -> __END_DATE_2__)
--   {sort_col}      str    -> __SORT_COLUMN__    (single-period tail only; one of spend/clicks/impressions/ctr/cpc/cpm)
--   {order}         str    -> __SORT_ORDER__     (single-period tail only; ASC | DESC)
--   {top_n}         int    -> __LIMIT__          (single-period tail only)
-- injected_fragments:                                  (SQL spliced in by a helper)
--   {channel_condition}  <- get_channel_filter(program_type, include_vendor=True)
--                        pla     -> "vendor = 'os_ads' AND channel = 'os_product_ads'"
--                        display -> "vendor = 'os_ads' AND channel IN ('guaranteed_display_ads', 'auction_display_ads')"
--                        all     -> "vendor = 'os_ads' AND channel IN ('os_product_ads', 'guaranteed_display_ads', 'auction_display_ads')"
--   {merchant_filter}    <- built inline from client_ids / seller_ids (optional; "" when neither given)
--                        client_ids -> "AND clients.client_id IN ('<id>', ...)"
--                        seller_ids -> "AND clients.seller_id IN ('<id>', ...)"
-- tables:
--   reporting.monetize_merchant_dimensions
--   reporting.client_vendor_channel_performance_facts
--   reporting.clients
--   reporting.marketplace_clients
--   reporting.static_currency_conversion
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          called once per period (current + baseline). Single-period mode: same base query + ORDER BY/LIMIT tail below.
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   ctr / cpc / cpm       = computed in SQL (per-merchant)
--   status               = active_both (imp cur>0 & base>0) | new (cur>0 only) | churned (base>0 only)
--   ctr_change           = ctr_current - ctr_baseline
--   clicks_change        = clicks_current - clicks_baseline
--   impressions_change   = impressions_current - impressions_baseline
--   spend_change         = round(spend_current - spend_baseline, 2)
--   contribution.impression_share_current_pct  = share_pct(impressions_current, total_impressions_current)
--   contribution.impression_share_baseline_pct = share_pct(impressions_baseline, total_impressions_baseline)
--   contribution.click_share_current_pct       = share_pct(clicks_current, total_clicks_current)
--   contribution.click_share_baseline_pct      = share_pct(clicks_baseline, total_clicks_baseline)
--   contribution.contribution_to_clicks_change_pct      = contribution_pct(clicks_change, total_clicks_delta)
--   contribution.contribution_to_impressions_change_pct = contribution_pct(impressions_change, total_impressions_delta)
--   high_impact_merchants (Pareto) = active_both ranked by spend_current desc, smallest set whose cumulative spend >= 80% of active_both spend
--   cumulative_spend_share_pct     = round(cum_spend * 100 / total_active_both_spend, 2)
--   current_overall_ctr  = round(total_clicks_current * 100 / total_impressions_current, 2)
--   baseline_overall_ctr = round(total_clicks_baseline * 100 / total_impressions_baseline, 2)
--   overall_ctr_change   = current_overall_ctr - baseline_overall_ctr
--   baseline_avg_ctr_threshold = check_ctr_overall state value if present, else baseline_overall_ctr
--   new_merchants_below_avg_ctr    = status new    with ctr_current  < baseline_avg_ctr_threshold
--   churned_merchants_above_avg_ctr= status churned with ctr_baseline > baseline_avg_ctr_threshold
--   (single-period) overall_ctr = round(total_clicks * 100 / total_impressions, 2)
-- =====================================================================

        SELECT
            merchant_data.merchant_name,
            merchant_data.merchant_id,
            merchant_data.os_client_id,
            merchant_data.clicks,
            merchant_data.impressions,
            merchant_data.spend,
            CASE
                WHEN merchant_data.impressions > 0
                THEN ROUND(merchant_data.clicks * 100.0 / merchant_data.impressions, 2)
                ELSE 0
            END AS ctr,
            CASE
                WHEN merchant_data.clicks > 0
                THEN ROUND(merchant_data.spend / merchant_data.clicks, 4)
                ELSE 0
            END AS cpc,
            CASE
                WHEN merchant_data.impressions > 0
                THEN ROUND(merchant_data.spend / merchant_data.impressions * 1000, 4)
                ELSE 0
            END AS cpm
        FROM (
            SELECT
                mmd.merchant_name AS merchant_name,
                mmd.merchant_id AS merchant_id,
                mmd.client_id AS os_client_id,
                SUM(CASE
                    WHEN {channel_condition}
                    THEN clicks ELSE 0
                END) AS clicks,
                SUM(CASE
                    WHEN {channel_condition}
                    THEN impressions ELSE 0
                END) AS impressions,
                SUM(CASE
                    WHEN {channel_condition}
                    THEN cost * scc.conversion_factor ELSE 0
                END) AS spend
            FROM `prj-onlinesales-prod-01.reporting.monetize_merchant_dimensions` mmd
            LEFT JOIN (
                SELECT
                    clients.agency_id AS agency_id,
                    clients.seller_id AS merchant_id,
                    cvcpf.date,
                    cvcpf.vendor,
                    cvcpf.channel,
                    cost,
                    clicks,
                    impressions,
                    cvcpf.currency
                FROM `prj-onlinesales-prod-01.reporting.client_vendor_channel_performance_facts` cvcpf
                INNER JOIN `prj-onlinesales-prod-01.reporting.clients` clients
                    ON clients.client_id = cvcpf.client_id
                    AND clients.agency_id = '{agency_id}'
                INNER JOIN `prj-onlinesales-prod-01.reporting.marketplace_clients` mc
                    ON mc.agency_id = clients.agency_id
                    AND clients.client_id != mc.marketplace_client_id
                    AND mc.agency_id = '{agency_id}'
                WHERE cvcpf.date >= '{period_start}' AND cvcpf.date <= '{period_end}'
                {merchant_filter}
            ) cvcpf
                ON mmd.merchant_id = cvcpf.merchant_id
                AND mmd.agency_id = cvcpf.agency_id
            LEFT JOIN `prj-onlinesales-prod-01.reporting.marketplace_clients` mc
                ON mmd.agency_id = mc.agency_id
                AND mc.agency_id = '{agency_id}'
            LEFT JOIN `prj-onlinesales-prod-01.reporting.static_currency_conversion` scc
                ON scc.from_currency = cvcpf.currency
                AND scc.to_currency = mc.currency
            WHERE mmd.agency_id = '{agency_id}'
            GROUP BY 1, 2, 3
        ) merchant_data
        WHERE merchant_data.impressions > 0


-- --- single-period mode appends the following tail (comparison mode omits it) ---
    ORDER BY merchant_data.{sort_col} {order}
    LIMIT {top_n}

