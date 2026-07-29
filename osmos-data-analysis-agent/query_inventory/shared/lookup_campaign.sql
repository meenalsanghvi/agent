-- =====================================================================
-- id:                       shared.lookup_campaign
-- source:                   tools/common_tools.py:141  (fn lookup_campaign)
-- agent:                    shared
-- description:              Resolve one campaign ID of a KNOWN type to all 4 ID types plus client_id, campaign_name (alias), type/subtype, bidding_strategy and status. Called once per raw_id in a loop.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   (none directly — see injected_fragments; the id column + value are spliced in)
-- injected_fragments:                                  (SQL spliced in by a helper/branch)
--   {where_clause}  <- "ctd.{id_type} = '{safe_id}'"   (id_type validated to one of:
--                      marketing_campaign_id, marketing_campaign_group_id,
--                      campaign_id, campaign_group_id; safe_id = raw_id with ' stripped)
-- tables:
--   reporting.campaign_tagging_data
--   reporting.marketing_campaign_dimensions
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          single call (once per input id)
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   (none — rows returned as-is; input_id + matched_on annotated; if empty, an error record is appended)
-- =====================================================================

        SELECT DISTINCT
            ctd.marketing_campaign_id,
            ctd.campaign_id,
            ctd.campaign_group_id,
            ctd.marketing_campaign_group_id,
            ctd.client_id,
            mcd.alias AS campaign_name,
            mcd.campaign_type,
            mcd.campaign_subtype,
            mcd.bidding_strategy,
            mcd.effective_status AS campaign_status
        FROM `prj-onlinesales-prod-01.reporting.campaign_tagging_data` ctd
        LEFT JOIN `prj-onlinesales-prod-01.reporting.marketing_campaign_dimensions` mcd
            ON ctd.marketing_campaign_id = mcd.marketing_campaign_id
            AND ctd.client_id = mcd.client_id
        WHERE {where_clause}
        LIMIT 10
