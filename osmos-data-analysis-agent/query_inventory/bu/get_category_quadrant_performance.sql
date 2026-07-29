-- =====================================================================
-- id:                       bu.get_category_quadrant_performance
-- source:                   tools/bu_analysis_tools.py:307  (fn get_category_quadrant_performance)
-- agent:                    bu
-- description:              PLA category-level (L1/L2/L3) quadrant for ONE date range: avg request count, response rate, spend, daily budget, BU%, unique campaigns/merchants.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {agency_id}    str    -> __AGENCY_ID__
--   {start_date}   date   -> __START_DATE_1__
--   {end_date}     date   -> __END_DATE_1__
--   {level}        str    -> __CATEGORY_LEVEL__   (l1|l2|l3; also -> 'category_{level}' in WHERE)
--   {top_n}        int    -> __TOP_N__
--   {category_l1_filter} str -> __CATEGORY_L1__   (optional)
--   {category_l2_filter} str -> __CATEGORY_L2__   (optional)
--   {category_l3_filter} str -> __CATEGORY_L3__   (optional)
-- injected_fragments:                                  (SQL spliced in by a helper)
--   {cat_path_expr}          <- selected category-path expr per level
--                               l1 -> "q.category_l1"
--                               l2 -> "CONCAT(q.category_l1, ' > ', q.category_l2)"
--                               l3 -> "CONCAT(q.category_l1, ' > ', q.category_l2, ' > ', q.category_l3)"
--   {spends_join_condition}  <- LOWER() join between quadrant and campaign-category subqueries, widening per level (l1 / l1+l2 / l1+l2+l3, NULL/'na' tolerant)
--   {category_filter_clause} <- cumulative "AND LOWER(qd.category_lN) = LOWER('{...}')" per supplied l1/l2/l3 filter (else "")
-- tables:
--   reporting.os_product_ads_daily_category_quadrant_report_pla
--   reporting.agencies
--   reporting.static_currency_conversion
--   reporting.os_product_ads_campaign_category_report_pla
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          single call (agent calls once per period to compare)
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   (none numeric; all metrics computed in SQL) rows passed through; total_categories = len(rows)
-- =====================================================================

SELECT
    {cat_path_expr} AS category_path,
    ROUND(AVG(q.request_count), 2) AS request_count,
    CASE
        WHEN ROUND(AVG(q.response_percentage), 2) > 100 THEN 100
        ELSE ROUND(AVG(q.response_percentage), 2)
    END AS response_rate,
    ROUND(AVG(q.cost), 2) AS spend,
    CASE
        WHEN AVG(q.daily_budget) > AVG(q.cost) THEN ROUND(AVG(q.daily_budget), 2)
        ELSE ROUND(AVG(q.cost), 2)
    END AS campaign_group_daily_budget,
    CASE
        WHEN AVG(q.daily_budget) < AVG(q.cost) OR ROUND(AVG(q.budget_utilisation_perc), 2) > 100 THEN 100
        ELSE ROUND(AVG(q.budget_utilisation_perc), 2)
    END AS budget_utilisation_perc,
    COUNT(DISTINCT s.campaign_id) AS uniq_campaigns_count,
    COUNT(DISTINCT s.merchant_id) AS uniq_merchant_count
FROM (
    SELECT
        qd.category_l1,
        qd.category_l2,
        qd.category_l3,
        SUM(qd.requests) AS request_count,
        SUM(qd.responses) AS response_count,
        CASE
            WHEN SUM(qd.responses) > 0 THEN SUM(qd.responses) * 100.0 / SUM(qd.requests)
            ELSE 0
        END AS response_percentage,
        SUM(qd.cost_usd * scc.conversion_factor) AS cost,
        SUM(qd.calculated_budget_usd * scc.conversion_factor) AS daily_budget,
        CASE
            WHEN SUM(qd.calculated_budget_usd) > 0
                THEN SUM(qd.cost_usd) * 100.0 / SUM(qd.calculated_budget_usd)
            ELSE 0
        END AS budget_utilisation_perc
    FROM `prj-onlinesales-prod-01.reporting.os_product_ads_daily_category_quadrant_report_pla` qd
    INNER JOIN `prj-onlinesales-prod-01.reporting.agencies` a
        ON a.marketplace_client_id = qd.marketplace_client_id
        AND a.agency_id = '{agency_id}'
    INNER JOIN `prj-onlinesales-prod-01.reporting.static_currency_conversion` scc
        ON scc.from_currency = 'USD'
        AND scc.to_currency = a.currency
    WHERE qd.date >= '{start_date}' AND qd.date <= '{end_date}'
        AND qd.category_level = 'category_{level}'
        AND qd.category_l1 IS NOT NULL
        AND qd.category_l1 <> 'na'
        {category_filter_clause}
    GROUP BY 1, 2, 3
    HAVING SUM(qd.requests) > 5000
) q
LEFT JOIN (
    SELECT
        CASE WHEN cr.category_l1 IS NULL OR cr.category_l1 = '' THEN 'na' ELSE cr.category_l1 END AS category_l1,
        CASE WHEN cr.category_l2 IS NULL OR cr.category_l2 = '' THEN 'na' ELSE cr.category_l2 END AS category_l2,
        CASE WHEN cr.category_l3 IS NULL OR cr.category_l3 = '' THEN 'na' ELSE cr.category_l3 END AS category_l3,
        cr.merchant_id,
        cr.marketing_campaign_id AS campaign_id,
        SUM(cr.cost) AS spend,
        SUM(cr.product_count) AS product_count
    FROM `prj-onlinesales-prod-01.reporting.os_product_ads_campaign_category_report_pla` cr
    CROSS JOIN `prj-onlinesales-prod-01.reporting.agencies` a
    WHERE a.marketplace_client_id = cr.marketplace_client_id
        AND a.agency_id = '{agency_id}'
        AND cr.date >= '{start_date}' AND cr.date <= '{end_date}'
    GROUP BY 1, 2, 3, 4, 5
    HAVING product_count > 0 OR spend > 0
) s ON {spends_join_condition}
WHERE q.category_l1 IS NOT NULL
GROUP BY 1
ORDER BY request_count DESC
LIMIT {top_n}
