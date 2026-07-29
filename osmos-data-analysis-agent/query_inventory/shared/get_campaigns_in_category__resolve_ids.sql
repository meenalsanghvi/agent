-- =====================================================================
-- id:                       shared.get_campaigns_in_category.resolve_ids
-- source:                   tools/common_tools.py:1820  (fn get_campaigns_in_category -> resolve_query)
-- agent:                    shared
-- description:              Resolve any marketing_campaign_group_ids passed in marketing_campaign_ids to their marketing_campaign_ids, so the main category query can filter uniformly. Single call, runs only when marketing_campaign_ids provided.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   (none directly — see injected_fragments)
-- injected_fragments:                                  (SQL spliced in by a helper/branch)
--   {id_list_sql}  <- ", ".join("'{mid}'" for mid in raw_ids)   (the caller-supplied ids)
--                     -> WHERE marketing_campaign_group_id IN (...)
-- tables:
--   reporting.campaign_tagging_data
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          single call
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   resolved_ids = df.mid.tolist(); all_ids = set(raw_ids + resolved_ids) -> feeds main query filter
-- =====================================================================

        SELECT DISTINCT CAST(marketing_campaign_id AS STRING) AS mid
        FROM `prj-onlinesales-prod-01.reporting.campaign_tagging_data`
        WHERE marketing_campaign_group_id IN ({id_list_sql})
