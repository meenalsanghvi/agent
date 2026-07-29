"""Wave 1 — merge the shared-fact-table request/response (RR) families.

M3 RR_DISPLAY                  6 -> 1   os_display_ads_filtered_level_performance_facts
M4 RR_PLA                      3 -> 1   os_product_ads_filtered_level_report
M5 SEARCH_QUERY_REQUESTS_PLA   3 -> 1   os_product_ads_search_query_request_report
M7 PAGE_PERFORMANCE_PLA        3 -> 1   os_product_ads_page_name_performance_facts
M8 DISPLAY_AD_UNIT             3 -> 1   os_display_ads_ad_unit_facts

Every member of each family already ran the same template; they differed only in which
attributes they grouped by, which metrics they exposed, and a few hardcoded null/NA
guards. KAM builds SELECT/GROUP BY from the *requested* columns, so one config serves
all of them. Guards that are not shared by every member become caller filters -- see
MERGE_MAP.md for the exact filter each retired report needs.
"""

from merge_lib import col, run

DATE_WINDOW = "'__START_DATE_1__' AND '__END_DATE_1__'"


def sum_metric(alias, column, description):
    return col(
        f"COALESCE(SUM(CASE WHEN {alias}.date BETWEEN {DATE_WINDOW} "
        f"THEN {alias}.{column} ELSE 0 END), 0)",
        "FLOAT", description,
    )


def rate_metric(alias, num, den, description):
    return col(
        f"ROUND(SAFE_DIVIDE("
        f"SUM(CASE WHEN {alias}.date BETWEEN {DATE_WINDOW} THEN {alias}.{num} ELSE 0 END) * 100, "
        f"NULLIF(SUM(CASE WHEN {alias}.date BETWEEN {DATE_WINDOW} THEN {alias}.{den} ELSE 0 END), 0)), 2)",
        "FLOAT", description,
    )


