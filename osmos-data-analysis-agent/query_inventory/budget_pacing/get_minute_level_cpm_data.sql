-- =====================================================================
-- id:                       budget_pacing.get_minute_level_cpm_data
-- source:                   tools/budget_pacing_tools.py:119  (fn get_minute_level_cpm_data)
-- agent:                    budget_pacing
-- description:              Per-minute impressions and spend for CPM-strategy PLA campaigns on a single day, grouped by marketing_campaign_group_id. Spend converted USD -> marketplace currency.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {marketplace_client_id}  str   -> __MARKETPLACE_CLIENT_ID__
--   {timezone}               str   -> __TIMEZONE__
--   {date}                   date  -> __DATE__
-- injected_fragments:                                  (SQL spliced in by a helper)
--   {local_dt}       <- "CAST(DATETIME(TIMESTAMP(i.response_timestamp_utc), '{tz}') AS DATETIME)".format(tz=timezone)
--                       e.g. "CAST(DATETIME(TIMESTAMP(i.response_timestamp_utc), 'Asia/Kolkata') AS DATETIME)"
--   {group_ids_str}  <- ", ".join(f"'{gid}'" for gid in marketing_campaign_group_ids)
--                       e.g. "'123', '456'"
-- tables:
--   reporting.os_product_ads_response_to_impressions_mapping
--   reporting.campaign_tagging_data
--   reporting.marketplace_clients
--   reporting.static_currency_conversion
-- region_specific:          false
-- timezone_aware:           true                        (DATE(TIMESTAMP(col), '{timezone}') + {local_dt})
-- comparison_mode:          single call
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   total_impressions = int(df["impressions"].sum())
--   total_spend       = round(float(df["spend"].sum()), 2)
--   row_count         = len(rows)
-- =====================================================================

SELECT
    t.marketing_campaign_group_id,
    EXTRACT(HOUR FROM {local_dt}) AS hour,
    EXTRACT(MINUTE FROM {local_dt}) AS minute,
    SUM(i.unique_impressions) AS impressions,
    SUM(COALESCE(i.bid, 0) * scc.conversion_factor) AS spend
FROM `prj-onlinesales-prod-01.reporting.os_product_ads_response_to_impressions_mapping` i
INNER JOIN `prj-onlinesales-prod-01.reporting.campaign_tagging_data` t
    ON i.campaign_id = t.campaign_id
INNER JOIN `prj-onlinesales-prod-01.reporting.marketplace_clients` mc
    ON mc.marketplace_client_id = '{marketplace_client_id}'
INNER JOIN `prj-onlinesales-prod-01.reporting.static_currency_conversion` scc
    ON scc.from_currency = 'USD'
    AND scc.to_currency = mc.currency
WHERE i.marketplace_client_id = '{marketplace_client_id}'
    AND t.marketing_campaign_group_id IN ({group_ids_str})
    AND DATE(TIMESTAMP(i.response_timestamp_utc), '{timezone}') = '{date}'
GROUP BY marketing_campaign_group_id, hour, minute
ORDER BY hour, minute, marketing_campaign_group_id
