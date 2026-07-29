-- =====================================================================
-- id:                       ctr.get_keyword_seller_breakdown
-- source:                   tools/ctr_analysis_tools.py:777  (fn get_keyword_seller_breakdown -> _build_query)
-- agent:                    ctr
-- description:              Per-(search_query x seller) impressions / clicks / spend / CTR (SQL) plus auto vs manual match-type impression split, from os_ads_search_query_performance_report. PLA only. Called once per period; comparison mode runs it for current + baseline.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {marketplace_client_id}  str  -> __MARKETPLACE_CLIENT_ID__
--   {timezone}               str  -> __TIMEZONE__
--   {s_date}                 date -> __START_DATE_1__   (baseline call -> __START_DATE_2__)
--   {e_date}                 date -> __END_DATE_1__     (baseline call -> __END_DATE_2__)
-- injected_fragments:                                  (SQL spliced in by a helper)
--   {in_clause}      <- built inline from search_queries list (lowercased, single-quote escaped)
--                     -> "'kw1', 'kw2', ..."   (used as LOWER(p.search_query) IN (...))
--   {client_filter}  <- built inline from client_ids / seller_ids (optional; "" when neither given)
--                     client_ids -> "AND p.client_id IN ('<id>', ...)"
--                     seller_ids -> "AND p.merchant_id IN ('<id>', ...)"
-- tables:
--   reporting.os_ads_search_query_performance_report
--   reporting.clients
-- region_specific:          false
-- timezone_aware:           true   (DATE(TIMESTAMP(p.date, 'UTC'), '{timezone}'))
-- comparison_mode:          called once per period (current + baseline)
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   ctr                  = computed in SQL per seller (SAFE_DIVIDE(clicks*100, impressions))
--   status               = existing (imp cur>0 & base>0) | new (cur>0 only) | churned (base>0 only)
--   ctr_change           = current.ctr - baseline.ctr
--   impressions_change   = current.impressions - baseline.impressions
--   clicks_change        = current.clicks - baseline.clicks
--   keyword baseline_ctr = round(kw_baseline_clicks * 100 / kw_baseline_impressions, 2)
--   keyword current_ctr  = round(kw_current_clicks * 100 / kw_current_impressions, 2)
--   keyword ctr_change   = current_ctr - baseline_ctr
--   contribution.impression_share_current_pct  = share_pct(impressions_current, kw_current_impressions)
--   contribution.impression_share_baseline_pct = share_pct(impressions_baseline, kw_baseline_impressions)
--   contribution.contribution_to_impressions_change_pct = contribution_pct(impressions_change, kw_impressions_delta)
--   contribution.contribution_to_clicks_change_pct      = contribution_pct(clicks_change, kw_clicks_delta)
--   new_sellers_below_avg_ctr = status new with ctr_current < keyword baseline_ctr
--   (single-period) keyword ctr = round(kw_clicks * 100 / kw_impressions, 2)
-- =====================================================================

        SELECT
            p.search_query,
            p.client_id AS os_client_id,
            p.merchant_id AS seller_id,
            cl.alias AS merchant_name,
            SUM(p.impressions) AS impressions,
            SUM(p.clicks) AS clicks,
            SUM(p.cost) AS spend,
            COALESCE(SAFE_DIVIDE(SUM(p.clicks) * 100.0, NULLIF(SUM(p.impressions), 0)), 0) AS ctr,
            SUM(CASE WHEN p.keyword_match_type = 'AUTO' THEN p.impressions ELSE 0 END) AS auto_impressions,
            SUM(CASE WHEN p.keyword_match_type != 'AUTO' THEN p.impressions ELSE 0 END) AS manual_impressions
        FROM `prj-onlinesales-prod-01.reporting.os_ads_search_query_performance_report` p
        JOIN `prj-onlinesales-prod-01.reporting.clients` cl
            ON cl.client_id = p.client_id
        WHERE p.marketplace_client_id = '{marketplace_client_id}'
            AND DATE(TIMESTAMP(p.date, 'UTC'), '{timezone}') >= '{s_date}'
            AND DATE(TIMESTAMP(p.date, 'UTC'), '{timezone}') <= '{e_date}'
            AND LOWER(p.search_query) IN ({in_clause})
            {client_filter}
        GROUP BY 1, 2, 3, 4
        ORDER BY search_query, impressions DESC
