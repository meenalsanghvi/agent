-- =====================================================================
-- id:                       budget_pacing.get_budget_delivery_mode
-- source:                   tools/budget_pacing_tools.py:486  (fn get_budget_delivery_mode)
-- agent:                    budget_pacing
-- description:              Budget delivery (pacing) mode — ACCELERATED vs STANDARD — for one or more PLA campaigns.
-- proposed_kam_report_type: TBD
-- parameters:               (none scalar)
-- injected_fragments:                                  (SQL spliced in by a helper)
--   {ids_str}  <- ", ".join(f"'{cid}'" for cid in marketing_campaign_ids)
--                 e.g. "'123', '456'"
-- tables:
--   reporting.marketing_campaign_dimensions
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          single call
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   accelerated_campaigns = sorted ids where budget_delivery_mode.upper() == "ACCELERATED"
--   standard_campaigns    = sorted ids where budget_delivery_mode.upper() == "STANDARD"
--   campaigns_not_found   = sorted(set(marketing_campaign_ids) - found_ids)
--   summary.total_requested / accelerated_count / standard_count / not_found_count
-- =====================================================================

SELECT
    marketing_campaign_id,
    budget_delivery_mode
FROM `prj-onlinesales-prod-01.reporting.marketing_campaign_dimensions`
WHERE marketing_campaign_id IN ({ids_str})
