-- =====================================================================
-- id:                       rr.get_filter_presence_response_rates
-- source:                   tools/rr_analysis_tools.py:1015  (fn get_filter_presence_response_rates)
-- agent:                    rr
-- description:              Single-scan conditional aggregation over the raw region-specific request log: present vs absent request/response counts for each client-sent filter over a recent lookback window. Single call (recent window, not pre/post period).
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {marketplace_client_id} str  -> __MARKETPLACE_CLIENT_ID__
--   {region}                str  -> __REGION__     (selects dataset reporting_{region})
--   {timezone}              str  -> __TIMEZONE__
--   {start_date}            date -> __START_DATE_1__   (derived: end - lookback_days + 1)
--   {end_date}              date -> __END_DATE_1__     (defaults to today)
-- injected_fragments:                                  (SQL spliced in by helper)
--   {select_sql}   <- total_requests + total_responses, then per selected filter f:
--                     "SUM(CASE WHEN (r.{col} IS NOT NULL AND TRIM(CAST(r.{col} AS STRING)) != '') THEN 1 ELSE 0 END) AS {f}_present_req"
--                     and the {f}_present_res / {f}_absent_req / {f}_absent_res variants.
--                     col from: brands->f_brands, zone->f_zone, storeid->f_storeid,
--                     network->f_network, city->f_city, state->f_state, country->f_country, device->device
--   {scope_clauses} <- optional AND filters on r.f_pt / r.f_cat1 / r.f_cat2 / r.f_cat3
--   {dataset}       <- get_region_dataset(region) -> reporting_{region} (or reporting)
-- tables:
--   {dataset}.os_product_ads_request_report   (region-specific: reporting_{region}.os_product_ads_request_report)
-- region_specific:          true   (dataset = reporting_{region} via get_region_dataset; run_query location resolved from dataset)
-- timezone_aware:           true   (DATE(TIMESTAMP(r.timestamp_utc), '{timezone}'))
-- comparison_mode:          single call
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   present.response_rate           = present_res * 100 / present_req  (per filter)
--   absent.response_rate            = absent_res * 100 / absent_req    (per filter)
--   present.request_share_pct       = share_pct(present_req, total_requests)
--   absent.request_share_pct        = share_pct(absent_req, total_requests)
--   rr_delta_present_minus_absent   = present_rr - absent_rr
--   overall_response_rate           = total_responses * 100 / total_requests
--   data_availability_warning       = warn if window > 15 days (os_product_ads_request_report retention)
-- =====================================================================

    SELECT
        {select_sql}
    FROM
        `prj-onlinesales-prod-01.{dataset}.os_product_ads_request_report` r
    WHERE
        r.mcid = '{marketplace_client_id}'
        AND DATE(TIMESTAMP(r.timestamp_utc), '{timezone}') >= '{start_date}'
        AND DATE(TIMESTAMP(r.timestamp_utc), '{timezone}') <= '{end_date}'{scope_clauses}
