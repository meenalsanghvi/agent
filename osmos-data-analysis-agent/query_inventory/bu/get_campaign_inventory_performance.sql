-- =====================================================================
-- id:                       bu.get_campaign_inventory_performance
-- source:                   tools/bu_analysis_tools.py:1445  (fn get_campaign_inventory_performance)
-- agent:                    bu
-- description:              Inventory/ad-unit slots selected by Display campaigns (filtered by client_id(s) and/or campaign_group_id(s)) for ONE date range: spend, impressions, clicks, CTR, CPM, sales, ROAS. Inverse of get_display_inventory_campaigns.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {start_date}   date   -> __START_DATE_1__
--   {end_date}     date   -> __END_DATE_1__
--   {top_n}        int    -> __TOP_N__
-- injected_fragments:                                  (SQL spliced in by a helper)
--   {filter_sql}  <- at least one of, newline-joined:
--                    client_id(s)        -> "AND baf.client_id IN ('id', ...)"
--                    campaign_group_id(s) -> "AND mcgd.marketing_campaign_group_id IN ('id', ...)"
-- tables:
--   reporting.os_brand_ads_network_level_facts
--   reporting.campaign_tagging_data
--   reporting.marketing_campaign_group_dimensions
--   reporting.brand_ads_dimensions
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          single call (agent calls once per period to compare)
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   (all metrics computed in SQL) float columns rounded to 2dp; rows passed through
--   per_campaign_inventories = group rows by campaign_group_id -> unique inventory list + count
--   total_slots = len(rows);  unique_inventory_count = nunique(inventory_name)
--   total_spend = SUM(spend);  total_impressions = SUM(impressions)
-- =====================================================================

SELECT
    bad.au_display_name AS inventory_name,
    mcgd.marketing_campaign_group_alias AS campaign_group_name,
    mcgd.marketing_campaign_group_id AS campaign_group_id,
    SUM(CASE WHEN baf.date BETWEEN '{start_date}' AND '{end_date}' THEN baf.cost ELSE 0 END) AS spend,
    SUM(CASE WHEN baf.date BETWEEN '{start_date}' AND '{end_date}' THEN baf.onsite_impressions ELSE 0 END) AS impressions,
    SUM(CASE WHEN baf.date BETWEEN '{start_date}' AND '{end_date}' THEN baf.clicks ELSE 0 END) AS clicks,
    COALESCE(SAFE_DIVIDE(
        SUM(CASE WHEN baf.date BETWEEN '{start_date}' AND '{end_date}' THEN baf.clicks ELSE 0 END) * 100,
        NULLIF(SUM(CASE WHEN baf.date BETWEEN '{start_date}' AND '{end_date}' THEN baf.onsite_impressions ELSE 0 END), 0)
    ), 0) AS ctr,
    COALESCE(SAFE_DIVIDE(
        SUM(CASE WHEN baf.date BETWEEN '{start_date}' AND '{end_date}' THEN baf.cost ELSE 0 END) * 1000,
        NULLIF(SUM(CASE WHEN baf.date BETWEEN '{start_date}' AND '{end_date}' THEN baf.onsite_impressions ELSE 0 END), 0)
    ), 0) AS cpm,
    SUM(CASE WHEN baf.date BETWEEN '{start_date}' AND '{end_date}' THEN baf.program_per_click_timestamp_sales ELSE 0 END) AS sales,
    COALESCE(SAFE_DIVIDE(
        SUM(CASE WHEN baf.date BETWEEN '{start_date}' AND '{end_date}' THEN baf.program_per_click_timestamp_sales ELSE 0 END),
        NULLIF(SUM(CASE WHEN baf.date BETWEEN '{start_date}' AND '{end_date}' THEN baf.cost ELSE 0 END), 0)
    ), 0) AS roas
FROM `prj-onlinesales-prod-01.reporting.os_brand_ads_network_level_facts` AS baf
JOIN `prj-onlinesales-prod-01.reporting.campaign_tagging_data` AS ctd
    ON ctd.campaign_id = baf.campaign_id AND ctd.client_id = baf.client_id
JOIN `prj-onlinesales-prod-01.reporting.marketing_campaign_group_dimensions` AS mcgd
    ON mcgd.marketing_campaign_group_id = ctd.marketing_campaign_group_id
    AND mcgd.client_id = ctd.client_id
    AND mcgd.campaign_origin != 'PACKAGE_BASED'
JOIN `prj-onlinesales-prod-01.reporting.brand_ads_dimensions` AS bad
    ON bad.campaign_id = ctd.campaign_id
    AND baf.ad_id = bad.ad_id
    AND bad.account_id = ctd.account_id
    AND baf.ad_creative_id = bad.ad_creative_id
    AND baf.account_id = bad.account_id
    AND baf.campaign_id = bad.campaign_id
    AND baf.client_id = bad.client_id
    AND baf.marketplace_client_id = bad.marketplace_client_id
    AND baf.inventory_ad_unit_id = bad.inventory_ad_unit_id
WHERE baf.date BETWEEN '{start_date}' AND '{end_date}'
    {filter_sql}
GROUP BY 1, 2, 3
ORDER BY impressions DESC
LIMIT {top_n}
