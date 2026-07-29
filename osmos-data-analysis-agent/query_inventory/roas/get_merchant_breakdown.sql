-- =====================================================================
-- id:                       roas.get_merchant_breakdown
-- source:                   tools/roi_analysis_tools.py:415  (fn get_merchant_breakdown -> _build_period_query)
-- agent:                    roas
-- description:              Merchant-level PROGRAM (ad-attributed) + SITE (organic) funnel for ONE period, one row per merchant. Same query string is issued once per period; comparison mode runs current + baseline.
-- proposed_kam_report_type: KAM_AGENT_ROAS_MERCHANT_BREAKDOWN
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {agency_id}      str    -> __AGENCY_ID__
--   {period_start}   date   -> __START_DATE_1__   (baseline call -> __START_DATE_2__)
--   {period_end}     date   -> __END_DATE_1__     (baseline call -> __END_DATE_2__)
-- injected_fragments:                                  (SQL spliced in by a helper)
--   {channel_condition}  <- get_channel_filter(program_type or "pla", include_vendor=True)
--                          pla     -> "vendor = 'os_ads' AND channel = 'os_product_ads'"
--                          display -> "vendor = 'os_ads' AND channel IN ('guaranteed_display_ads', 'auction_display_ads')"
--                          all     -> "vendor = 'os_ads' AND channel IN ('os_product_ads', 'guaranteed_display_ads', 'auction_display_ads')"
--                          (appears inside CASE WHEN ... THEN, so vendor is included here)
--   {merchant_filter}    <- built inline from client_ids / seller_ids (optional; default "")
--                          client_ids -> "AND clients.client_id IN ('id1', 'id2', ...)"   (-> __CLIENT_IDS__)
--                          seller_ids -> "AND clients.seller_id IN ('id1', 'id2', ...)"   (-> __SELLER_IDS__)
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
--   per-merchant (_period_metrics):
--     roi             = program_gmv / spend
--     attributed_cvr  = program_orders / program_viewproducts * 100
--     site_cvr        = site_orders / site_viewproducts * 100
--   status            = active_both (spend_current>0 & spend_baseline>0) | new (cur only) | churned (base only)
--   changes.<m>_change      = current - baseline   (program_gmv, program_orders, spend, roi, attributed_cvr, site_gmv, site_orders, site_cvr)
--   changes.<m>_change_pct  = (current - baseline)/baseline * 100   (program_gmv, spend)
--   contribution.program_gmv_share_current_pct   = merchant.program_gmv / total_current.program_gmv * 100
--   contribution.program_gmv_share_baseline_pct  = merchant.program_gmv / total_baseline.program_gmv * 100
--   contribution.contribution_to_program_gmv_change_pct    = merchant program_gmv delta / total program_gmv delta * 100
--   contribution.contribution_to_program_orders_change_pct = merchant program_orders delta / total program_orders delta * 100
--   contribution.contribution_to_spend_change_pct          = merchant spend delta / total spend delta * 100
--   contribution.site_gmv_share_current_pct / site_gmv_share_baseline_pct / contribution_to_site_gmv_change_pct (same shape for site_gmv)
--   user_intent_decline_suspected = _intent_diagnostic(spend flat + program views flat + program GMV down + attributed CVR down)
--   high_impact_merchants  = Pareto vital-few: active_both ranked by current spend desc until cumulative reaches 80%; each gains cumulative_spend_share_pct
--   baseline_avg_roi_threshold = total_baseline.program_gmv / total_baseline.spend
--   new_merchants_below_avg_roi      = status=new & current.roi < baseline_avg_roi_threshold
--   churned_merchants_above_avg_roi  = status=churned & baseline.roi > baseline_avg_roi_threshold
--   summary                = marketplace totals/roi/cvr per period + total_active_both/new/churned + change/change_pct + overall user_intent_diagnostic
-- =====================================================================

SELECT
    base.merchant_name, base.merchant_id, base.os_client_id,
    base.spend, base.clicks, base.program_viewproducts, base.program_add2carts,
    base.program_orders, base.program_gmv,
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
        SUM(CASE WHEN {channel_condition} THEN program_per_click_timestamp_viewproduct ELSE 0 END) AS program_viewproducts,
        SUM(CASE WHEN {channel_condition} THEN program_per_click_timestamp_add_to_cart ELSE 0 END) AS program_add2carts,
        SUM(CASE WHEN {channel_condition} THEN program_per_click_timestamp_conversions ELSE 0 END) AS program_orders,
        SUM(CASE WHEN {channel_condition} THEN program_per_click_timestamp_sales ELSE 0 END) AS program_gmv
    FROM `prj-onlinesales-prod-01.reporting.monetize_merchant_dimensions` mmd
    LEFT JOIN (
        SELECT
            clients.agency_id AS agency_id,
            clients.seller_id AS merchant_id,
            cvcpf.vendor, cvcpf.channel, cvcpf.currency, cvcpf.cost, cvcpf.clicks,
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
WHERE base.merchant_id IS NOT NULL
