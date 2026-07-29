-- =====================================================================
-- id:                       rr.get_category_request_volume
-- source:                   tools/rr_analysis_tools.py:586  (fn get_category_request_volume)
-- agent:                    rr
-- description:              Raw request volume (COUNT of rid) by category (l1/l2/l3) from the region-specific request log for ONE period. Called once per period; comparison mode runs it for current + baseline.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {marketplace_client_id} str  -> __MARKETPLACE_CLIENT_ID__
--   {region}                str  -> __REGION__     (selects dataset reporting_{region})
--   {timezone}              str  -> __TIMEZONE__
--   {start_date}            date -> __START_DATE_1__   (baseline call -> __START_DATE_2__)
--   {end_date}              date -> __END_DATE_1__     (baseline call -> __END_DATE_2__)
--   {top_n}                 int  -> __LIMIT__          (default 50)
-- injected_fragments:                                  (SQL spliced in by branch on category_level)
--   {cat_select}  <- l1 -> "r.f_cat1 AS category_l1"
--                    l2 -> "r.f_cat1 AS category_l1, r.f_cat2 AS category_l2"
--                    l3 -> "r.f_cat1 AS category_l1, r.f_cat2 AS category_l2, r.f_cat3 AS category_l3"
--   {cat_group}   <- l1 -> "r.f_cat1"  |  l2 -> "r.f_cat1, r.f_cat2"  |  l3 -> "r.f_cat1, r.f_cat2, r.f_cat3"
--   {dataset}     <- get_region_dataset(region)  -> reporting_{region} (or reporting)
-- tables:
--   {dataset}.os_product_ads_request_report   (region-specific: reporting_{region}.os_product_ads_request_report)
-- region_specific:          true   (dataset = reporting_{region} via get_region_dataset; run_query location resolved from dataset)
-- timezone_aware:           true   (DATE(TIMESTAMP(r.timestamp_utc), '{timezone}'))
-- comparison_mode:          called once per period (current + baseline)
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   category_path      = " > ".join(non-empty category levels) or "Unknown"
--   total_categories   = len(rows)
--   total_requests     = sum(request)
--   data_availability_warning = warn if date range > 15 days (os_product_ads_request_report retention)
-- =====================================================================

    SELECT
        {cat_select},
        COUNT(r.rid) AS request
    FROM
        `prj-onlinesales-prod-01.{dataset}.os_product_ads_request_report` r
    WHERE
        r.mcid = '{marketplace_client_id}'
        AND DATE(TIMESTAMP(r.timestamp_utc), '{timezone}') >= '{start_date}'
        AND DATE(TIMESTAMP(r.timestamp_utc), '{timezone}') <= '{end_date}'
        AND r.f_cat1 IS NOT NULL AND TRIM(r.f_cat1) != ''
    GROUP BY {cat_group}
    ORDER BY request DESC
    LIMIT {top_n}
