-- =====================================================================
-- id:                       cpc.get_merchant_cpc_breakdown
-- source:                   tools/cpc_analysis_tools.py:76  (fn get_merchant_cpc_breakdown -> _period_query)
-- agent:                    cpc
-- description:              Merchant-level PROGRAM (ad) vs SITE (organic) funnel for ONE period, one row per merchant (spend, clicks, impressions, program & site viewproducts/add2carts/orders/GMV). Called once per period; comparison mode runs it for current + baseline.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {agency_id}      str   -> __AGENCY_ID__
--   {period_start}   date  -> __START_DATE_1__   (baseline call -> __START_DATE_2__)
--   {period_end}     date  -> __END_DATE_1__     (baseline call -> __END_DATE_2__)
-- injected_fragments:                                  (SQL spliced in by a helper)
--   {channel_condition}  <- get_channel_filter(program_type, include_vendor=True)  (splices into CASE WHEN inside SELECT, repeated for each metric)
--                          pla     -> "vendor = 'os_ads' AND channel = 'os_product_ads'"
--                          display -> "vendor = 'os_ads' AND channel IN ('guaranteed_display_ads', 'auction_display_ads')"
--   {merchant_filter}    <- built inline from client_ids / seller_ids (empty string if neither)
--                          client_ids -> "AND clients.client_id IN ('c1', 'c2', ...)"
--                          seller_ids -> "AND clients.seller_id IN ('s1', 's2', ...)"
-- tables:
--   reporting.monetize_merchant_dimensions
--   reporting.client_vendor_channel_performance_facts
--   reporting.clients
--   reporting.marketplace_clients
--   reporting.static_currency_conversion
--   reporting.monetize_merchant_facts
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          called once per period (current + baseline)
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   cpc              = spend / clicks
--   ctr              = clicks / impressions * 100
--   cpm              = spend * 1000 / impressions
--   roi              = program_gmv / spend
--   attributed_cvr   = program_orders / program_viewproducts * 100
--   site_cvr         = site_orders / site_viewproducts * 100
--   cpc_change       = cur.cpc - base.cpc
--   cpc_change_pct   = (cur.cpc - base.cpc)/base.cpc * 100
--   spend_change / spend_change_pct / clicks_change / clicks_change_pct = current - baseline (and pct)
--   ctr_change / roi_change / attributed_cvr_change / site_cvr_change   = current - baseline
--   status           = active_both | new | churned   (from spend_current>0 / spend_baseline>0)
--   spend_share_current_pct   = merchant_spend / total_spend * 100   (current & baseline)
--   contribution_to_spend_change_pct  = (cur.spend - base.spend) / marketplace_spend_delta * 100
--   contribution_to_clicks_change_pct = (cur.clicks - base.clicks) / marketplace_clicks_delta * 100
--   high_impact_merchants     = Pareto vital-few (active_both by current spend to 80%), each w/ cumulative_spend_share_pct
--   baseline_avg_cpc_threshold = total_base_spend / total_base_clicks
--   new_merchants_above_avg_cpc     = new merchants w/ current cpc > baseline_avg_cpc
--   churned_merchants_below_avg_cpc = churned merchants w/ baseline cpc < baseline_avg_cpc
--   overall_cpc      = total_spend / total_clicks   (per period)
-- =====================================================================

        SELECT
            base.merchant_name, base.merchant_id, base.os_client_id,
            base.spend, base.clicks, base.impressions,
            base.program_viewproducts, base.program_add2carts, base.program_orders, base.program_gmv,
            COALESCE(org.site_viewproducts, 0) AS site_viewproducts,
            COALESCE(org.site_add2carts, 0) AS site_add2carts,
            COALESCE(org.site_orders, 0) AS site_orders,
            COALESCE(org.site_gmv, 0) AS site_gmv
        FROM (
            SELECT
                mmd.merchant_name AS merchant_name,
                mmd.merchant_id AS merchant_id,
                mmd.client_id AS os_client_id,
                SUM(CASE WHEN {channel_condition} THEN cost * scc.conversion_factor ELSE 0 END) AS spend,
                SUM(CASE WHEN {channel_condition} THEN clicks ELSE 0 END) AS clicks,
                SUM(CASE WHEN {channel_condition} THEN impressions ELSE 0 END) AS impressions,
                SUM(CASE WHEN {channel_condition} THEN program_per_click_timestamp_viewproduct ELSE 0 END) AS program_viewproducts,
                SUM(CASE WHEN {channel_condition} THEN program_per_click_timestamp_add_to_cart ELSE 0 END) AS program_add2carts,
                SUM(CASE WHEN {channel_condition} THEN program_per_click_timestamp_conversions ELSE 0 END) AS program_orders,
                SUM(CASE WHEN {channel_condition} THEN program_per_click_timestamp_sales ELSE 0 END) AS program_gmv
            FROM `prj-onlinesales-prod-01.reporting.monetize_merchant_dimensions` mmd
            LEFT JOIN (
                SELECT
                    clients.agency_id AS agency_id,
                    clients.seller_id AS merchant_id,
                    cvcpf.vendor, cvcpf.channel, cvcpf.currency,
                    cvcpf.cost, cvcpf.clicks, cvcpf.impressions,
                    cvcpf.program_per_click_timestamp_viewproduct,
                    cvcpf.program_per_click_timestamp_add_to_cart,
                    cvcpf.program_per_click_timestamp_conversions,
                    cvcpf.program_per_click_timestamp_sales
                FROM `prj-onlinesales-prod-01.reporting.client_vendor_channel_performance_facts` cvcpf
                INNER JOIN `prj-onlinesales-prod-01.reporting.clients` clients
                    ON clients.client_id = cvcpf.client_id AND clients.agency_id = '{agency_id}'
                INNER JOIN `prj-onlinesales-prod-01.reporting.marketplace_clients` mc
                    ON mc.agency_id = clients.agency_id
                    AND clients.client_id != mc.marketplace_client_id AND mc.agency_id = '{agency_id}'
                WHERE cvcpf.date >= '{period_start}' AND cvcpf.date <= '{period_end}'
                {merchant_filter}
            ) cvcpf
                ON mmd.merchant_id = cvcpf.merchant_id AND mmd.agency_id = cvcpf.agency_id
            LEFT JOIN `prj-onlinesales-prod-01.reporting.marketplace_clients` mc
                ON mmd.agency_id = mc.agency_id AND mc.agency_id = '{agency_id}'
            LEFT JOIN `prj-onlinesales-prod-01.reporting.static_currency_conversion` scc
                ON scc.from_currency = cvcpf.currency AND scc.to_currency = mc.currency
            WHERE mmd.agency_id = '{agency_id}'
            GROUP BY 1, 2, 3
        ) base
        LEFT JOIN (
            SELECT
                mmf.merchant_id AS merchant_id,
                SUM(total_sok_viewproducts) AS site_viewproducts,
                SUM(total_sok_add2carts) AS site_add2carts,
                SUM(total_sok_salecompletes) AS site_orders,
                SUM(total_sok_sales_usd * scc.conversion_factor) AS site_gmv
            FROM `prj-onlinesales-prod-01.reporting.monetize_merchant_facts` mmf
            INNER JOIN `prj-onlinesales-prod-01.reporting.marketplace_clients` mc
                ON mmf.agency_id = mc.agency_id
                AND mmf.marketplace_client_id = mc.marketplace_client_id AND mc.agency_id = '{agency_id}'
            INNER JOIN `prj-onlinesales-prod-01.reporting.static_currency_conversion` scc
                ON scc.from_currency = 'USD' AND scc.to_currency = mc.currency
            WHERE mmf.agency_id = '{agency_id}'
                AND mmf.date >= '{period_start}' AND mmf.date <= '{period_end}'
            GROUP BY 1
        ) org
            ON base.merchant_id = org.merchant_id
        WHERE base.merchant_id IS NOT NULL AND base.spend > 0
