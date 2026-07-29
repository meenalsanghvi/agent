"""Wave 2 — merge the cvcpf / SKU / funnel families.

M1  MERCHANT_PERFORMANCE   5 -> 1   client_vendor_channel_performance_facts (+ site funnel)
M2  SKU_PERFORMANCE        3 -> 1   os_product_ads_device_product_facts (+ site funnel)
M6  GMV_ATTRIBUTION        2 -> 1   absorbs PROGRAM_SPEND (strict 1-metric subset)
M15 CATEGORY_PERFORMANCE   2 -> 1   marketplace_category_level_performance_facts_v2

MERCHANT_BU and MERCHANT_RR were byte-identical; MERCHANT_CTR added only derived
metrics; MERCHANT_CPC and MERCHANT_ROAS shared the same two-CTE shape. The merged base
is the two-CTE form (program aggregates from cvcpf, site aggregates LEFT JOINed from
monetize_merchant_facts) so both the raw and the site-funnel callers are served. Same
story for the SKU family: SKU_ROAS and SKU_CPC were byte-identical and SKU_CTR was the
same query without the site join.
"""

from merge_lib import col, run

# Inner program CTE shared by MERCHANT_ROAS / MERCHANT_CPC, plus `impressions` which
# only MERCHANT_CPC selected -- the merged report needs both.
MERCHANT_QUERY = """
    SELECT __ATTRIBUTES__, __METRICS__
    FROM (
        SELECT mmd.client_id AS os_client_id,
               mmd.merchant_name AS merchant_name,
               mmd.merchant_id AS merchant_id,
               cvcpf.channel AS channel,
               SUM(cvcpf.cost * scc.conversion_factor) AS spend,
               SUM(cvcpf.clicks) AS clicks,
               SUM(cvcpf.impressions) AS impressions,
               SUM(cvcpf.program_per_click_timestamp_viewproduct) AS program_viewproducts,
               SUM(cvcpf.program_per_click_timestamp_add_to_cart) AS program_add2carts,
               SUM(cvcpf.program_per_click_timestamp_conversions) AS program_orders,
               SUM(cvcpf.program_per_click_timestamp_sales) AS program_gmv
        FROM `prj-onlinesales-prod-01.reporting.client_vendor_channel_performance_facts` AS cvcpf
        INNER JOIN `prj-onlinesales-prod-01.reporting.clients` AS clients
          ON clients.client_id = cvcpf.client_id AND clients.agency_id = '__AGENCY_ID__'
        INNER JOIN `prj-onlinesales-prod-01.reporting.marketplace_clients` AS mc
          ON mc.agency_id = clients.agency_id
         AND clients.client_id != mc.marketplace_client_id
         AND mc.agency_id = '__AGENCY_ID__'
        INNER JOIN `prj-onlinesales-prod-01.reporting.monetize_merchant_dimensions` AS mmd
          ON mmd.merchant_id = clients.seller_id AND mmd.agency_id = clients.agency_id
        LEFT JOIN `prj-onlinesales-prod-01.reporting.static_currency_conversion` AS scc
          ON scc.from_currency = cvcpf.currency AND scc.to_currency = mc.currency
        WHERE cvcpf.vendor = 'os_ads'
          AND cvcpf.date BETWEEN '__START_DATE_1__' AND '__END_DATE_1__'
        GROUP BY 1, 2, 3, 4
    ) AS base
    LEFT JOIN (
        SELECT mmf.merchant_id AS merchant_id,
               SUM(mmf.total_sok_viewproducts) AS site_viewproducts,
               SUM(mmf.total_sok_add2carts) AS site_add2carts,
               SUM(mmf.total_sok_salecompletes) AS site_orders,
               SUM(mmf.total_sok_sales_usd * scc.conversion_factor) AS site_gmv
        FROM `prj-onlinesales-prod-01.reporting.monetize_merchant_facts` AS mmf
        INNER JOIN `prj-onlinesales-prod-01.reporting.marketplace_clients` AS mc
          ON mmf.agency_id = mc.agency_id
         AND mmf.marketplace_client_id = mc.marketplace_client_id
         AND mc.agency_id = '__AGENCY_ID__'
        INNER JOIN `prj-onlinesales-prod-01.reporting.static_currency_conversion` AS scc
          ON scc.from_currency = 'USD' AND scc.to_currency = mc.currency
        WHERE mmf.agency_id = '__AGENCY_ID__'
          AND mmf.date >= '__START_DATE_1__' AND mmf.date <= '__END_DATE_1__'
        GROUP BY 1
    ) AS org ON base.merchant_id = org.merchant_id
    WHERE base.merchant_id IS NOT NULL AND __FILTER__
    GROUP BY __ATTRIBUTES_GROUP_BY__;
"""

