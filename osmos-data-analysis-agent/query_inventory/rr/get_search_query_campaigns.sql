-- =====================================================================
-- id:                       rr.get_search_query_campaigns
-- source:                   tools/rr_analysis_tools.py:157  (fn get_search_query_campaigns)
-- agent:                    rr
-- description:              Distinct campaigns (+ current effective_status) responding to a set of search queries for ONE period, for RR-drop root-cause. Called once per period; comparison mode runs it for current + baseline.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {marketplace_client_id} str  -> __MARKETPLACE_CLIENT_ID__
--   {start_date}            date -> __START_DATE_1__   (baseline call -> __START_DATE_2__)
--   {end_date}              date -> __END_DATE_1__     (baseline call -> __END_DATE_2__)
-- injected_fragments:                                  (SQL spliced in by helper/branch)
--   {in_clause}   <- ", ".join("'{q}'" for q in search_queries)  (single-quote-escaped list)
--                    e.g. "'shoes', 'blue shirt'"    -> resp.search_query IN (...)
--   {f"LIMIT {top_n}" if top_n else ""}  <- optional row cap (empty string when top_n is None)
-- tables:
--   reporting.os_ads_search_query_performance_report
--   reporting.campaign_tagging_data
--   reporting.marketing_campaign_dimensions
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          called once per period (current + baseline)
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   query_campaigns          = rows[search_query, os_client_id, merchant_id, marketing_campaign_id, effective_status]
--   paused_campaigns         = rows where effective_status.upper() != 'ACTIVE' (deduped by marketing_campaign_id)
--   active_campaigns_count   = unique_campaigns_total - paused_campaigns_count
--   all_campaign_ids         = sorted(unique(marketing_campaign_id))
--   all_client_ids           = sorted(unique(os_client_id))
--   unique_campaigns_total   = nunique(marketing_campaign_id)
--   unique_merchants         = nunique(merchant_id)
--   queries_with_data        = nunique(search_query)
--   truncated                = True when len(df) == top_n
-- =====================================================================

    SELECT DISTINCT
        resp.search_query,
        resp.client_id AS os_client_id,
        resp.merchant_id,
        ctd.marketing_campaign_id,
        mcd.effective_status
    FROM `prj-onlinesales-prod-01.reporting.os_ads_search_query_performance_report` resp
    JOIN `prj-onlinesales-prod-01.reporting.campaign_tagging_data` ctd
        ON ctd.campaign_id = resp.campaign_id
    LEFT JOIN `prj-onlinesales-prod-01.reporting.marketing_campaign_dimensions` mcd
        ON mcd.marketing_campaign_id = ctd.marketing_campaign_id
    WHERE
        resp.search_query IN ({in_clause})
        AND resp.marketplace_client_id = '{marketplace_client_id}'
        AND resp.date >= '{start_date}' AND resp.date <= '{end_date}'
    {f"LIMIT {top_n}" if top_n else ""}
