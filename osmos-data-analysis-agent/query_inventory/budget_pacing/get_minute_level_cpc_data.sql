-- =====================================================================
-- id:                       budget_pacing.get_minute_level_cpc_data
-- source:                   tools/budget_pacing_tools.py:40  (fn get_minute_level_cpc_data)
-- agent:                    budget_pacing
-- description:              Per-minute clicks and spend for CPC-strategy PLA campaigns on a single day, split by campaign and page_type (SEARCH vs NON-SEARCH). Spend converted USD -> marketplace currency.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {marketplace_client_id}  str   -> __MARKETPLACE_CLIENT_ID__
--   {timezone}               str   -> __TIMEZONE__
--   {date}                   date  -> __DATE__
-- injected_fragments:                                  (SQL spliced in by a helper)
--   {local_dt}         <- "CAST(DATETIME(TIMESTAMP(c.response_timestamp_utc), '{tz}') AS DATETIME)".format(tz=timezone)
--                         e.g. "CAST(DATETIME(TIMESTAMP(c.response_timestamp_utc), 'Asia/Kolkata') AS DATETIME)"
--   {campaign_ids_str} <- ", ".join(f"'{cid}'" for cid in marketing_campaign_ids)
--                         e.g. "'123', '456'"
-- tables:
--   reporting.os_product_ads_response_to_clicks_mapping
--   reporting.marketplace_clients
--   reporting.static_currency_conversion
--   reporting.campaign_tagging_data
-- region_specific:          false
-- timezone_aware:           true                        (DATE(TIMESTAMP(col), '{timezone}') + {local_dt})
-- comparison_mode:          single call
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   total_clicks = int(df["clicks"].sum())
--   total_spend  = round(float(df["spend"].sum()), 2)
--   row_count    = len(rows)
-- =====================================================================

SELECT
    c.campaign_id,
    c.page_type,
    EXTRACT(HOUR FROM {local_dt}) AS hour,
    EXTRACT(MINUTE FROM {local_dt}) AS minute,
    SUM(c.unique_click) AS clicks,
    SUM(COALESCE(c.bid, 0) * scc.conversion_factor) AS spend
FROM `prj-onlinesales-prod-01.reporting.os_product_ads_response_to_clicks_mapping` c
INNER JOIN `prj-onlinesales-prod-01.reporting.marketplace_clients` mc
    ON mc.marketplace_client_id = '{marketplace_client_id}'
INNER JOIN `prj-onlinesales-prod-01.reporting.static_currency_conversion` scc
    ON scc.from_currency = 'USD'
    AND scc.to_currency = mc.currency
WHERE c.marketplace_client_id = '{marketplace_client_id}'
    AND c.is_valid_click = TRUE
    AND DATE(TIMESTAMP(c.response_timestamp_utc), '{timezone}') = '{date}'
    AND c.campaign_id IN (
        SELECT campaign_id
        FROM `prj-onlinesales-prod-01.reporting.campaign_tagging_data`
        WHERE marketing_campaign_id IN ({campaign_ids_str})
    )
GROUP BY campaign_id, page_type, hour, minute
ORDER BY hour, minute, campaign_id