SKU_QUERY = """
    SELECT __ATTRIBUTES__, __METRICS__
    FROM (
        SELECT merchant_merchandise_product_dimensions.sku_id AS product_id,
               os_product_ads_device_product_facts.client_id AS client_id,
               clients.seller_id AS seller_id,
               clients.seller_name AS seller_name,
               MAX(merchant_merchandise_product_dimensions.e_name) AS product,
               STRING_AGG(DISTINCT marketing_campaign_dimensions.alias, ', ') AS campaign_names,
               MAX(merchant_merchandise_product_dimensions.e_brand) AS brand,
               MAX(merchant_merchandise_product_dimensions.e_product_type) AS category,
               COALESCE(SUM(os_product_ads_device_product_facts.cost), 0) AS spend,
               COALESCE(SUM(os_product_ads_device_product_facts.impressions), 0) AS impressions,
               COALESCE(SUM(os_product_ads_device_product_facts.clicks), 0) AS clicks,
               COALESCE(SUM(os_product_ads_device_product_facts.program_per_click_timestamp_viewproduct), 0) AS program_viewproducts,
               COALESCE(SUM(os_product_ads_device_product_facts.program_per_click_timestamp_add_to_cart), 0) AS program_add2carts,
               COALESCE(SUM(os_product_ads_device_product_facts.program_per_click_timestamp_conversions), 0) AS program_orders,
               COALESCE(SUM(os_product_ads_device_product_facts.program_per_click_timestamp_sales), 0) AS program_gmv
        FROM `prj-onlinesales-prod-01.reporting.merchant_merchandise_product_dimensions` merchant_merchandise_product_dimensions
        JOIN `prj-onlinesales-prod-01.reporting.os_product_ads_device_product_facts` os_product_ads_device_product_facts
          ON os_product_ads_device_product_facts.client_id = merchant_merchandise_product_dimensions.client_id
         AND os_product_ads_device_product_facts.sku_id = merchant_merchandise_product_dimensions.sku_id
        LEFT JOIN `prj-onlinesales-prod-01.reporting.campaign_tagging_data` campaign_tagging_data
          ON campaign_tagging_data.account_id = os_product_ads_device_product_facts.account_id
         AND campaign_tagging_data.campaign_id = os_product_ads_device_product_facts.campaign_id
         AND campaign_tagging_data.client_id = os_product_ads_device_product_facts.client_id
        JOIN `prj-onlinesales-prod-01.reporting.marketing_campaign_dimensions` marketing_campaign_dimensions
          ON campaign_tagging_data.marketing_campaign_id = marketing_campaign_dimensions.marketing_campaign_id
         AND marketing_campaign_dimensions.client_id = os_product_ads_device_product_facts.client_id
         AND marketing_campaign_dimensions.campaign_origin != 'PACKAGE_BASED'
        JOIN `prj-onlinesales-prod-01.reporting.marketing_campaign_group_dimensions` marketing_campaign_group_dimensions
          ON campaign_tagging_data.client_id = marketing_campaign_group_dimensions.client_id
         AND campaign_tagging_data.marketing_campaign_group_id = marketing_campaign_group_dimensions.marketing_campaign_group_id
        JOIN `prj-onlinesales-prod-01.reporting.clients` clients
          ON clients.client_id = os_product_ads_device_product_facts.client_id
        WHERE clients.agency_id = '__AGENCY_ID__'
          AND os_product_ads_device_product_facts.date >= '__START_DATE_1__'
          AND os_product_ads_device_product_facts.date <= '__END_DATE_1__'
          AND LOWER(marketing_campaign_group_dimensions.campaign_type) IN ('performance')
          AND LOWER(marketing_campaign_group_dimensions.campaign_subtype) IN ('os_ads_search', 'smart_shopping')
        GROUP BY 1, 2, 3, 4
    ) prog
    LEFT JOIN (
        SELECT merchant_id, sku_id,
               SUM(sok_viewproducts) AS site_viewproducts,
               SUM(sok_add2carts) AS site_add2carts,
               SUM(sok_salecompletes) AS site_orders,
               SUM(sok_sales_usd) AS site_gmv
        FROM `prj-onlinesales-prod-01.reporting.os_merchandise_product_performance_facts`
        WHERE client_id = (SELECT marketplace_client_id
                           FROM `prj-onlinesales-prod-01.reporting.agencies`
                           WHERE agency_id = '__AGENCY_ID__')
          AND date >= '__START_DATE_1__' AND date <= '__END_DATE_1__'
        GROUP BY 1, 2
    ) org
      ON CAST(org.merchant_id AS STRING) = CAST(prog.seller_id AS STRING)
     AND CAST(org.sku_id AS STRING) = CAST(prog.product_id AS STRING)
    WHERE prog.product_id IS NOT NULL AND __FILTER__
    GROUP BY __ATTRIBUTES_GROUP_BY__;
"""

