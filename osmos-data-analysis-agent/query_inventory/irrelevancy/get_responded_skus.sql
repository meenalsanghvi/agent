-- =====================================================================
-- id:                       irrelevancy.get_responded_skus
-- source:                   tools/irrelevancy_tools.py:69  (fn get_responded_skus)
-- agent:                    irrelevancy
-- description:              For SEARCH-page search queries, list the SKUs that were responded/served (product name, brand, e_product_type category, serving cache_type/algorithm) with spend and impressions, so keyword-to-SKU irrelevancy can be investigated. PLA only. Sorted by spend desc, top_n limited.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {marketplace_client_id}  str   -> __MARKETPLACE_CLIENT_ID__   (also interpolated into the oltp_merchandise_product_dimensions_{...} table name)
--   {timezone}               str   -> __TIMEZONE__
--   {start_date}             date  -> __START_DATE_1__
--   {end_date}               date  -> __END_DATE_1__
--   {top_n}                  int   -> __LIMIT__            (default 200)
-- injected_fragments:                                  (SQL spliced in by {filter_sql}, newline-joined optional AND clauses)
--   {filter_sql}  <- built in-fn from optional args:
--     search_queries      -> "AND LOWER(TRIM(impr.search_query, '[\"],')) IN (<'q1','q2',...>)"   (values lower-cased, single-quotes escaped)
--     campaign_ids        -> "AND impr.campaign_id IN (<'id1','id2',...>)"                          (single-quotes escaped)
--     product_name_like   -> "AND LOWER(mpd.e_name) LIKE '%<value>%'"                               (value lower-cased, single-quotes escaped)
-- tables:
--   reporting.os_product_ads_response_to_impressions_mapping
--   reporting.marketplace_clients
--   reporting.oltp_merchandise_product_dimensions_{marketplace_client_id}   (per-marketplace suffixed table)
--   reporting.static_currency_conversion
-- region_specific:          false
-- timezone_aware:           true    (DATE(TIMESTAMP(impr.response_timestamp_utc), '{timezone}'))
-- comparison_mode:          single call
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   spend            = round(spend.fillna(0), 2)
--   impressions      = impressions.fillna(0)
--   summary.total_rows          = len(rows)
--   summary.unique_keywords     = nunique(keyword)
--   summary.unique_skus         = nunique(sku_id)
--   summary.unique_cache_types  = sorted(unique(cache_type))
--   summary.total_spend         = round(sum(spend), 2)
--   summary.total_impressions   = sum(impressions)
--   truncated        = (len(df) == top_n)
-- =====================================================================

    SELECT
        LOWER(TRIM(impr.search_query, '[\"],')) AS keyword,
        impr.cache_type,
        impr.sku_id,
        mpd.e_name AS product_name,
        mpd.e_brand AS brand,
        mpd.e_product_type AS category,
        SUM(COALESCE(impr.bid, 0) * scc.conversion_factor) AS spend,
        SUM(CASE WHEN impr.unique_impressions > 0 THEN 1 ELSE 0 END) AS impressions
    FROM `prj-onlinesales-prod-01.reporting.os_product_ads_response_to_impressions_mapping` AS impr
    JOIN `prj-onlinesales-prod-01.reporting.marketplace_clients` AS mc
        ON mc.marketplace_client_id = impr.marketplace_client_id
    JOIN `prj-onlinesales-prod-01.reporting.oltp_merchandise_product_dimensions_{marketplace_client_id}` AS mpd
        ON mpd.sku_id = impr.sku_id
    JOIN `prj-onlinesales-prod-01.reporting.static_currency_conversion` AS scc
        ON scc.from_currency = 'USD'
        AND scc.to_currency = mc.currency
    WHERE mc.marketplace_client_id = '{marketplace_client_id}'
        AND DATE(TIMESTAMP(impr.response_timestamp_utc), '{timezone}')
            BETWEEN '{start_date}' AND '{end_date}'
        AND impr.page_type = 'SEARCH'
        {filter_sql}
    GROUP BY 1, 2, 3, 4, 5, 6
    ORDER BY spend DESC
    LIMIT {top_n}