SPECS = [
    # ------------------------------------------------------------------ M3
    {
        "path": "rr/INTERNAL_PERF_RR_DISPLAY.json",
        "reportType": "INTERNAL_PERF_RR_DISPLAY",
        "externalReportType": "RR_DISPLAY_REPORT",
        "filterTags": ["report_group:rr", "report_group:search_query"],
        "absorbs": [
            "rr/INTERNAL_PERF_RR_BY_DIMENSION_DISPLAY.json",
            "rr/INTERNAL_PERF_RR_DISPLAY_PAGE_TYPE.json",
            "rr/INTERNAL_PERF_RR_HOURLY.json",
            "rr/INTERNAL_PERF_RR_HOURLY_AD_UNIT.json",
            "rr/INTERNAL_PERF_SEARCH_QUERY_RR_DISPLAY.json",
            "rr/INTERNAL_PERF_SEARCH_QUERY_RR_DISPLAY_AD_UNIT.json",
        ],
        "description": """
            Display ad request / response volume and response rate for a marketplace over a
            period, grouped by any combination of the dimensions below: supply network, store,
            page type, device, ad unit, product category (L1-L3), hour of day, or the keyword
            the request carried. Replaces the six single-grain Display RR reports. Group by
            page_type for page-type RR, by hour for the hourly RR curve, by ad_unit to find ad
            units with zero responses, by keyword for keyword-level Display RR, or by keyword +
            ad_unit for the follow-up breakdown. Pass a NOT IN ('', 'NA') filter on the grouping
            column to reproduce the null/blank guards the retired reports hardcoded.
        """,
        "attributes": [
            "network", "page_type", "device", "ad_unit",
            "category_l1", "category_l2", "category_l3", "hour", "keyword",
        ],
        # store_id is DROPPED, not lost. RR_BY_DIMENSION_DISPLAY declared it with
        # selector `r.store_id`, but os_display_ads_filtered_level_performance_facts has
        # no such column -- requesting it 500s with "Name store_id not found inside r",
        # verified identically on the retired report. Shipping a column that can only
        # ever fail is worse than not shipping it. store_id remains available on the PLA
        # side (INTERNAL_PERF_RR_PLA), where the column genuinely exists.
        "drop_attributes": ["store_id"],
        "attribute_overrides": {
            "page_type": {"description": "Page type the Display ad request was served on. "
                                         "Filter page_type NOT IN ('', 'NA') to drop unattributed rows."},
        },
        "extra_attributes": {
            "hour": col("EXTRACT(HOUR FROM r.date_hour)", "INTEGER",
                        "Hour of day (0-23) the Display ad request was made, from date_hour. "
                        "Group by this to find low-activity hours dragging RR down."),
            "keyword": col("LOWER(TRIM(r.filter_keywords))", "STRING",
                           "Keyword the Display ad request carried (filter_keywords), lowercased "
                           "and trimmed. Filter keyword NOT IN ('') to drop requests with no keyword."),
        },
        "metrics": ["requests", "responses", "response_rate"],
        "query": """
            SELECT __ATTRIBUTES__, __METRICS__
            FROM `prj-onlinesales-prod-01.reporting.os_display_ads_filtered_level_performance_facts` AS r
            JOIN `prj-onlinesales-prod-01.reporting.marketplace_clients` AS mc
              ON r.marketplace_client_id = mc.marketplace_client_id
            WHERE mc.agency_id = '__AGENCY_ID__'
              AND r.date BETWEEN '__START_DATE_1__' AND '__END_DATE_1__'
              AND __FILTER__
            GROUP BY __ATTRIBUTES_GROUP_BY__;
        """,
    },
    # ------------------------------------------------------------------ M4
    {
        "path": "rr/INTERNAL_PERF_RR_PLA.json",
        "reportType": "INTERNAL_PERF_RR_PLA",
        "externalReportType": "RR_PLA_REPORT",
        "filterTags": ["report_group:rr", "report_group:category"],
        "absorbs": [
            "rr/INTERNAL_PERF_RR_BY_DIMENSION_PLA.json",
            "rr/INTERNAL_PERF_CATEGORY_RR.json",
            "rr/INTERNAL_PERF_STORE_LEVEL_RR.json",
        ],
        "description": """
            PLA ad request / non-zero-response volume and response rate for a marketplace over a
            period, grouped by any combination of the dimensions below: supply network, store,
            page type, page name, device, product category (L1-L5 or the concatenated
            category path), day of month, or hour of day. Replaces the three single-grain PLA RR
            reports. Group by category_l1/l2/l3 for category RR, by store_id + category + day +
            hour for the store-hour eligibility buckets, or by any other dimension mix. Pass a
            NOT IN ('', 'NA') filter on the grouping column to reproduce the null/blank guards
            the retired reports hardcoded.
        """,
        "attributes": [
            "network", "store_id", "page_type", "page_name", "device",
            "category_l1", "category_l2", "category_l3", "category_l4", "category_l5",
            "category", "day", "hour",
        ],
        "metrics": ["requests", "responses", "response_rate"],
        "query": """
            SELECT __ATTRIBUTES__, __METRICS__
            FROM `prj-onlinesales-prod-01.reporting.os_product_ads_filtered_level_report` AS r
            JOIN `prj-onlinesales-prod-01.reporting.marketplace_clients` AS mc
              ON r.marketplace_client_id = mc.marketplace_client_id
            WHERE mc.agency_id = '__AGENCY_ID__'
              AND r.date BETWEEN '__START_DATE_1__' AND '__END_DATE_1__'
              AND __FILTER__
            GROUP BY __ATTRIBUTES_GROUP_BY__;
        """,
    },
    # ------------------------------------------------------------------ M5
    {
        "path": "rr/INTERNAL_PERF_SEARCH_QUERY_REQUESTS_PLA.json",
        "reportType": "INTERNAL_PERF_SEARCH_QUERY_REQUESTS_PLA",
        "externalReportType": "SEARCH_QUERY_REQUESTS_PLA_REPORT",
        "filterTags": ["report_group:rr", "report_group:search_query", "report_group:keyword"],
        "absorbs": [
            "rr/INTERNAL_PERF_SEARCH_QUERY_RR_PLA.json",
            "rr/INTERNAL_PERF_SEARCH_QUERY_RR_BUCKETS.json",
            "keyword_delivery/INTERNAL_PERF_KW_REQUEST_VOLUME.json",
        ],
        "description": """
            Per-keyword PLA ad request / response volume and response rate on search pages for a
            marketplace over a period, from the timezone-aware search-query request report (dates
            are converted to the marketplace timezone). One row per keyword. Replaces the three
            keyword-request reports: use requests + responses + response_rate for keyword-level
            RR, requests + responses for the Pareto / zero-vs-partial-response buckets, and
            requests + days_with_requests to judge whether a keyword has enough demand to warrant
            a campaign. Filter keyword NOT IN ('') to drop requests that carried no search query;
            use a metrics filter on requests to apply a minimum-volume threshold.
        """,
        "attributes": ["keyword"],
        "metrics": ["requests", "responses", "response_rate", "days_with_requests"],
        "query": """
            SELECT __ATTRIBUTES__, __METRICS__
            FROM `prj-onlinesales-prod-01.reporting.os_product_ads_search_query_request_report` AS r
            JOIN `prj-onlinesales-prod-01.reporting.marketplace_clients` AS mc
              ON r.marketplace_client_id = mc.marketplace_client_id
            WHERE mc.agency_id = '__AGENCY_ID__'
              AND DATE(TIMESTAMP(r.date, 'UTC'), '__SP_TIMEZONE__') BETWEEN '__START_DATE_1__' AND '__END_DATE_1__'
              AND __FILTER__
            GROUP BY __ATTRIBUTES_GROUP_BY__;
        """,
    },
    # ------------------------------------------------------------------ M7
    {
        "path": "shared/INTERNAL_PERF_PAGE_PERFORMANCE_PLA.json",
        "reportType": "INTERNAL_PERF_PAGE_PERFORMANCE_PLA",
        "externalReportType": "PAGE_PERFORMANCE_PLA_REPORT",
        "filterTags": ["report_group:page_performance", "report_group:rr", "report_group:bu"],
        "absorbs": [
            "shared/INTERNAL_PERF_PAGE_LEVEL.json",
            "rr/INTERNAL_PERF_RR_BY_PAGE_PLA.json",
            "bu/INTERNAL_PERF_BU_REQUESTS_PLA.json",
        ],
        "description": """
            PLA page-level funnel for a marketplace over a period: requests, non-zero responses,
            response rate, impressions, clicks and marketplace-currency spend. Group by page_type
            for the page-type breakdown (page-level performance and page RR) or by date for the
            daily request/response trend used in budget-utilisation debugging. Rows with a null,
            blank or 'NA' page_type are excluded, matching all three retired reports.
        """,
        "attributes": ["page_type", "date"],
        "extra_attributes": {
            "date": col("pf.date", "DATE",
                        "Calendar date of the PLA page-level facts row. Group by this for the "
                        "daily request / response trend."),
        },
        "metrics": ["requests", "responses", "response_rate", "impressions", "clicks", "spend"],
        "extra_metrics": {
            "response_rate": rate_metric(
                "pf", "non_zero_responses", "requests",
                "Non-zero responses as a percentage of requests for this grouping."),
        },
        "query": """
            SELECT __ATTRIBUTES__, __METRICS__
            FROM `prj-onlinesales-prod-01.reporting.os_product_ads_page_name_performance_facts` AS pf
            JOIN `prj-onlinesales-prod-01.reporting.marketplace_clients` AS mc
              ON pf.marketplace_client_id = mc.marketplace_client_id
            LEFT JOIN `prj-onlinesales-prod-01.reporting.static_currency_conversion` AS scc
              ON scc.from_currency = 'USD' AND scc.to_currency = mc.currency
            WHERE mc.agency_id = '__AGENCY_ID__'
              AND pf.date BETWEEN '__START_DATE_1__' AND '__END_DATE_1__'
              AND pf.page_type IS NOT NULL AND pf.page_type NOT IN ('', 'NA')
              AND __FILTER__
            GROUP BY __ATTRIBUTES_GROUP_BY__;
        """,
    },
    # ------------------------------------------------------------------ M8
    {
        "path": "bu/INTERNAL_PERF_DISPLAY_AD_UNIT.json",
        "reportType": "INTERNAL_PERF_DISPLAY_AD_UNIT",
        "externalReportType": "DISPLAY_AD_UNIT_PERFORMANCE_REPORT",
        "filterTags": ["report_group:bu", "report_group:rr"],
        "absorbs": [
            "bu/INTERNAL_PERF_DISPLAY_AD_UNIT.json",
            "rr/INTERNAL_PERF_RR_BY_PAGE_DISPLAY.json",
            "bu/INTERNAL_PERF_BU_REQUESTS_DISPLAY.json",
        ],
        "description": """
            Display ad-unit funnel for a marketplace over a period: requests, non-zero responses,
            response rate, impressions, clicks, marketplace-currency spend and revenue, and the
            program funnel events (view-product, add-to-cart, conversions). Group by
            ad_unit_name and/or page_type for the ad-unit and page-type breakdowns, or by date
            for the daily request / response trend used in budget-utilisation debugging. Pass a
            page_type NOT IN ('', 'NA') filter to reproduce the guard the retired page-type and
            daily-requests reports hardcoded.
        """,
        "attributes": ["ad_unit_name", "page_type", "date"],
        "extra_attributes": {
            "date": col("auf.date", "DATE",
                        "Calendar date of the Display ad-unit facts row. Group by this for the "
                        "daily request / response trend."),
        },
        "metrics": [
            "requests", "responses", "response_rate", "impressions", "clicks",
            "spend", "revenue", "view_product", "add_to_cart", "conversions",
        ],
        "extra_metrics": {
            "response_rate": rate_metric(
                "auf", "non_zero_responses", "requests",
                "Non-zero responses as a percentage of requests for this grouping."),
        },
        "query": """
            SELECT __ATTRIBUTES__, __METRICS__
            FROM `prj-onlinesales-prod-01.reporting.os_display_ads_ad_unit_facts` AS auf
            INNER JOIN `prj-onlinesales-prod-01.reporting.marketplace_clients` AS mc
              ON auf.marketplace_client_id = mc.marketplace_client_id
            LEFT JOIN `prj-onlinesales-prod-01.reporting.static_currency_conversion` AS scc
              ON scc.from_currency = 'USD' AND scc.to_currency = mc.currency
            WHERE mc.agency_id = '__AGENCY_ID__'
              AND auf.date BETWEEN '__START_DATE_1__' AND '__END_DATE_1__'
              AND __FILTER__
            GROUP BY __ATTRIBUTES_GROUP_BY__;
        """,
    },
]

if __name__ == "__main__":
    print("Wave 1 — RR / request-response families")
    run(SPECS)