CVCPF_MARKETPLACE_QUERY = """
    SELECT __METRICS__
    FROM `prj-onlinesales-prod-01.reporting.client_vendor_channel_performance_facts` AS cvcpf
    INNER JOIN `prj-onlinesales-prod-01.reporting.clients` AS clients
      ON clients.client_id = cvcpf.client_id AND clients.agency_id = '__AGENCY_ID__'
    INNER JOIN `prj-onlinesales-prod-01.reporting.marketplace_clients` AS mc
      ON mc.agency_id = clients.agency_id AND clients.client_id != mc.marketplace_client_id
    INNER JOIN `prj-onlinesales-prod-01.reporting.static_currency_conversion` AS scc
      ON scc.from_currency = cvcpf.currency AND scc.to_currency = mc.currency
    WHERE cvcpf.vendor = 'os_ads'
      AND cvcpf.date BETWEEN '__START_DATE_1__' AND '__END_DATE_1__'
      AND __FILTER__;
"""

CATEGORY_QUERY = """
    SELECT __ATTRIBUTES__, __METRICS__
    FROM `prj-onlinesales-prod-01.reporting.marketplace_category_level_performance_facts_v2` AS f
    WHERE f.agency_id = '__AGENCY_ID__'
      AND f.date BETWEEN '__START_DATE_1__' AND '__END_DATE_1__'
      AND __FILTER__
    GROUP BY __ATTRIBUTES_GROUP_BY__;
"""


def base_ratio(num, den, scale, digits, description):
    return col(
        f"COALESCE(ROUND(SAFE_DIVIDE(SUM(base.{num}){scale}, NULLIF(SUM(base.{den}), 0)), {digits}), 0)",
        "FLOAT", description,
    )


