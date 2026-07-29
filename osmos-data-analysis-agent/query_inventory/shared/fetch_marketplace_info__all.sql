-- =====================================================================
-- id:                       shared.fetch_marketplace_info.all
-- source:                   tools/state_tools.py:38  (fn fetch_marketplace_info)
-- agent:                    shared
-- description:              Fuzzy-fallback: fetch ALL active 'monetize' marketplaces (name + agency/region/currency/timezone context) so the app can rapidfuzz-match the user's input when the primary LIKE query returns nothing.
-- proposed_kam_report_type: TBD
-- parameters:                                          (none — static query, no placeholders)
-- injected_fragments:                                  (none)
-- tables:
--   reporting.agencies
--   reporting.marketplace_clients
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          single call
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   (no numeric derived metrics)
--   post-processing = fuzz_process.extract(marketplace_name, all_names, scorer=fuzz.WRatio, limit=3, score_cutoff=65);
--                     if 1 match -> auto-store {marketplace_client_id, agency_id, region, currency, timezone} into session state;
--                     if >1 match -> return numbered suggestion list for user selection
-- =====================================================================

        SELECT a.name, a.marketplace_client_id, a.agency_id, a.region, a.currency, mc.timezone
        FROM `prj-onlinesales-prod-01.reporting.agencies` a
        JOIN `prj-onlinesales-prod-01.reporting.marketplace_clients` mc
          ON mc.marketplace_client_id = a.marketplace_client_id
        WHERE LOWER(a.name) NOT LIKE "%staging%"
          AND LOWER(a.name) NOT LIKE "%sandbox%"
          AND a.status_type = 'ACTIVE'
          AND a.marketplace_type = 'monetize'
