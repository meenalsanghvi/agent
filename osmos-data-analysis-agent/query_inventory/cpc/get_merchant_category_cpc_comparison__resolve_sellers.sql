-- =====================================================================
-- id:                       cpc.get_merchant_category_cpc_comparison.resolve_sellers
-- source:                   tools/cpc_analysis_tools.py:477  (fn get_merchant_category_cpc_comparison)
-- agent:                    cpc
-- description:              Resolve the given os_client_ids to their seller_ids (merchant_id used in the category facts table). Runs only when client_ids are passed and seller_ids are not.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {agency_id}   str   -> __AGENCY_ID__
-- injected_fragments:                                  (SQL spliced in by a helper)
--   {cid_in}  <- built inline from client_ids: ", ".join("'{c}'" ...)  ->  "'c1', 'c2', ..."
-- tables:
--   reporting.clients
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          single call
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   sellers = [str(s) for s in seller_id column]   (list of resolved seller_ids fed into the main category query)
-- =====================================================================

SELECT DISTINCT seller_id FROM `prj-onlinesales-prod-01.reporting.clients` WHERE agency_id = '{agency_id}' AND client_id IN ({cid_in}) AND seller_id IS NOT NULL
