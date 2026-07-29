-- =====================================================================
-- id:                       shared.get_campaign_targeted_keywords.targeted
-- source:                   tools/common_tools.py:1424  (fn get_campaign_targeted_keywords -> targeted_query)
-- agent:                    shared
-- description:              Active TARGETED keywords (is_negative=0, is_deleted=0) a SEARCH campaign bids on: text + merchant-set bidding_value. Single call. (Paired with the negative-keyword query.)
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {safe_mcid}   str -> __MARKETPLACE_CLIENT_ID__   (marketplace_client_id, ' stripped, SAFE_CAST INT64)
--   {safe_cid}    str -> __MARKETING_CAMPAIGN_ID__   (marketing_campaign_id, ' stripped, SAFE_CAST INT64)
--   {safe_client} str -> __CLIENT_ID__               (os_client_id, ' stripped, SAFE_CAST INT64)
-- injected_fragments:                                  (none)
-- tables:
--   reporting.os_ads_db_campaign_level_keywords
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          single call
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   targeted_keywords      = rows [{text, bidding_value}]
--   targeted_keyword_count = len(targeted_keywords)
-- =====================================================================

    SELECT text, bidding_value
    FROM `prj-onlinesales-prod-01.reporting.os_ads_db_campaign_level_keywords`
    WHERE
        marketplace_client_id = SAFE_CAST('{safe_mcid}' AS INT64)
        AND marketing_campaign_id = SAFE_CAST('{safe_cid}' AS INT64)
        AND client_id = SAFE_CAST('{safe_client}' AS INT64)
        AND is_deleted = 0
        AND is_negative = 0
