-- =====================================================================
-- id:                       bu.get_display_inventory_campaigns
-- source:                   tools/bu_analysis_tools.py:1216  (fn get_display_inventory_campaigns)
-- agent:                    bu
-- description:              Campaigns running under a specific Display inventory slot (ad unit, optional page type) for ONE date range: merchant, campaign-group name/type/status/subtype, bidding strategy, daily budget, spend, CPM (cost > 0, BLOCK_BUY or ACTIVE).
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {agency_id}     str   -> __AGENCY_ID__
--   {start_date}    date  -> __START_DATE_1__
--   {end_date}      date  -> __END_DATE_1__
--   {ad_unit_name}  str   -> __AD_UNIT_NAME__
--   {top_n}         int   -> __TOP_N__
--   {page_type}     str   -> __PAGE_TYPE__   (optional; see injected_fragments)
-- injected_fragments:                                  (SQL spliced in by a helper)
--   {page_filter}  <- page_type set -> "AND LOWER(rpt.page_type) = LOWER('{page_type}')"  else ""
-- tables:
--   reporting.os_display_ads_ad_targeting_report
--   reporting.agencies
--   reporting.monetize_merchant_dimensions
--   reporting.campaign_tagging_data
--   reporting.marketing_campaign_group_dimensions
--   reporting.marketing_campaign_dimensions
--   reporting.marketplace_clients
--   reporting.static_currency_conversion
--   reporting.os_ads_db_campaign_inventory_configurations
--   reporting.os_ads_db_status_types
-- region_specific:          false
-- timezone_aware:           false   (start/end date converted via joined marketplace_clients.timezone column, not a {timezone} placeholder)
-- comparison_mode:          single call (agent calls once per period to compare)
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   (all metrics computed in SQL) rows passed through
--   total_campaigns = len(rows);  total_spend = SUM(campaign_inventory_spend)
-- =====================================================================

