-- =====================================================================
-- id:                       shared.get_campaign_targeted_networks.by_campaign_id
-- source:                   tools/common_tools.py:1520  (fn get_campaign_targeted_networks, campaign_id branch)
-- agent:                    shared
-- description:              Targeted NETWORK mappings for a campaign, filtered DIRECTLY on the internal numeric campaign_id (target_type='NETWORK', is_deleted=0). Single call. Used when the caller already holds campaign_id.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {safe_client} str -> __CLIENT_ID__     (os_client_id, ' stripped, SAFE_CAST INT64)
--   {safe_id}     str -> __CAMPAIGN_ID__   (internal numeric campaign_id, ' stripped, SAFE_CAST INT64)
-- injected_fragments:                                  (none — branch selected by id_type == campaign_id)
-- tables:
--   reporting.os_ads_db_campaign_targeting_mapping
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          single call
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   networks      = rows [{campaign_id, target_details}] (all values str-cast)
--   network_count = len(networks)
--   matched_on    = 'campaign_id'
-- =====================================================================

        SELECT
            ctm.campaign_id,
            TO_JSON_STRING(ctm.target_details) AS target_details
        FROM `prj-onlinesales-prod-01.reporting.os_ads_db_campaign_targeting_mapping` ctm
        WHERE
            ctm.target_type = 'NETWORK'
            AND ctm.is_deleted = 0
            AND ctm.client_id = SAFE_CAST('{safe_client}' AS INT64)
            AND ctm.campaign_id = SAFE_CAST('{safe_id}' AS INT64)
