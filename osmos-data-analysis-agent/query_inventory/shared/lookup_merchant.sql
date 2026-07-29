-- =====================================================================
-- id:                       shared.lookup_merchant
-- source:                   tools/common_tools.py:60  (fn lookup_merchant)
-- agent:                    shared
-- description:              Resolve a merchant within a marketplace by client_id (os_client_id) OR merchant_id (seller_id); returns merchant_id, client_id, merchant_name. Single call.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {marketplace_client_id} str -> __MARKETPLACE_CLIENT_ID__
--   {agency_id}             str -> __AGENCY_ID__
-- injected_fragments:                                  (SQL spliced in by a helper/branch)
--   {where_clause}  <- built inline from client_id / merchant_id (exactly one is provided)
--                      client_id  -> "mmd.client_id = '{client_id}'"
--                      merchant_id-> "mmd.merchant_id = '{merchant_id}'"
-- tables:
--   reporting.monetize_merchant_dimensions
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          single call
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   (none — first row returned as {client_id, merchant_id, merchant_name}; error if empty)
-- =====================================================================

    SELECT
        mmd.merchant_id,
        mmd.client_id,
        mmd.merchant_name
    FROM `prj-onlinesales-prod-01.reporting.monetize_merchant_dimensions` mmd
    WHERE {where_clause}
        AND mmd.marketplace_client_id = '{marketplace_client_id}'
        AND mmd.agency_id = '{agency_id}'
    LIMIT 1
