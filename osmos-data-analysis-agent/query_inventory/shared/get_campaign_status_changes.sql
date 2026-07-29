-- =====================================================================
-- id:                       shared.get_campaign_status_changes
-- source:                   tools/common_tools.py:244  (fn get_campaign_status_changes)
-- agent:                    shared
-- description:              Campaign status-change audit log (action_type_id=16) for specific merchants/campaigns in a period: old_status -> new_status, who + when. Single call.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {agency_id}   str   -> __AGENCY_ID__
--   {timezone}    str   -> __TIMEZONE__
--   {start_date}  date  -> __START_DATE_1__
--   {end_date}    date  -> __END_DATE_1__
-- injected_fragments:                                  (SQL spliced in by a helper/branch)
--   {extra_filters}  <- built inline from client_ids / marketing_campaign_ids (at least one required)
--                       client_ids            -> " AND entity_id IN ('c1', 'c2', ...)"
--                       marketing_campaign_ids-> " AND scope_id IN ('m1', 'm2', ...)"
--   {f"LIMIT {top_n}" if top_n else ""}  <- optional row cap (empty string when top_n is None)
-- tables:
--   audit.audit_logs_v2
-- region_specific:          false
-- timezone_aware:           true   (DATETIME(timestamp, '{timezone}'); TIMESTAMP('{date}', '{timezone}'))
-- comparison_mode:          single call
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   changes             = all rows
--   paused_campaigns    = rows where new_status contains 'PAUSED' (case-insensitive)
--   activated_campaigns = rows where new_status contains 'ACTIVE' (case-insensitive)
--   summary.total_changes / paused_count / activated_count
--   summary.unique_campaigns = nunique(marketing_campaign_id)
--   truncated = True when len(changes) == top_n
-- =====================================================================

    SELECT
        entity_id AS client_id,
        scope_id AS marketing_campaign_id,
        JSON_EXTRACT_SCALAR(scope_metadata, '$.campaignName') AS campaign_name,
        JSON_EXTRACT_SCALAR(old_state, '$.status') AS old_status,
        JSON_EXTRACT_SCALAR(new_state, '$.status') AS new_status,
        DATETIME(timestamp, '{timezone}') AS change_timestamp
    FROM `prj-onlinesales-prod-01.audit.audit_logs_v2`
    WHERE
        agency_id = '{agency_id}'
        AND action_type_id = 16
        AND timestamp >= TIMESTAMP('{start_date}', '{timezone}')
        AND timestamp < TIMESTAMP(DATE_ADD('{end_date}', INTERVAL 1 DAY), '{timezone}')
        {extra_filters}
    ORDER BY timestamp DESC
    {f"LIMIT {top_n}" if top_n else ""}
