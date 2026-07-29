-- =====================================================================
-- id:                       shared.get_search_query_performance
-- source:                   tools/common_tools.py:2223  (fn get_search_query_performance -> _build_query)
-- agent:                    shared
-- description:              PLA search-query (what users TYPED) performance for one period from os_ads_search_query_performance_report: impressions, clicks, spend, ctr, and AUTO-vs-manual impression/click split. Optional per-(query,campaign,merchant,match_type) breakdown. Called once per period; comparison mode runs it for current + baseline.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {marketplace_client_id} str  -> __MARKETPLACE_CLIENT_ID__
--   {timezone}              str  -> __TIMEZONE__
--   {s_date}                date -> __START_DATE_1__   (baseline call -> __START_DATE_2__)
--   {e_date}                date -> __END_DATE_1__     (baseline call -> __END_DATE_2__)
--   {top_n}                 int  -> __LIMIT__
--   {sort_col}              -> "impressions" or "spend" (candidate-pool ORDER BY; change-based sorts re-rank in Python)
-- injected_fragments:                                  (SQL spliced in by a helper/branch)
--   {select_extra} <- breakdown_by=="campaign": ", p.client_id AS os_client_id, p.merchant_id,
--                     ctd.marketing_campaign_id, mcd.effective_status, p.keyword_match_type" (else empty)
--   {group_by}     <- breakdown columns matching select_extra (else "p.search_query")
--   {campaign_join}<- present when breakdown_by=="campaign" OR marketing_campaign_ids set:
--                     JOIN campaign_tagging_data ctd + LEFT JOIN marketing_campaign_dimensions mcd
--   {client_filter}<- client_ids -> "AND p.client_id IN (...)"; else seller_ids -> "AND p.merchant_id IN (...)"
--   {campaign_filter}<- marketing_campaign_ids -> "AND ctd.marketing_campaign_id IN (...)"
--   {sq_filter}    <- search_queries -> "AND LOWER(p.search_query) IN ('q1', 'q2', ...)" (single-quote-escaped, lowercased)
-- tables:
--   reporting.os_ads_search_query_performance_report
--   reporting.campaign_tagging_data            (only via {campaign_join})
--   reporting.marketing_campaign_dimensions    (only via {campaign_join})
-- region_specific:          false
-- timezone_aware:           true   (DATE(TIMESTAMP(p.date, 'UTC'), '{timezone}'))
-- comparison_mode:          called once per period (current + baseline)
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   cpc = spend / clicks
--   cpm = spend * 1000 / impressions
--   ctr = clicks * 100 / impressions   (also computed in SQL as ctr)
--   -- comparison mode (merge on merge_keys; per breakdown):
--   ctr_change / cpc_change / spend_change / impressions_change / clicks_change = current - baseline
--   status (campaign breakdown) = active_both | new | churned   (from impressions_current/baseline)
--   spend_share_current_pct / spend_share_baseline_pct = spend / total_spend * 100
--   contribution_to_spend_change_pct / contribution_to_clicks_change_pct
--   ranking: default current spend; sort_by cpc_change/spend_change re-ranks by |magnitude|
--   new_competitors (campaign breakdown, comparison) = status=='new' rows
--   all_campaign_ids / all_client_ids; paused_campaigns (effective_status != 'ACTIVE')
--   summary: current/baseline total impressions/clicks + overall_ctr; unique_campaigns
-- =====================================================================

        SELECT
            p.search_query
            {select_extra},
            SUM(p.impressions) AS impressions,
            SUM(p.clicks) AS clicks,
            SUM(p.cost) AS spend,
            COALESCE(SAFE_DIVIDE(SUM(p.clicks) * 100.0, NULLIF(SUM(p.impressions), 0)), 0) AS ctr,
            SUM(CASE WHEN p.keyword_match_type = 'AUTO' THEN p.impressions ELSE 0 END) AS auto_impressions,
            SUM(CASE WHEN p.keyword_match_type = 'AUTO' THEN p.clicks ELSE 0 END) AS auto_clicks,
            SUM(CASE WHEN p.keyword_match_type != 'AUTO' THEN p.impressions ELSE 0 END) AS manual_impressions,
            SUM(CASE WHEN p.keyword_match_type != 'AUTO' THEN p.clicks ELSE 0 END) AS manual_clicks
        FROM `prj-onlinesales-prod-01.reporting.os_ads_search_query_performance_report` p
        {campaign_join}
        WHERE p.marketplace_client_id = '{marketplace_client_id}'
            AND DATE(TIMESTAMP(p.date, 'UTC'), '{timezone}') >= '{s_date}'
            AND DATE(TIMESTAMP(p.date, 'UTC'), '{timezone}') <= '{e_date}'
            {client_filter}
            {campaign_filter}
            {sq_filter}
        GROUP BY {group_by}
        ORDER BY {sort_col} DESC
        LIMIT {top_n}
