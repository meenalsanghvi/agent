-- =====================================================================
-- id:                       shared.get_product_selection_changes.product_names
-- source:                   tools/common_tools.py:399  (fn get_product_selection_changes -> name_query)
-- agent:                    shared
-- description:              Batch SKU -> product_name (e_name) lookup for the (client_id, sku_id) pairs surfaced by get_product_selection_changes. Single call, follow-up to the main audit query.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   (none — see injected_fragments)
-- injected_fragments:                                  (SQL spliced in by a helper/branch)
--   {pairs_str}  <- ", ".join("('{client_id}', '{sku_id}')" for each distinct valid pair)
--                   e.g. "('10092920', 'SKU1'), ('10092920', 'SKU2')"
--                   -> WHERE (client_id, sku_id) IN (...)
-- tables:
--   reporting.merchant_merchandise_product_dimensions
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          single call
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   name_map  = {(client_id, sku_id): product_name}  used to annotate each change row
-- =====================================================================

        SELECT DISTINCT
            client_id,
            sku_id,
            e_name AS product_name
        FROM `prj-onlinesales-prod-01.reporting.merchant_merchandise_product_dimensions`
        WHERE (client_id, sku_id) IN ({pairs_str})
