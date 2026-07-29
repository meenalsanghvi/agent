-- =====================================================================
-- id:                       shared.get_campaign_targeted_keywords.negative
-- source:                   tools/common_tools.py:1435  (fn get_campaign_targeted_keywords -> negative_query)
-- agent:                    shared
-- description:              Negative keywords (is_negative=1, is_deleted=0) explicitly excluded by a SEARCH campaign: text only. Single call. (Paired with the targeted-keyword query.)
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
--   negative_keywords      = rows [text]
--   negative_keyword_count = len(negative_keywords)
-- =====================================================================

    SELECT text
    FROM `prj-onlinesales-prod-01.reporting.os_ads_db_campaign_level_keywords`
    WHERE
        marketplace_client_id = SAFE_CAST('{safe_mcid}' AS INT64)
        AND marketing_campaign_id = SAFE_CAST('{safe_cid}' AS INT64)
        AND client_id = SAFE_CAST('{safe_client}' AS INT64)
        AND is_deleted = 0
        AND is_negative = 1
