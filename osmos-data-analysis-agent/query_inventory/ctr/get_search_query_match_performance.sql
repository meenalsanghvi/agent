-- =====================================================================
-- id:                       ctr.get_search_query_match_performance
-- source:                   tools/ctr_analysis_tools.py:1027  (fn get_search_query_match_performance -> _sov_query)
-- agent:                    ctr
-- description:              Per-(search_query x matched_keyword x match_type) performance inside specific advertiser campaign(s): spend, impressions, clicks, CTR, CPC, CPM, top-of-search impression share, and SOV vs marketplace-wide impressions for that query. Called once per period; comparison mode runs it for current + baseline.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {agency_id}   str    -> __AGENCY_ID__
--   {sd}          date   -> __START_DATE_1__   (baseline call -> __START_DATE_2__)
--   {ed}          date   -> __END_DATE_1__     (baseline call -> __END_DATE_2__)
--   {top_n}       int    -> __LIMIT__
-- injected_fragments:                                  (SQL spliced in by a helper)
--   {client_in}   <- built inline from client_ids list      -> "'c1', 'c2', ..."   (r.client_id / ctd.client_id IN (...))
--   {cid_in}      <- built inline from marketing_campaign_ids list (lowercased) -> "'mc1', ..."  (LOWER(mcd.marketing_campaign_id) IN (...))
--   {sq_filter}   <- built inline from search_queries (optional; "" when omitted)
--                  -> "AND LOWER(r.search_query) IN ('q1', 'q2', ...)"
-- tables:
--   reporting.os_marketplace_search_query_performance_facts
--   reporting.marketplace_clients
--   reporting.os_ads_search_query_performance_report
--   reporting.campaign_tagging_data
--   reporting.marketing_campaign_dimensions
--   reporting.agencies
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          called once per period (current + baseline)
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   spend/ctr/cpc/cpm/top_search_impressions_share/sov = computed in SQL; Python rounds them
--   status               = active_both (imp cur>0 & base>0) | new (cur>0 only) | churned (base>0 only)
--   spend_change         = round(current.spend - baseline.spend, 2)
--   ctr_change           = round(current.ctr - baseline.ctr, 2)
--   cpc_change           = round(current.cpc - baseline.cpc, 2)
--   sov_change           = round(current.sov - baseline.sov, 2)
--   contribution.spend_share_current_pct        = share_pct(spend_current, total_spend_current)
--   contribution.spend_share_baseline_pct       = share_pct(spend_baseline, total_spend_baseline)
--   contribution.impressions_share_current_pct  = share_pct(impressions_current, total_impressions_current)
--   contribution.impressions_share_baseline_pct = share_pct(impressions_baseline, total_impressions_baseline)
--   contribution.contribution_to_spend_change_pct       = contribution_pct(spend_change, total_spend_delta)
--   contribution.contribution_to_impressions_change_pct = contribution_pct(impressions_change, total_impressions_delta)
--   (single-period) match_type_rollup = groupby keyword_match_type -> sum(spend/impressions/clicks),
--                    ctr = round(clicks * 100 / impressions, 2), cpc = round(spend / clicks, 2)
-- =====================================================================

    WITH overall_per_day AS (
      SELECT
        f.date AS overall_date,
        LOWER(f.search_query) AS overall_search_query,
        SUM(f.impressions) AS overall_impressions
      FROM `prj-onlinesales-prod-01.reporting.os_marketplace_search_query_performance_facts` f
      INNER JOIN `prj-onlinesales-prod-01.reporting.marketplace_clients` mc
        ON mc.marketplace_client_id = f.marketplace_client_id
        AND mc.agency_id = '{agency_id}'
      WHERE f.date >= '{sd}' AND f.date <= '{ed}'
      GROUP BY 1, 2
    ),
    overall_totals AS (
      SELECT
        overall_search_query,
        SUM(overall_impressions) AS total_overall_impressions
      FROM overall_per_day
      GROUP BY 1
    ),
    campaign_level AS (
      SELECT
        LOWER(r.search_query) AS search_query,
        r.matched_keyword AS matched_keyword,
        r.keyword_match_type AS keyword_match_type,
        SUM(r.cost) AS spend,
        SUM(r.impressions) AS impressions,
        SUM(r.clicks) AS visits,
        SUM(CASE
          WHEN a.is_impression_ad_position_enabled = TRUE THEN r.top_position_search_impressions
          ELSE r.top_search_keyword_impressions
        END) AS top_search_keyword_impressions
      FROM `prj-onlinesales-prod-01.reporting.os_ads_search_query_performance_report` r
      INNER JOIN `prj-onlinesales-prod-01.reporting.campaign_tagging_data` ctd
        ON ctd.client_id = r.client_id
        AND ctd.account_id = r.account_id
        AND ctd.campaign_id = r.campaign_id
      INNER JOIN `prj-onlinesales-prod-01.reporting.marketing_campaign_dimensions` mcd
        ON ctd.client_id = mcd.client_id
        AND ctd.marketing_campaign_id = mcd.marketing_campaign_id
      INNER JOIN `prj-onlinesales-prod-01.reporting.agencies` a
        ON a.marketplace_client_id = r.marketplace_client_id
      WHERE a.agency_id = '{agency_id}'
        AND r.client_id IN ({client_in})
        AND ctd.client_id IN ({client_in})
        AND LOWER(mcd.marketing_campaign_id) IN ({cid_in})
        AND r.date >= '{sd}' AND r.date <= '{ed}'
        AND (mcd.campaign_origin != 'PACKAGE_BASED' OR mcd.campaign_origin IS NULL)
        {sq_filter}
      GROUP BY 1, 2, 3
    )
    SELECT
      c.search_query,
      c.matched_keyword,
      c.keyword_match_type,
      c.spend,
      c.impressions,
      c.visits AS clicks,
      CASE WHEN c.impressions > 0 THEN SAFE_DIVIDE(c.visits * 100.0, c.impressions) ELSE 0 END AS ctr,
      CASE WHEN c.visits > 0 THEN SAFE_DIVIDE(c.spend, c.visits) ELSE 0 END AS cpc,
      CASE WHEN c.impressions > 0 THEN SAFE_DIVIDE(c.spend * 1000.0, c.impressions) ELSE 0 END AS cpm,
      CASE WHEN c.impressions > 0 THEN SAFE_DIVIDE(c.top_search_keyword_impressions * 100.0, c.impressions) ELSE 0 END AS top_search_impressions_share,
      CASE WHEN t.total_overall_impressions > 0 THEN SAFE_DIVIDE(c.impressions * 100.0, t.total_overall_impressions) ELSE 0 END AS sov
    FROM campaign_level c
    LEFT JOIN overall_totals t ON t.overall_search_query = c.search_query
    ORDER BY c.impressions DESC
    LIMIT {top_n}
