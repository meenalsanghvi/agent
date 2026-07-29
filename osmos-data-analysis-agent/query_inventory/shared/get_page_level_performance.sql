-- =====================================================================
-- id:                       shared.get_page_level_performance
-- source:                   tools/common_tools.py:1585  (fn get_page_level_performance -> _page_query)
-- agent:                    shared
-- description:              PLA page-type (search/category/product/...) raw aggregates for one period: requests, responses, impressions, clicks, cost (currency-converted). Called once per period; comparison mode runs it for current + baseline.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {agency_id}  str  -> __AGENCY_ID__
--   {sd}         date -> __START_DATE_1__   (baseline call -> __START_DATE_2__)
--   {ed}         date -> __END_DATE_1__     (baseline call -> __END_DATE_2__)
-- injected_fragments:                                  (none)
-- tables:
--   reporting.os_product_ads_page_name_performance_facts
--   reporting.marketplace_clients
--   reporting.static_currency_conversion
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          called once per period (current + baseline)
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   cpc = cost / clicks
--   ctr = clicks / impressions * 100
--   ir  = impressions / responses   (I/R — impressions served per ad response)
--   -- comparison mode (merge on page_type):
--   cpc_change / cpc_change_pct = current vs baseline
--   ir_change  / ir_change_pct  = current vs baseline
--   spend_share_baseline_pct / spend_share_current_pct = cost / total_cost * 100
--   contribution_to_spend_change_pct  = (cur.cost - base.cost) / total_spend_delta * 100
--   contribution_to_clicks_change_pct = (cur.clicks - base.clicks) / total_clicks_delta * 100
--   summary overall_cpc / overall_ir per period + change; totals per metric
-- =====================================================================

        SELECT
            page_type,
            SUM(requests) AS requests,
            SUM(responses) AS responses,
            SUM(impressions) AS impressions,
            SUM(clicks) AS clicks,
            SUM(cost) AS cost
        FROM (
            SELECT
                pf.page_type,
                COALESCE(SUM(pf.requests), 0) AS requests,
                COALESCE(SUM(pf.non_zero_responses), 0) AS responses,
                COALESCE(SUM(pf.impressions), 0) AS impressions,
                COALESCE(SUM(pf.clicks), 0) AS clicks,
                COALESCE(SUM(pf.cost_usd * scc.conversion_factor), 0) AS cost
            FROM `prj-onlinesales-prod-01.reporting.os_product_ads_page_name_performance_facts` pf
            INNER JOIN `prj-onlinesales-prod-01.reporting.marketplace_clients` mc
                ON pf.marketplace_client_id = mc.marketplace_client_id
            INNER JOIN `prj-onlinesales-prod-01.reporting.static_currency_conversion` scc
                ON scc.from_currency = 'USD' AND scc.to_currency = mc.currency
            WHERE mc.agency_id = '{agency_id}'
                AND pf.date >= '{sd}' AND pf.date <= '{ed}'
                AND pf.page_type IS NOT NULL AND pf.page_type != '' AND pf.page_type != 'NA'
            GROUP BY 1
        ) p
        GROUP BY 1
