-- =====================================================================
-- id:                       shared.fetch_marketplace_info
-- source:                   tools/state_tools.py:23  (fn fetch_marketplace_info)
-- agent:                    shared
-- description:              Look up active 'monetize' marketplaces whose name matches a user-supplied substring (case-insensitive LIKE), returning agency/region/currency/timezone context. Primary exact-substring match.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {marketplace_name.lower()}   str  -> __MARKETPLACE_NAME__   (lower-cased user input, embedded inside a LIKE "%...%")
-- injected_fragments:                                  (none)
-- tables:
--   reporting.agencies
--   reporting.marketplace_clients
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          single call
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   (no numeric derived metrics)
--   post-processing = if 0 rows -> run fuzzy-fallback query (fetch_marketplace_info__all) and rank names with rapidfuzz WRatio (limit=3, score_cutoff=65);
--                     if 1 match -> auto-store {marketplace_client_id, agency_id, region, currency, timezone} into session state;
--                     if >1 match -> return list for user selection
-- =====================================================================

    SELECT a.name, a.marketplace_client_id, a.agency_id, a.region, a.currency, mc.timezone
    FROM `prj-onlinesales-prod-01.reporting.agencies` a
    JOIN `prj-onlinesales-prod-01.reporting.marketplace_clients` mc
      ON mc.marketplace_client_id = a.marketplace_client_id
    WHERE LOWER(a.name) LIKE "%{marketplace_name.lower()}%"
      AND LOWER(a.name) NOT LIKE "%staging%"
      AND LOWER(a.name) NOT LIKE "%sandbox%"
      AND a.status_type = 'ACTIVE'
      AND a.marketplace_type = 'monetize'