SELECT
    mmd.merchant_id AS merchant_id,
    mmd.merchant_name AS merchant_name,
    mcd.marketing_campaign_group_id AS campaign_group_id,
    mcd.marketing_campaign_group_alias AS campaign_group_name,
    mmd.client_id AS client_id,
    CASE
        WHEN (JSON_EXTRACT_SCALAR(mcgd.metadata, '$.isEanEnabled') = 'true'
              AND ctd.vendor IN ('google', 'facebook', 'tiktok')) THEN 'Offsite Ad'
        WHEN mcgd.campaign_type = 'PERFORMANCE' THEN 'Sponsored Product Ad'
        WHEN mcgd.campaign_type IN ('AWARENESS', 'INVENTORY') THEN 'Sponsored Display Ad'
        WHEN mcgd.campaign_type IN ('OFFSITE') THEN 'Offsite Ad'
        ELSE 'Sponsored Offsite Ad'
    END AS campaign_group_type,
    REPLACE(mcgd.effective_status, '_', ' ') AS campaign_group_status,
    CAST(DATE(TIMESTAMP(mcgd.start_date, 'UTC'), marketplace_clients.timezone) AS STRING) AS campaign_group_start_date,
    CASE
        WHEN DATETIME(TIMESTAMP(mcgd.end_date, 'UTC'), marketplace_clients.timezone) >= '2036-01-01' THEN NULL
        ELSE CAST(DATE(TIMESTAMP(mcgd.end_date, 'UTC'), marketplace_clients.timezone) AS STRING)
    END AS campaign_group_end_date,
    CASE
        WHEN (JSON_EXTRACT_SCALAR(mcgd.metadata, '$.isEanEnabled') = 'true'
              AND ctd.vendor IN ('google', 'facebook', 'tiktok')) THEN 'Manual'
        WHEN mcgd.campaign_type = 'PERFORMANCE' AND mcgd.campaign_subtype = 'SMART_SHOPPING'
             AND ((mcgd.bidding_strategy IN ('AUTO_CPC', 'AUTO_CPM')
                   AND mcgd.objective_name IN ('Visitors', 'Visibility'))
                  OR mcgd.objective_name = 'Absolute Revenue') THEN 'Smart Shopping'
        WHEN mcgd.campaign_type = 'PERFORMANCE'
             AND mcgd.objective_name IN ('Visitors', 'Visibility')
             AND mcgd.bidding_strategy IN ('CPC', 'CPM') THEN 'Manual'
        WHEN mcgd.campaign_type = 'PERFORMANCE'
             AND mcgd.campaign_subtype = 'OS_ADS_SEARCH' THEN 'Search-Only'
        WHEN mcgd.campaign_type IN ('AWARENESS', 'INVENTORY')
             AND mcgd.campaign_subtype = 'AUCTION' THEN 'Auction'
        WHEN mcgd.campaign_type IN ('AWARENESS', 'INVENTORY')
             AND mcgd.campaign_subtype = 'BLOCK_BUY' THEN 'Guaranteed'
        WHEN mcgd.campaign_type IN ('AWARENESS', 'INVENTORY')
             AND mcgd.campaign_subtype = 'PRE_AUCTION' THEN 'Auction Packages'
        WHEN mcgd.campaign_type IN ('OFFSITE')
             AND mcgd.campaign_subtype IN ('FACEBOOK_PRODUCT_AD', 'FACEBOOK', 'FACEBOOK_CAROUSEL_AD') THEN 'Facebook'
        WHEN mcgd.campaign_type IN ('OFFSITE')
             AND mcgd.campaign_subtype IN ('FACEBOOK_DPA') THEN 'Facebook DPA'
        WHEN mcgd.campaign_type IN ('OFFSITE')
             AND mcgd.campaign_subtype IN ('GOOGLE_PERFORMANCE_MAX_SHOPPING', 'GOOGLE_PERFORMANCE_MAX') THEN 'Google Performance Max'
        WHEN mcgd.campaign_type IN ('OFFSITE')
             AND mcgd.campaign_subtype IN ('GOOGLE_PRODUCT_AD', 'GOOGLE_SEARCH_TEXT_AD') THEN 'Google'
        WHEN mcgd.campaign_type IN ('OFFSITE')
             AND mcgd.campaign_subtype IN ('TIKTOK_TRAFFIC') THEN 'Tiktok Traffic'
        WHEN mcgd.campaign_type IN ('OFFSITE')
             AND mcgd.campaign_subtype IN ('TIKTOK_REACH') THEN 'Tiktok Reach'
    END AS campaign_group_subtype,
    ROUND(CASE
        WHEN ROUND(mmd.remaning_balance, 0) <= 0.01 THEN 0
        ELSE ROUND(mmd.remaning_balance, 0)
    END, 2) AS merchant_remaining_balance,
    mcgd.daily_budget AS campaign_group_current_daily_budget,
    CASE
        WHEN (mcd.campaign_type = 'PERFORMANCE'
              AND mcd.objective_name IN ('Visitors', 'Visibility')
              AND mcd.bidding_strategy = 'AUTO_CPC') THEN 'Max Performance CPC'
        WHEN (mcd.campaign_type = 'PERFORMANCE'
              AND mcd.objective_name IN ('Visitors', 'Visibility')
              AND mcd.bidding_strategy = 'AUTO_CPM') THEN 'Max Performance CPM'
        WHEN (mcd.campaign_type = 'PERFORMANCE'
              AND mcd.objective_name IN ('Visitors', 'Visibility')
              AND mcd.bidding_strategy IN ('CPM', 'CPC')) THEN mcd.bidding_strategy
        WHEN mcd.campaign_type IN ('INVENTORY', 'AWARENESS')
             AND mcd.campaign_subtype = 'PRE_AUCTION' THEN 'NA'
        WHEN mcd.objective_name IN ('Absolute Revenue') THEN 'ROI'
        WHEN mcd.objective_name IN ('Visibility', 'Reach')
             AND mcd.campaign_subtype = 'AUCTION'
             THEN UPPER(JSON_EXTRACT_SCALAR(mcd.campaign_setting_metadata, '$.bidding_strategy_type'))
        WHEN mcd.objective_name IN ('Visibility', 'Reach')
             AND mcd.campaign_subtype = 'BLOCK_BUY'
             AND JSON_EXTRACT_SCALAR(mcd.campaign_setting_metadata, '$.bidding_strategy_type') = 'CPM'
             THEN 'Fixed CPM'
        WHEN mcd.objective_name IN ('Visibility', 'Reach')
             AND mcd.campaign_subtype = 'BLOCK_BUY'
             AND JSON_EXTRACT_SCALAR(mcd.campaign_setting_metadata, '$.bidding_strategy_type') = 'CPD'
             THEN 'CPD'
        ELSE 'UNKNOWN'
    END AS campaign_group_bidding_strategy_type,
    ROUND(SUM(rpt.cost), 2) AS campaign_inventory_spend,
    ROUND(CASE
        WHEN SUM(rpt.impressions) > 0 THEN SUM(rpt.cost) * 1000 / SUM(rpt.impressions)
        ELSE 0
    END, 2) AS campaign_inventory_cpm
