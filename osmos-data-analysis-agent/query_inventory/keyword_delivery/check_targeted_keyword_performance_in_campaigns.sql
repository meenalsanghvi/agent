-- =====================================================================
-- id:                       keyword_delivery.check_targeted_keyword_performance_in_campaigns
-- source:                   tools/keyword_delivery_tools.py:290  (fn check_targeted_keyword_performance_in_campaigns)
-- agent:                    keyword_delivery
-- description:              Targeted-keyword performance (spend, impressions, clicks, CTR, CPC, CPM, attributed sales, ROI) for specific advertiser client_ids + marketing_campaign_ids over one period. Top 50 by spend.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {agency_id}   str    -> __AGENCY_ID__
--   {start_date}  date   -> __START_DATE_1__
--   {end_date}    date   -> __END_DATE_1__
-- injected_fragments:                                  (SQL spliced in by a helper)
--   {kw_in}      <- ", ".join(f"'{q.lower().replace(chr(39), chr(92)+chr(39))}'" for q in search_queries)
--                   (lowercased, single-quote-escaped keyword list) e.g. "'running shoes', 'yoga mat'"
--   {cid_in}     <- ", ".join(f"'{str(c).lower()}'" for c in marketing_campaign_ids)   e.g. "'mc_123', 'mc_456'"
--   {client_in}  <- ", ".join(f"'{str(c)}'" for c in client_ids)                       e.g. "'101', '102'"
-- tables:
--   reporting.os_ads_keyword_performance_report
--   reporting.campaign_tagging_data
--   reporting.marketing_campaign_dimensions
--   reporting.marketplace_clients
--   reporting.static_currency_conversion
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          single call
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates; most metrics computed in SQL)
--   <num_cols>.fillna(0)  for spend, impressions, clicks, program_ctr, program_cpc, program_cpm,
--                              program_per_click_timestamp_sales, program_per_click_timestamp_roi
--   found         = set of matched_keyword values returned
--   not_found     = {q.lower() for q in search_queries} - found
--   keywords_with_data = len(found)
-- =====================================================================

    WITH campaign_keyword_perf AS (
      SELECT
        LOWER(k.matched_keyword) AS matched_keyword,
        k.keyword_match_type AS keyword_match_type,
        mcd.marketing_campaign_id AS marketing_campaign_id,
        SUM(k.cost * scc.conversion_factor) AS spend,
        SUM(k.impressions) AS impressions,
        SUM(k.clicks) AS visits,
        SUM(k.program_per_click_timestamp_sales * scc.conversion_factor)
            AS program_per_click_timestamp_sales
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
      INNER JOIN `prj-onlinesales-prod-01.reporting.static_currency_conversion` scc
        ON scc.from_currency = k.currency
        AND scc.to_currency = mc.currency
      WHERE k.date >= '{start_date}'
        AND k.date <= '{end_date}'
        AND LOWER(k.matched_keyword) IN ({kw_in})
        AND k.client_id IN ({client_in})
        AND ctd.client_id IN ({client_in})
        AND LOWER(mcd.marketing_campaign_id) IN ({cid_in})
        AND (mcd.campaign_origin != 'PACKAGE_BASED' OR mcd.campaign_origin IS NULL)
      GROUP BY 1, 2, 3
    )
    SELECT
      matched_keyword,
      keyword_match_type,
      SUM(spend) AS spend,
      SUM(impressions) AS impressions,
      SUM(visits) AS clicks,
      CASE WHEN SUM(impressions) > 0
           THEN SAFE_DIVIDE(SUM(visits) * 100, SUM(impressions))
           ELSE 0 END AS program_ctr,
      CASE WHEN SUM(visits) > 0
           THEN SAFE_DIVIDE(SUM(spend), SUM(visits))
           ELSE 0 END AS program_cpc,
      CASE WHEN SUM(impressions) > 0
           THEN SAFE_DIVIDE(SUM(spend) * 1000, SUM(impressions))
           ELSE 0 END AS program_cpm,
      SUM(program_per_click_timestamp_sales) AS program_per_click_timestamp_sales,
      CASE WHEN SUM(spend) > 0
           THEN SAFE_DIVIDE(SUM(program_per_click_timestamp_sales), SUM(spend))
           ELSE 0 END AS program_per_click_timestamp_roi
    FROM campaign_keyword_perf
    GROUP BY 1, 2
    ORDER BY spend DESC
    LIMIT 50
