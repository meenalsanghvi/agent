-- =====================================================================
-- id:                       cpc.get_sku_level_cpc_performance.resolve_marketplace_client
-- source:                   tools/cpc_analysis_tools.py:623  (fn get_sku_level_cpc_performance)
-- agent:                    cpc
-- description:              Look up the marketplace's own client record (marketplace_client_id) for the agency, used to attach the SITE/organic SKU funnel in the main SKU query.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {agency_id}   str   -> __AGENCY_ID__
-- injected_fragments:       none
-- tables:
--   reporting.agencies
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          single call
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   mkt_client_id = str(first row marketplace_client_id) or None   (None -> org/site SKU join is omitted from the SKU query)
-- =====================================================================

SELECT marketplace_client_id FROM `prj-onlinesales-prod-01.reporting.agencies` WHERE agency_id = '{agency_id}'
