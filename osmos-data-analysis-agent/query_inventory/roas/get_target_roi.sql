-- =====================================================================
-- id:                       roas.get_target_roi
-- source:                   tools/roi_analysis_tools.py:120  (fn get_target_roi)
-- agent:                    roas
-- description:              Marketplace target ROI benchmark for one agency (single scalar lookup).
-- proposed_kam_report_type: KAM_AGENT_ROAS_TARGET_ROI
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {agency_id}   str    -> __AGENCY_ID__
-- injected_fragments:                                  (none)
-- tables:
--   reporting.agencies
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          single call
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   target_roi = df.iloc[0]["target_roi"]   (passthrough; None + error="Agency not found" when no row)
-- =====================================================================

SELECT target_roi
FROM `prj-onlinesales-prod-01.reporting.agencies`
WHERE agency_id = '{agency_id}'
