-- =====================================================================
-- id:                       shared.get_merchant_keyword_performance
-- source:                   tools/common_tools.py:2504  (fn get_merchant_keyword_performance -> _kw_query)
-- agent:                    shared
-- description:              A merchant's TARGETED keywords across all its PLA performance campaigns (os_ads_search, smart_shopping) for one period: keyword×campaign spend, impressions, clicks, ad_revenue (currency-converted), each tagged with match_type + campaign_name. Called once per period; comparison mode runs it for current + baseline.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {agency_id}  str  -> __AGENCY_ID__
--   {sd}         date -> __START_DATE_1__   (baseline call -> __START_DATE_2__)
--   {ed}         date -> __END_DATE_1__     (baseline call -> __END_DATE_2__)
--   {top_n}      int  -> __LIMIT__
-- injected_fragments:                                  (SQL spliced in by a helper/branch)
--   {client_in}  <- ", ".join("'{c}'" for c in client_ids.split(","))   (os_client_ids)
--                   used twice: "AND k.client_id IN (...)" and "AND ctd.client_id IN (...)"
-- tables:
--   reporting.os_ads_keyword_performance_report
--   reporting.campaign_tagging_data
--   reporting.marketing_campaign_dimensions
--   reporting.marketing_campaign_group_dimensions
--   reporting.marketplace_clients
--   reporting.static_currency_conversion
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          called once per period (current + baseline)
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   ctr  = clicks / impressions * 100
--   cpc  = spend / clicks
--   cpm  = spend * 1000 / impressions
--   roas = ad_revenue / spend
--   -- comparison mode (merge on keyword, match_type, marketing_campaign_id, os_client_id):
--   status            = active_both | new | churned   (from spend_current>0 / spend_baseline>0)
--   spend_change / cpc_change / ctr_change / roas_change = current - baseline
--   spend_share_current_pct / spend_share_baseline_pct = spend / total_spend * 100
--   contribution_to_spend_change_pct / contribution_to_clicks_change_pct
--   (empty result -> "purely AUTO, use get_search_query_performance")
-- =====================================================================

        SELECT
            LOWER(k.matched_keyword) AS keyword,
            k.keyword_match_type AS match_type,
            ctd.marketing_campaign_id AS marketing_campaign_id,
            mcd.alias AS campaign_name,
            ctd.marketing_campaign_group_id AS marketing_campaign_group_id,
            k.client_id AS os_client_id,
            COALESCE(SUM(k.cost * scc.conversion_factor), 0) AS spend,
            COALESCE(SUM(k.impressions), 0) AS impressions,
            COALESCE(SUM(k.clicks), 0) AS clicks,
            COALESCE(SUM(k.program_per_click_timestamp_sales * scc.conversion_factor), 0) AS ad_revenue
        FROM `prj-onlinesales-prod-01.reporting.os_ads_keyword_performance_report` k
        INNER JOIN `prj-onlinesales-prod-01.reporting.campaign_tagging_data` ctd
            ON ctd.account_id = k.account_id AND ctd.campaign_id = k.campaign_id AND ctd.client_id = k.client_id
        INNER JOIN `prj-onlinesales-prod-01.reporting.marketing_campaign_dimensions` mcd
            ON ctd.client_id = mcd.client_id AND ctd.marketing_campaign_id = mcd.marketing_campaign_id
            AND (mcd.campaign_origin != 'PACKAGE_BASED' OR mcd.campaign_origin IS NULL)
        INNER JOIN `prj-onlinesales-prod-01.reporting.marketing_campaign_group_dimensions` mcgd
            ON ctd.client_id = mcgd.client_id AND ctd.marketing_campaign_group_id = mcgd.marketing_campaign_group_id
        INNER JOIN `prj-onlinesales-prod-01.reporting.marketplace_clients` mc
            ON mc.marketplace_client_id = k.marketplace_client_id AND mc.agency_id = '{agency_id}'
        INNER JOIN `prj-onlinesales-prod-01.reporting.static_currency_conversion` scc
            ON scc.from_currency = k.currency AND scc.to_currency = mc.currency
        WHERE k.date >= '{sd}' AND k.date <= '{ed}'
            AND k.client_id IN ({client_in})
            AND ctd.client_id IN ({client_in})
            AND LOWER(mcgd.campaign_type) IN ('performance')
            AND LOWER(mcgd.campaign_subtype) IN ('os_ads_search', 'smart_shopping')
        GROUP BY 1, 2, 3, 4, 5, 6
        HAVING COALESCE(SUM(k.cost * scc.conversion_factor), 0) > 0
        ORDER BY spend DESC
        LIMIT {top_n}
