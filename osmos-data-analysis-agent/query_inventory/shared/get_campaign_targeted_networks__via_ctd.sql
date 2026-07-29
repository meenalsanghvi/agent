-- =====================================================================
-- id:                       shared.get_campaign_targeted_networks.via_ctd
-- source:                   tools/common_tools.py:1533  (fn get_campaign_targeted_networks, else branch)
-- agent:                    shared
-- description:              Targeted NETWORK mappings for a campaign resolved through campaign_tagging_data when the caller holds a non-campaign_id key (marketing_campaign_id / campaign_group_id / marketing_campaign_group_id). Single call.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {safe_client} str -> __CLIENT_ID__   (os_client_id, ' stripped, SAFE_CAST INT64)
--   {safe_id}     str -> __CAMPAIGN_ID_VALUE__   (id value for the chosen ctd column, ' stripped)
-- injected_fragments:                                  (SQL spliced in by a helper/branch)
--   {ctd_col}  <- _CTD_ID_COLUMNS[id_type], one of:
--                 marketing_campaign_id | campaign_group_id | marketing_campaign_group_id
--                 -> "AND CAST(ctd.{ctd_col} AS STRING) = '{safe_id}'"
-- tables:
--   reporting.os_ads_db_campaign_targeting_mapping
--   reporting.campaign_tagging_data
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          single call
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   networks      = rows [{campaign_id, target_details}] (all values str-cast)
--   network_count = len(networks)
--   matched_on    = id_type used
-- =====================================================================

        SELECT
            ctm.campaign_id,
            TO_JSON_STRING(ctm.target_details) AS target_details
        FROM `prj-onlinesales-prod-01.reporting.os_ads_db_campaign_targeting_mapping` ctm
        INNER JOIN `prj-onlinesales-prod-01.reporting.campaign_tagging_data` ctd
            ON SAFE_CAST(ctd.campaign_id AS INT64) = ctm.campaign_id
            AND SAFE_CAST(ctd.client_id AS INT64) = ctm.client_id
        WHERE
            ctm.target_type = 'NETWORK'
            AND ctm.is_deleted = 0
            AND ctm.client_id = SAFE_CAST('{safe_client}' AS INT64)
            AND CAST(ctd.{ctd_col} AS STRING) = '{safe_id}'
        GROUP BY ctm.campaign_id, TO_JSON_STRING(ctm.target_details)
