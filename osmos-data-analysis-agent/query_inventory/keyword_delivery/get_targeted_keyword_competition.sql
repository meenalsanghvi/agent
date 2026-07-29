-- =====================================================================
-- id:                       keyword_delivery.get_targeted_keyword_competition
-- source:                   tools/keyword_delivery_tools.py:435  (fn get_targeted_keyword_competition -> _period_query)
-- agent:                    keyword_delivery
-- description:              Per-campaign competition on a targeted keyword across the whole marketplace for ONE period: every campaign that served the keyword with spend, impressions, clicks, CPC, CPM, CTR, attributed sales, ROI, plus campaign_name/effective_status/creation_date. Top N by impressions.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {agency_id}   str    -> __AGENCY_ID__
--   {sd}          date   -> __START_DATE_1__   (baseline call -> __START_DATE_2__)
--   {ed}          date   -> __END_DATE_1__     (baseline call -> __END_DATE_2__)
--   {top_n}       int    -> __LIMIT__          (default 25)
-- injected_fragments:                                  (SQL spliced in by a helper)
--   {kw_in}           <- ", ".join(f"'{q.lower().replace(chr(39), chr(92)+chr(39))}'" for q in search_queries)
--                        (lowercased, single-quote-escaped keyword list) e.g. "'running shoes', 'yoga mat'"
--   {exclude_filter}  <- "" when exclude_marketing_campaign_ids is empty;
--                        else "AND LOWER(mcd.marketing_campaign_id) NOT IN ({ex})"
--                        where ex = ", ".join(f"'{str(c).lower()}'" for c in exclude_marketing_campaign_ids)
-- tables:
--   reporting.os_ads_keyword_performance_report
--   reporting.campaign_tagging_data
--   reporting.marketing_campaign_dimensions
--   reporting.marketplace_clients
--   reporting.clients
--   reporting.static_currency_conversion
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          called once per period (current + baseline)  -- comparison mode runs it for current + baseline when baseline_start_date/baseline_end_date supplied
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates; base cpc/cpm/ctr/roi computed in SQL)
--   <num_cols>.fillna(0)   for spend, impressions, clicks, cpc, cpm, ctr, attributed_sales, roi
--   -- Comparison mode (cur outer-merged with base on matched_keyword, marketing_campaign_id, os_client_id, seller_id):
--   status                = 'active_both' if spend_current>0 & spend_baseline>0; 'new' if only current; 'churned' if only baseline
--   spend_change          = round(spend_current - spend_baseline, 2)
--   cpc_change            = round(cpc_current - cpc_baseline, 4)
--   cpm_change            = round(cpm_current - cpm_baseline, 4)
--   tot_spend_delta       = sum(spend_current) - sum(spend_baseline)
--   spend_share_current_pct            = share_pct(spend_current, tot_spend_cur)
--   spend_share_baseline_pct           = share_pct(spend_baseline, tot_spend_base)
--   contribution_to_spend_change_pct   = contribution_pct(spend_change, tot_spend_delta)
--   new_in_post           = competitors where status == 'new'
--   summary.total_competing_campaigns  = nunique(marketing_campaign_id)
--   -- Single-period mode:
--   new_entrants          = rows where campaign_creation_date within [start_date, end_date]
--   summary.total_spend / total_impressions = sum over rows
-- =====================================================================

    WITH per_campaign AS (
      SELECT
        LOWER(k.matched_keyword) AS matched_keyword,
        mcd.marketing_campaign_id,
        mcd.alias AS campaign_name,
        mcd.effective_status,
        DATE(mcd.campaign_creation_date) AS campaign_creation_date,
        k.client_id AS os_client_id,
        cl.seller_id,
        SUM(k.cost * scc.conversion_factor) AS spend,
        SUM(k.impressions) AS impressions,
        SUM(k.clicks) AS clicks,
        SUM(k.program_per_click_timestamp_sales * scc.conversion_factor) AS attributed_sales
      FROM `prj-onlinesales-prod-01.reporting.os_ads_keyword_performance_report` k
      INNER JOIN `prj-onlinesales-prod-01.reporting.campaign_tagging_data` ctd
        ON ctd.account_id = k.account_id
        AND ctd.campaign_id = k.campaign_id
        AND ctd.client_id = k.client_id
      INNER JOIN `prj-onlinesales-prod-01.reporting.marketing_campaign_dimensions` mcd
        ON ctd.client_id = mcd.client_id
        AND ctd.marketing_campaign_id = mcd.marketing_campaign_id
      INNER JOIN `prj-onlinesales-prod-01.reporting.marketplace_clients` mc
        ON mc.marketplace_client_id = k.marketplace_client_id
        AND mc.agency_id = '{agency_id}'
      LEFT JOIN `prj-onlinesales-prod-01.reporting.clients` cl
        ON cl.client_id = k.client_id
      INNER JOIN `prj-onlinesales-prod-01.reporting.static_currency_conversion` scc
        ON scc.from_currency = k.currency
        AND scc.to_currency = mc.currency
      WHERE k.date >= '{sd}'
        AND k.date <= '{ed}'
        AND LOWER(k.matched_keyword) IN ({kw_in})
        AND (mcd.campaign_origin != 'PACKAGE_BASED' OR mcd.campaign_origin IS NULL)
        {exclude_filter}
      GROUP BY 1, 2, 3, 4, 5, 6, 7
    )
    SELECT
      matched_keyword,
      marketing_campaign_id,
      campaign_name,
      effective_status,
      campaign_creation_date,
      os_client_id,
      seller_id,
      spend,
      impressions,
      clicks,
      CASE WHEN clicks > 0 THEN SAFE_DIVIDE(spend, clicks) ELSE 0 END AS cpc,
      CASE WHEN impressions > 0 THEN SAFE_DIVIDE(spend * 1000.0, impressions) ELSE 0 END AS cpm,
      CASE WHEN impressions > 0 THEN SAFE_DIVIDE(clicks * 100.0, impressions) ELSE 0 END AS ctr,
      attributed_sales,
      CASE WHEN spend > 0 THEN SAFE_DIVIDE(attributed_sales, spend) ELSE 0 END AS roi
    FROM per_campaign
    ORDER BY impressions DESC
    LIMIT {top_n}
