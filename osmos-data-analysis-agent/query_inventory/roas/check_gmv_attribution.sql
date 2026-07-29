-- =====================================================================
-- id:                       roas.check_gmv_attribution
-- source:                   tools/roi_analysis_tools.py:154  (fn check_gmv_attribution -> _overall)
-- agent:                    roas
-- description:              Marketplace-level PROGRAM (ad-attributed) vs SITE (organic) funnel for ONE period. Called once per period; comparison mode runs it for current + baseline.
-- proposed_kam_report_type: KAM_AGENT_ROAS_GMV_ATTRIBUTION
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {agency_id}   str    -> __AGENCY_ID__
--   {sd}          date   -> __START_DATE_1__   (baseline call -> __START_DATE_2__)
--   {ed}          date   -> __END_DATE_1__     (baseline call -> __END_DATE_2__)
-- injected_fragments:                                  (SQL spliced in by a helper)
--   {channel_filter}  <- get_channel_filter(program_type)
--                        pla     -> "channel = 'os_product_ads'"
--                        display -> "channel IN ('guaranteed_display_ads', 'auction_display_ads')"
--                        all     -> "channel IN ('os_product_ads', 'guaranteed_display_ads', 'auction_display_ads')"
-- tables:
--   reporting.client_vendor_channel_performance_facts
--   reporting.clients
--   reporting.marketplace_clients
--   reporting.static_currency_conversion
--   reporting.monetize_merchant_facts
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          called once per period (current + baseline)
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   organic_gmv      = site_revenue - program_gmv
--   organic_orders   = site_orders - program_orders
--   actual_roi       = program_gmv / spend
--   attributed_cvr   = program_orders / program_viewproducts * 100
--   site_cvr         = site_orders / site_viewproducts * 100
--   <metric>_change      = current - baseline           (per change_metric)
--   <metric>_change_pct  = (current - baseline)/baseline * 100
--   trend_verdict          (program attributed-CVR trend vs organic site-CVR trend)
--   user_intent_diagnostic (spend flat + views flat + GMV down + CVR down)
-- =====================================================================

WITH program_data AS (
    SELECT cvcpf.date,
        SUM(cost * scc.conversion_factor) as spend,
        SUM(impressions) as impressions,
        SUM(clicks) as clicks,
        SUM(program_per_click_timestamp_sales) as program_gmv,
        SUM(program_per_click_timestamp_conversions) as program_orders,
        SUM(program_per_click_timestamp_viewproduct) as program_viewproducts,
        SUM(program_per_click_timestamp_add_to_cart) as program_add2carts
    FROM `prj-onlinesales-prod-01.reporting.client_vendor_channel_performance_facts` cvcpf
    INNER JOIN `prj-onlinesales-prod-01.reporting.clients` clients
        ON clients.client_id = cvcpf.client_id AND clients.agency_id = '{agency_id}'
    INNER JOIN `prj-onlinesales-prod-01.reporting.marketplace_clients` mc
        ON mc.agency_id = clients.agency_id AND clients.client_id != mc.marketplace_client_id
    INNER JOIN `prj-onlinesales-prod-01.reporting.static_currency_conversion` scc
        ON scc.from_currency = cvcpf.currency AND scc.to_currency = mc.currency
    WHERE cvcpf.vendor = 'os_ads' AND {channel_filter}
        AND cvcpf.date >= '{sd}' AND cvcpf.date <= '{ed}'
    GROUP BY 1
),
site_data AS (
    SELECT mmf.date,
        SUM(total_sok_sales_usd * scc.conversion_factor) as site_revenue,
        SUM(total_sok_salecompletes) as site_orders,
        SUM(total_sok_viewproducts) as site_viewproducts,
        SUM(total_sok_add2carts) as site_add2carts
    FROM `prj-onlinesales-prod-01.reporting.monetize_merchant_facts` mmf
    INNER JOIN `prj-onlinesales-prod-01.reporting.marketplace_clients` mc
        ON mmf.agency_id = mc.agency_id AND mmf.marketplace_client_id = mc.marketplace_client_id
    INNER JOIN `prj-onlinesales-prod-01.reporting.static_currency_conversion` scc
        ON scc.from_currency = 'USD' AND scc.to_currency = mc.currency
    WHERE mmf.agency_id = '{agency_id}' AND mmf.date >= '{sd}' AND mmf.date <= '{ed}'
    GROUP BY 1
)
SELECT
    SUM(COALESCE(p.spend,0)) as spend,
    SUM(COALESCE(p.impressions,0)) as impressions,
    SUM(COALESCE(p.clicks,0)) as clicks,
    SUM(COALESCE(p.program_gmv,0)) as program_gmv,
    SUM(COALESCE(p.program_orders,0)) as program_orders,
    SUM(COALESCE(p.program_viewproducts,0)) as program_viewproducts,
    SUM(COALESCE(p.program_add2carts,0)) as program_add2carts,
    SUM(COALESCE(s.site_revenue,0)) as site_revenue,
    SUM(COALESCE(s.site_orders,0)) as site_orders,
    SUM(COALESCE(s.site_viewproducts,0)) as site_viewproducts,
    SUM(COALESCE(s.site_add2carts,0)) as site_add2carts
FROM site_data s
FULL OUTER JOIN program_data p ON s.date = p.date