SPECS = [
    # ------------------------------------------------------------------ M1
    {
        "path": "shared/INTERNAL_PERF_MERCHANT_PERFORMANCE.json",
        "reportType": "INTERNAL_PERF_MERCHANT_PERFORMANCE",
        "externalReportType": "MERCHANT_PERFORMANCE_REPORT",
        "filterTags": [
            "report_group:merchant_breakdown", "report_group:roas", "report_group:cpc",
            "report_group:ctr", "report_group:bu", "report_group:rr",
        ],
        "absorbs": [
            "roas/INTERNAL_PERF_MERCHANT_ROAS.json",
            "cpc/INTERNAL_PERF_MERCHANT_CPC.json",
            "ctr/INTERNAL_PERF_MERCHANT_CTR.json",
            "bu/INTERNAL_PERF_MERCHANT_BU.json",
            "rr/INTERNAL_PERF_MERCHANT_RR.json",
        ],
        "description": """
            Per-merchant PROGRAM (ad-attributed) and SITE (organic) funnel for a marketplace over
            a period, one row per merchant and channel. PROGRAM metrics come from per-click-
            timestamp attribution in client_vendor_channel_performance_facts; SITE metrics come
            from monetize_merchant_facts via a LEFT JOIN, so merchants with no organic rows still
            appear. Spend and revenue are converted to the marketplace currency. This is the
            single merchant-breakdown report for every metric SOP -- request only the metrics
            that SOP needs: spend/clicks/impressions for budget-utilisation and response-rate
            work, + ctr/cpc/cpm for CTR and CPC work, + the program/site funnel and roas for
            ROAS work. Filter channel to isolate PLA (os_product_ads) from Display
            (guaranteed_display_ads / auction_display_ads). Merchants whose merchant_id is null
            are excluded.
        """,
        "attributes": ["os_client_id", "merchant_name", "merchant_id", "channel"],
        "metrics": [
            "spend", "clicks", "impressions", "ctr", "cpc", "cpm",
            "program_viewproducts", "program_add2carts", "program_orders", "program_gmv", "roas",
            "site_viewproducts", "site_add2carts", "site_orders", "site_revenue",
        ],
        # MERCHANT_CTR defined these against the bare `cvcpf` alias, which the two-CTE
        # template does not bind -- recompute them from the `base` subquery.
        "metric_overrides": {
            "ctr": base_ratio("clicks", "impressions", " * 100.0", 2,
                              "Clicks as a percentage of impressions for this merchant."),
            "cpm": base_ratio("spend", "impressions", " * 1000", 4,
                              "Cost per thousand impressions, in the marketplace currency."),
        },
        "query": MERCHANT_QUERY,
    },
    # ------------------------------------------------------------------ M2
    {
        "path": "shared/INTERNAL_PERF_SKU_PERFORMANCE.json",
        "reportType": "INTERNAL_PERF_SKU_PERFORMANCE",
        "externalReportType": "SKU_PERFORMANCE_REPORT",
        "filterTags": [
            "report_group:sku", "report_group:roas", "report_group:cpc", "report_group:ctr",
        ],
        "absorbs": [
            "roas/INTERNAL_PERF_SKU_ROAS.json",
            "cpc/INTERNAL_PERF_SKU_CPC.json",
            "ctr/INTERNAL_PERF_SKU_CTR.json",
        ],
        "externalRequiredFilters": ["os_client_id"],
        "description": """
            SKU-level PROGRAM funnel for PLA performance campaigns (os_ads_search,
            smart_shopping) joined to the SITE/organic SKU funnel, one row per SKU, for a
            marketplace over a period. This is the single SKU drill-down report for the ROAS,
            CPC and CTR SOPs -- request only the metrics that SOP needs. Scope with an
            os_client_id filter: an unscoped fetch scans every SKU in the marketplace and is too
            heavy. Spend is in the source currency of the device-product facts table.
        """,
        "attributes": [
            "sku_id", "os_client_id", "merchant_id", "merchant_name",
            "product_name", "brand", "category", "campaign_names",
        ],
        "metrics": [
            "spend", "impressions", "clicks", "ctr", "cpc",
            "program_viewproducts", "program_add2carts", "program_orders", "program_gmv",
            "site_viewproducts", "site_add2carts", "site_orders", "site_gmv",
        ],
        "query": SKU_QUERY,
    },
    # ------------------------------------------------------------------ M6
    {
        "path": "roas/INTERNAL_PERF_GMV_ATTRIBUTION.json",
        "reportType": "INTERNAL_PERF_GMV_ATTRIBUTION",
        "externalReportType": "GMV_ATTRIBUTION_REPORT",
        "filterTags": ["report_group:roas", "report_group:bu"],
        "absorbs": [
            "roas/INTERNAL_PERF_GMV_ATTRIBUTION.json",
            "bu/INTERNAL_PERF_PROGRAM_SPEND.json",
        ],
        "description": """
            Marketplace-level PROGRAM (ad-attributed) vs SITE (organic) funnel for a single
            period: a one-row aggregate across every seller of the agency. PROGRAM metrics come
            from per-click-timestamp attribution in client_vendor_channel_performance_facts;
            SITE metrics are correlated subqueries over monetize_merchant_facts. Spend and
            revenue are converted to the marketplace currency. Request `spend` alone for the
            total program-spend check. NOTE: `channel` is a FILTER-ONLY attribute -- this
            template has no __ATTRIBUTES__ placeholder, so channel can be filtered (PLA =
            os_product_ads, Display = guaranteed_display_ads / auction_display_ads) but never
            grouped by. The report is single-period; fetch current and baseline separately.
        """,
        "attributes": ["channel"],
        "metrics": [
            "spend", "impressions", "clicks",
            "program_gmv", "program_orders", "program_viewproducts", "program_add2carts",
            "site_revenue", "site_orders", "site_viewproducts", "site_add2carts",
        ],
        "query": CVCPF_MARKETPLACE_QUERY,
    },
    # ------------------------------------------------------------------ M15
    {
        "path": "shared/INTERNAL_PERF_CATEGORY_PERFORMANCE.json",
        "reportType": "INTERNAL_PERF_CATEGORY_PERFORMANCE",
        "externalReportType": "CATEGORY_PERFORMANCE_REPORT",
        "filterTags": ["report_group:category", "report_group:cpc", "report_group:roas"],
        "absorbs": [
            "shared/INTERNAL_PERF_CATEGORY_LEVEL.json",
            "cpc/INTERNAL_PERF_MERCHANT_CATEGORY_CPC.json",
        ],
        "description": """
            PLA category-level (L1/L2/L3) PROGRAM and SITE aggregates for a marketplace over a
            period, optionally broken down by merchant. Group by category_l1/l2/l3 for the
            marketplace-wide category view, or add merchant_id for the merchant-vs-category
            comparison. Two category forms are exposed: category_l1/l2/l3 are display-normalised
            (null / blank / 'na' collapse to 'Unknown' at L1 and '-' below it), while
            category_l1_raw/l2_raw/l3_raw are the untouched column values -- use the raw form
            when joining back to another category-keyed result. Spend and revenue are in the
            source currency of the category facts table. program_revenue and program_gmv are the
            same aggregate under both of the names the retired reports used.
        """,
        "attributes": [
            "category_l1", "category_l2", "category_l3",
            "category_l1_raw", "category_l2_raw", "category_l3_raw",
            "merchant_id",
        ],
        "extra_attributes": {
            "category_l1_raw": col("f.category_l1", "STRING",
                                   "Level-1 product category exactly as stored, with no null/blank "
                                   "normalisation applied."),
            "category_l2_raw": col("f.category_l2", "STRING",
                                   "Level-2 product category exactly as stored, with no null/blank "
                                   "normalisation applied."),
            "category_l3_raw": col("f.category_l3", "STRING",
                                   "Level-3 product category exactly as stored, with no null/blank "
                                   "normalisation applied."),
        },
        "metrics": [
            "spend", "impressions", "clicks",
            "program_orders", "program_revenue", "program_gmv",
            "program_viewproducts", "program_add_to_carts",
            "site_viewproducts", "site_add_to_carts", "site_orders", "site_revenue",
            "merchant_count",
        ],
        "query": CATEGORY_QUERY,
    },
]

if __name__ == "__main__":
    print("Wave 2 — cvcpf / SKU / funnel families")
    run(SPECS)
