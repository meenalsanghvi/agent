-- =====================================================================
-- id:                       cpc.get_campaign_subtype_cpc_breakdown
-- source:                   tools/cpc_analysis_tools.py:334  (fn get_campaign_subtype_cpc_breakdown -> _subtype_query)
-- agent:                    cpc
-- description:              Marketplace-level PLA campaign-subtype BUCKETS (os_ads_search vs smart_shopping vs ...) for ONE period: campaign count, spend, clicks, impressions, program GMV, program orders per subtype. Called once per period; comparison mode runs it for current + baseline.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {agency_id}   str   -> __AGENCY_ID__
--   {sd}          date  -> __START_DATE_1__   (baseline call -> __START_DATE_2__)
--   {ed}          date  -> __END_DATE_1__     (baseline call -> __END_DATE_2__)
-- injected_fragments:                                  (SQL spliced in by a helper)
--   {merchant_filter}  <- built inline from client_ids / seller_ids (empty string if neither)
--                        client_ids -> "AND cl.client_id IN ('c1', 'c2', ...)"
--                        seller_ids -> "AND cl.seller_id IN ('s1', 's2', ...)"
-- tables:
--   reporting.campaign_performance_facts
--   reporting.clients
--   reporting.campaign_tagging_data
--   reporting.marketing_campaign_group_dimensions
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          called once per period (current + baseline)
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   cpc              = spend / clicks
--   ctr              = clicks / impressions * 100
--   cpm              = spend * 1000 / impressions
--   roi              = program_gmv / spend
--   cpc_change       = cur.cpc - base.cpc
--   cpc_change_pct   = (cur.cpc - base.cpc)/base.cpc * 100
--   spend_share_current_pct  = bucket_spend / total_spend * 100   (current & baseline)
--   contribution_to_spend_change_pct  = (cur.spend - base.spend) / marketplace_spend_delta * 100
--   contribution_to_clicks_change_pct = (cur.clicks - base.clicks) / marketplace_clicks_delta * 100
--   overall_cpc      = total_spend / total_clicks   (per period)
--   overall_cpc_change = current_overall_cpc - baseline_overall_cpc
-- =====================================================================

        SELECT
            LOWER(g.campaign_subtype) AS subtype,
            COUNT(DISTINCT cpf.campaign_id) AS campaigns,
            COALESCE(SUM(cpf.cost), 0) AS spend,
            COALESCE(SUM(cpf.clicks), 0) AS clicks,
            COALESCE(SUM(cpf.impressions), 0) AS impressions,
            COALESCE(SUM(cpf.program_per_click_timestamp_sales), 0) AS program_gmv,
            COALESCE(SUM(cpf.program_per_click_timestamp_conversions_multi_channel_onsite_offsite), 0) AS program_orders
        FROM `prj-onlinesales-prod-01.reporting.campaign_performance_facts` cpf
        JOIN `prj-onlinesales-prod-01.reporting.clients` cl
            ON cl.client_id = cpf.client_id AND cl.agency_id = '{agency_id}'
        JOIN `prj-onlinesales-prod-01.reporting.campaign_tagging_data` ctd
            ON ctd.account_id = cpf.account_id AND ctd.campaign_id = cpf.campaign_id AND ctd.client_id = cpf.client_id
        JOIN `prj-onlinesales-prod-01.reporting.marketing_campaign_group_dimensions` g
            ON g.client_id = ctd.client_id AND g.marketing_campaign_group_id = ctd.marketing_campaign_group_id
        WHERE cpf.date >= '{sd}' AND cpf.date <= '{ed}'
            AND LOWER(g.campaign_type) = 'performance'
            AND g.campaign_subtype IS NOT NULL
            {merchant_filter}
        GROUP BY 1
