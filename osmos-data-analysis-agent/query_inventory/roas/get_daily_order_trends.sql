-- =====================================================================
-- id:                       roas.get_daily_order_trends
-- source:                   tools/roi_analysis_tools.py:285  (fn get_daily_order_trends)
-- agent:                    roas
-- description:              Date-level PROGRAM (ad-attributed) vs SITE (organic) funnel for ONE period, one row per date. Called once per period; comparison runs it for current + baseline.
-- proposed_kam_report_type: KAM_AGENT_ROAS_DAILY_ORDER_TRENDS
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {agency_id}    str    -> __AGENCY_ID__
--   {start_date}   date   -> __START_DATE_1__   (baseline call -> __START_DATE_2__)
--   {end_date}     date   -> __END_DATE_1__     (baseline call -> __END_DATE_2__)
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
--   organic_orders   = site_orders - program_orders   (also computed per-row in SQL)
--   date             -> cast to string per daily row
--   totals.<metric>  = SUM over daily rows for each of: spend, clicks, program_orders,
--                      program_gmv, program_viewproducts, program_add2carts, site_orders,
--                      site_revenue, site_viewproducts, site_add2carts, organic_orders
--   totals.actual_roi     = totals.program_gmv / totals.spend
--   totals.attributed_cvr = totals.program_orders / totals.program_viewproducts * 100
--   totals.site_cvr       = totals.site_orders / totals.site_viewproducts * 100
-- =====================================================================

WITH program_data AS (
    SELECT cvcpf.date,
        SUM(cost * scc.conversion_factor) as spend,
        SUM(clicks) as clicks,
        SUM(program_per_click_timestamp_conversions) as program_orders,
        SUM(program_per_click_timestamp_sales) as program_gmv,
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
        AND cvcpf.date >= '{start_date}' AND cvcpf.date <= '{end_date}'
    GROUP BY 1
),
site_data AS (
    SELECT mmf.date,
        SUM(total_sok_salecompletes) as site_orders,
        SUM(total_sok_sales_usd * scc.conversion_factor) as site_revenue,
        SUM(total_sok_viewproducts) as site_viewproducts,
        SUM(total_sok_add2carts) as site_add2carts
    FROM `prj-onlinesales-prod-01.reporting.monetize_merchant_facts` mmf
    INNER JOIN `prj-onlinesales-prod-01.reporting.marketplace_clients` mc
        ON mmf.agency_id = mc.agency_id AND mmf.marketplace_client_id = mc.marketplace_client_id
    INNER JOIN `prj-onlinesales-prod-01.reporting.static_currency_conversion` scc
        ON scc.from_currency = 'USD' AND scc.to_currency = mc.currency
    WHERE mmf.agency_id = '{agency_id}' AND mmf.date >= '{start_date}' AND mmf.date <= '{end_date}'
    GROUP BY 1
)
SELECT
    COALESCE(s.date, p.date) as date,
    COALESCE(p.spend, 0) as spend,
    COALESCE(p.clicks, 0) as clicks,
    COALESCE(p.program_orders, 0) as program_orders,
    COALESCE(p.program_gmv, 0) as program_gmv,
    COALESCE(p.program_viewproducts, 0) as program_viewproducts,
    COALESCE(p.program_add2carts, 0) as program_add2carts,
    COALESCE(s.site_orders, 0) as site_orders,
    COALESCE(s.site_revenue, 0) as site_revenue,
    COALESCE(s.site_viewproducts, 0) as site_viewproducts,
    COALESCE(s.site_add2carts, 0) as site_add2carts,
    COALESCE(s.site_orders, 0) - COALESCE(p.program_orders, 0) as organic_orders
FROM site_data s
FULL OUTER JOIN program_data p ON s.date = p.date
ORDER BY date
