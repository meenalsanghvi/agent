-- =====================================================================
-- id:                       shared.get_campaigns_in_category
-- source:                   tools/common_tools.py:1868  (fn get_campaigns_in_category -> _period_query)
-- agent:                    shared
-- description:              PLA campaigns competing in a category for one period, each with category-level spend/cpc/cpm, daily budget, campaign_subtype and derived bid model (bidding_strategy_type CASE). Called once per period; comparison mode runs it for current + baseline.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {agency_id}  str  -> __AGENCY_ID__   (appears 3x: CTE agencies filter, outer merchant JOIN, outer WHERE)
--   {sd}         date -> __START_DATE_1__   (baseline call -> __START_DATE_2__)
--   {ed}         date -> __END_DATE_1__     (baseline call -> __END_DATE_2__)
--   {top_n}      int  -> __LIMIT__
-- injected_fragments:                                  (SQL spliced in by a helper/branch)
--   {category_filter_clause} <- space-joined optional filters (at least one filter required overall):
--                               "AND LOWER(opacrp_raw.category_lN) = LOWER('{value}')" per level;
--                               "AND opacrp_raw.client_id IN (...)";
--                               "AND opacrp_raw.marketing_campaign_id IN (...)"  (ids resolved via resolve_ids query)
--   {cte_cat_select} / {cte_cat_group} / {outer_cat_select} / {outer_cat_group}
--                            <- raw category_l1[/l2/l3] column lists at the requested level
--   {bidding_strategy_type_case} <- large CASE -> campaign_group_bidding_strategy_type
--                            (see _fragment_bidding_strategy_type.sql; uses
--                             _meta = REPLACE(mcd.campaign_setting_metadata, '""', '"'))
-- tables:
--   reporting.os_product_ads_campaign_category_report_pla
--   reporting.agencies
--   reporting.marketing_campaign_dimensions
--   reporting.marketing_campaign_group_dimensions
--   reporting.monetize_merchant_dimensions
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          called once per period (current + baseline)
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   category_path = " > ".join(category_l1, l2, l3)   (display-only breadcrumb)
--   -- single-period:
--   paused_campaigns = rows where campaign_group_status contains 'PAUSED'
--   low_bu_campaigns = rows where daily_budget>0 AND campaign_category_spend < daily_budget*0.5
--   -- comparison mode (merge on merchant_id, os_client_id, marketing_campaign_id + category keys):
--   status            = active_both | new | churned   (from spend_current>0 / spend_baseline>0)
--   spend_change / cpc_change / cpm_change = current - baseline
--   spend_share_current_pct / spend_share_baseline_pct = spend / total_spend * 100
--   contribution_to_spend_change_pct = spend_change / total_spend_delta * 100
--   new_entrants_in_period = status=='new' rows ranked by current spend
--   subtype_summary  = per campaign_subtype rolled current_spend / baseline_spend / spend_change
--   summary totals: current/baseline total_category_spend + change, counts
-- =====================================================================

    WITH cte AS (
        SELECT
            opacrp_raw.merchant_id,
            opacrp_raw.client_id,
            opacrp_raw.marketing_campaign_id,
            {cte_cat_select},
            SUM(opacrp_raw.cost) AS cost,
            SUM(opacrp_raw.clicks) AS clicks,
            SUM(opacrp_raw.impressions) AS impressions
        FROM `prj-onlinesales-prod-01.reporting.os_product_ads_campaign_category_report_pla` opacrp_raw
        INNER JOIN `prj-onlinesales-prod-01.reporting.agencies` agencies
            ON agencies.marketplace_client_id = opacrp_raw.marketplace_client_id
        WHERE agencies.agency_id = '{agency_id}'
            AND opacrp_raw.date >= '{sd}'
            AND opacrp_raw.date <= '{ed}'
            {category_filter_clause}
        GROUP BY opacrp_raw.merchant_id, opacrp_raw.client_id, opacrp_raw.marketing_campaign_id, {cte_cat_group}
        HAVING SUM(opacrp_raw.product_count) > 0 OR SUM(opacrp_raw.cost) > 0
    )
    SELECT
        mmd.merchant_name,
        mmd.merchant_id,
        cte.client_id AS os_client_id,
        cte.marketing_campaign_id,
        {outer_cat_select},
        mcgd.marketing_campaign_group_alias AS campaign_group_name,
        REPLACE(mcgd.effective_status, '_', ' ') AS campaign_group_status,
        mcgd.daily_budget AS campaign_group_daily_budget,
        {bidding_strategy_type_case} AS campaign_group_bidding_strategy_type,
        LOWER(mcgd.campaign_subtype) AS campaign_subtype,
        ROUND(SUM(cte.cost), 2) AS campaign_category_spend,
        ROUND(CASE WHEN SUM(cte.clicks) > 0
            THEN SUM(cte.cost) / SUM(cte.clicks) ELSE 0 END, 2) AS campaign_category_cpc,
        ROUND(CASE WHEN SUM(cte.impressions) > 0
            THEN (SUM(cte.cost) * 1000) / SUM(cte.impressions) ELSE 0 END, 2) AS campaign_category_cpm
    FROM cte
    INNER JOIN `prj-onlinesales-prod-01.reporting.marketing_campaign_dimensions` mcd
        ON mcd.client_id = cte.client_id
        AND mcd.marketing_campaign_id = cte.marketing_campaign_id
    INNER JOIN `prj-onlinesales-prod-01.reporting.marketing_campaign_group_dimensions` mcgd
        ON mcgd.client_id = cte.client_id
        AND mcgd.marketing_campaign_group_id = mcd.marketing_campaign_group_id
    INNER JOIN `prj-onlinesales-prod-01.reporting.monetize_merchant_dimensions` mmd
        ON LOWER(mmd.merchant_id) = LOWER(cte.merchant_id)
        AND mmd.agency_id = '{agency_id}'
    WHERE mmd.agency_id = '{agency_id}'
        AND (mcd.campaign_origin != 'PACKAGE_BASED' OR mcd.campaign_origin IS NULL)
    GROUP BY
        mmd.merchant_name, mmd.merchant_id, cte.client_id, cte.marketing_campaign_id,
        {outer_cat_group}, mcgd.marketing_campaign_group_alias, mcgd.effective_status, mcgd.daily_budget,
        mcgd.campaign_subtype, campaign_group_bidding_strategy_type
    ORDER BY campaign_category_spend DESC
    LIMIT {top_n}