FROM `prj-onlinesales-prod-01.reporting.os_display_ads_ad_targeting_report` AS rpt
INNER JOIN `prj-onlinesales-prod-01.reporting.agencies` AS agencies
    ON agencies.marketplace_client_id = rpt.marketplace_client_id
    AND agencies.agency_id = '{agency_id}'
INNER JOIN `prj-onlinesales-prod-01.reporting.monetize_merchant_dimensions` AS mmd
    ON mmd.marketplace_client_id = rpt.marketplace_client_id
    AND mmd.merchant_id = rpt.merchant_id
    AND mmd.agency_id = '{agency_id}'
INNER JOIN `prj-onlinesales-prod-01.reporting.campaign_tagging_data` AS ctd
    ON ctd.client_id = rpt.client_id
    AND ctd.campaign_id = rpt.campaign_id
INNER JOIN `prj-onlinesales-prod-01.reporting.marketing_campaign_group_dimensions` AS mcgd
    ON mcgd.marketing_campaign_group_id = ctd.marketing_campaign_group_id
    AND mcgd.client_id = ctd.client_id
INNER JOIN `prj-onlinesales-prod-01.reporting.marketing_campaign_dimensions` AS mcd
    ON mcd.client_id = ctd.client_id
    AND mcd.marketing_campaign_id = ctd.marketing_campaign_id
INNER JOIN `prj-onlinesales-prod-01.reporting.marketplace_clients` AS marketplace_clients
    ON marketplace_clients.marketplace_client_id = rpt.marketplace_client_id
    AND marketplace_clients.agency_id = agencies.agency_id
    AND marketplace_clients.agency_id = mmd.agency_id
INNER JOIN `prj-onlinesales-prod-01.reporting.static_currency_conversion` AS scc_usd
    ON scc_usd.from_currency = 'USD'
    AND scc_usd.to_currency = mmd.currency
LEFT JOIN `prj-onlinesales-prod-01.reporting.os_ads_db_campaign_inventory_configurations` AS os_cic
    ON SAFE_CAST(os_cic.marketplace_client_id AS STRING) = agencies.marketplace_client_id
    AND SAFE_CAST(os_cic.marketplace_client_id AS STRING) = rpt.marketplace_client_id
    AND SAFE_CAST(os_cic.client_id AS STRING) = rpt.client_id
    AND SAFE_CAST(os_cic.campaign_id AS STRING) = rpt.campaign_id
    AND SAFE_CAST(os_cic.marketplace_client_id AS STRING) = mmd.marketplace_client_id
    AND SAFE_CAST(os_cic.client_id AS STRING) = mmd.client_id
    AND SAFE_CAST(os_cic.client_id AS STRING) = mcgd.client_id
    AND SAFE_CAST(os_cic.client_id AS STRING) = ctd.client_id
    AND SAFE_CAST(os_cic.campaign_id AS STRING) = ctd.campaign_id
    AND SAFE_CAST(os_cic.marketplace_client_id AS STRING) = marketplace_clients.marketplace_client_id
INNER JOIN `prj-onlinesales-prod-01.reporting.os_ads_db_status_types` AS status_types
    ON os_cic.status_type_id = status_types.id
WHERE rpt.date >= '{start_date}'
    AND rpt.date <= '{end_date}'
    AND rpt.cost > 0
    AND (mcgd.campaign_subtype = 'BLOCK_BUY' OR status_types.name = 'ACTIVE')
    AND LOWER(rpt.ad_unit_name) = LOWER('{ad_unit_name}')
    {page_filter}
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13
ORDER BY campaign_inventory_spend DESC
LIMIT {top_n} OFFSET 0
