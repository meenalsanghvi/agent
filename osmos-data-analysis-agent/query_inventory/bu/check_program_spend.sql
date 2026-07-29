-- =====================================================================
-- id:                       bu.check_program_spend
-- source:                   tools/bu_analysis_tools.py:44  (fn check_program_spend)
-- agent:                    bu
-- description:              Total program spend (marketplace currency) for ONE date range, single scalar. Spend stable does NOT imply BU stable.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {agency_id}    str    -> __AGENCY_ID__
--   {start_date}   date   -> __START_DATE_1__
--   {end_date}     date   -> __END_DATE_1__
-- injected_fragments:                                  (SQL spliced in by a helper)
--   {channel_condition}  <- get_channel_filter(program_type, include_vendor=True)
--                        pla     -> "vendor = 'os_ads' AND channel = 'os_product_ads'"
--                        display -> "vendor = 'os_ads' AND channel IN ('guaranteed_display_ads', 'auction_display_ads')"
--                        all     -> "vendor = 'os_ads' AND channel IN ('os_product_ads', 'guaranteed_display_ads', 'auction_display_ads')"
-- tables:
--   reporting.client_vendor_channel_performance_facts
--   reporting.clients
--   reporting.marketplace_clients
--   reporting.static_currency_conversion
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          single call (agent calls once per period to compare)
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   spend = round(float(row.spend) or 0, 2)   (null-safe passthrough of the single SUM row)
-- =====================================================================

SELECT
    SUM(cvcpf.cost * scc.conversion_factor) AS spend
FROM `prj-onlinesales-prod-01.reporting.client_vendor_channel_performance_facts` cvcpf
INNER JOIN `prj-onlinesales-prod-01.reporting.clients` clients
    ON clients.client_id = cvcpf.client_id
    AND clients.agency_id = '{agency_id}'
INNER JOIN `prj-onlinesales-prod-01.reporting.marketplace_clients` mc
    ON mc.agency_id = clients.agency_id
    AND clients.client_id != mc.marketplace_client_id
INNER JOIN `prj-onlinesales-prod-01.reporting.static_currency_conversion` scc
    ON scc.from_currency = cvcpf.currency
    AND scc.to_currency = mc.currency
WHERE {channel_condition}
    AND cvcpf.date >= '{start_date}' AND cvcpf.date <= '{end_date}'
