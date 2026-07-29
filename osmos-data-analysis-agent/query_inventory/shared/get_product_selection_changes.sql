-- =====================================================================
-- id:                       shared.get_product_selection_changes
-- source:                   tools/common_tools.py:353  (fn get_product_selection_changes)
-- agent:                    shared
-- description:              Product selection audit log (action_type_id 50=added / 51=removed) for specific merchants/campaigns in a period: sku_id, action, who + when. Single call. (SKU names resolved by a follow-up query -> get_product_selection_changes__product_names.)
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
-- tables:
--   audit.audit_logs_v2
-- region_specific:          false
-- timezone_aware:           true   (DATETIME(timestamp, '{timezone}'); TIMESTAMP('{date}', '{timezone}'))
-- comparison_mode:          single call
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   product_name  = resolved via get_product_selection_changes__product_names, else 'Unknown Product'
--   changes       = all rows
--   additions     = rows where action = 'added'
--   removals      = rows where action = 'removed'
--   summary.total_changes / additions_count / removals_count
--   summary.unique_campaigns / unique_clients / unique_skus (nunique)
-- =====================================================================

    SELECT
        entity_id AS client_id,
        scope_id AS marketing_campaign_id,
        JSON_EXTRACT_SCALAR(scope_metadata, '$.campaignName') AS campaign_name,
        JSON_EXTRACT_SCALAR(scope_metadata, '$.campaignType') AS campaign_type,
        JSON_EXTRACT_SCALAR(scope_metadata, '$.campaignSubType') AS campaign_subtype,
        JSON_EXTRACT_SCALAR(metadata, '$.skuId') AS sku_id,
        CASE WHEN action_type_id = 50 THEN 'added' ELSE 'removed' END AS action,
        JSON_EXTRACT_SCALAR(user, '$.name') AS changed_by,
        JSON_EXTRACT_SCALAR(user, '$.userType') AS changed_by_type,
        DATETIME(timestamp, '{timezone}') AS change_timestamp
    FROM `prj-onlinesales-prod-01.audit.audit_logs_v2`
    WHERE
        agency_id = '{agency_id}'
        AND action_type_id IN (50, 51)
        AND timestamp >= TIMESTAMP('{start_date}', '{timezone}')
        AND timestamp < TIMESTAMP(DATE_ADD('{end_date}', INTERVAL 1 DAY), '{timezone}')
        {extra_filters}
    ORDER BY timestamp DESC
