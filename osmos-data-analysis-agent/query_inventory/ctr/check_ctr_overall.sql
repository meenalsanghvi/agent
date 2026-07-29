-- =====================================================================
-- id:                       ctr.check_ctr_overall
-- source:                   tools/ctr_analysis_tools.py:80  (fn check_ctr_overall -> _q)
-- agent:                    ctr
-- description:              Marketplace-level CTR for ONE period, decomposed into raw clicks / impressions / spend (CTR itself computed in Python). Optional per-merchant filter. Called once per period; comparison mode runs it for current + baseline.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {agency_id}   str    -> __AGENCY_ID__
--   {sd}          date   -> __START_DATE_1__   (baseline call -> __START_DATE_2__)
--   {ed}          date   -> __END_DATE_1__     (baseline call -> __END_DATE_2__)
-- injected_fragments:                                  (SQL spliced in by a helper)
--   {channel_condition}  <- get_channel_filter(program_type, include_vendor=True)
--                        pla     -> "vendor = 'os_ads' AND channel = 'os_product_ads'"
--                        display -> "vendor = 'os_ads' AND channel IN ('guaranteed_display_ads', 'auction_display_ads')"
--                        all     -> "vendor = 'os_ads' AND channel IN ('os_product_ads', 'guaranteed_display_ads', 'auction_display_ads')"
--   {merchant_filter}    <- built inline from client_ids / seller_ids (optional; "" when neither given)
--                        client_ids -> "AND clients.client_id IN ('<id>', ...)"
--                        seller_ids -> "AND clients.seller_id IN ('<id>', ...)"
-- tables:
--   reporting.client_vendor_channel_performance_facts
--   reporting.clients
--   reporting.marketplace_clients
--   reporting.static_currency_conversion
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          called once per period (current + baseline)
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   ctr                  = round(clicks * 100 / impressions, 2)   (0 when impressions = 0)
--   spend                = round(spend, 2)
--   ctr_change           = current.ctr - baseline.ctr
--   clicks_change        = current.clicks - baseline.clicks
--   clicks_change_pct    = pct_change(current.clicks, baseline.clicks) = (cur-base)/base*100
--   impressions_change   = current.impressions - baseline.impressions
--   impressions_change_pct = pct_change(current.impressions, baseline.impressions)
--   spend_change         = round(current.spend - baseline.spend, 2)
-- =====================================================================

    SELECT
        SUM(CASE WHEN {channel_condition} THEN clicks ELSE 0 END) AS clicks,
        SUM(CASE WHEN {channel_condition} THEN impressions ELSE 0 END) AS impressions,
        SUM(CASE WHEN {channel_condition} THEN cost * scc.conversion_factor ELSE 0 END) AS spend
    FROM `prj-onlinesales-prod-01.reporting.client_vendor_channel_performance_facts` cvcpf
    INNER JOIN `prj-onlinesales-prod-01.reporting.clients` clients
        ON clients.client_id = cvcpf.client_id
        AND clients.agency_id = '{agency_id}'
    INNER JOIN `prj-onlinesales-prod-01.reporting.marketplace_clients` mc
        ON mc.agency_id = clients.agency_id
        AND clients.client_id != mc.marketplace_client_id
        AND mc.agency_id = '{agency_id}'
    INNER JOIN `prj-onlinesales-prod-01.reporting.static_currency_conversion` scc
        ON scc.from_currency = cvcpf.currency
        AND scc.to_currency = mc.currency
    WHERE cvcpf.date >= '{sd}' AND cvcpf.date <= '{ed}'
    {merchant_filter}
