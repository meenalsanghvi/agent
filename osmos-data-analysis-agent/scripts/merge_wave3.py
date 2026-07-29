"""Wave 3 — merge the keyword / search-query / campaign / audit families.

M9  KEYWORD_PERFORMANCE        3 -> 1   os_ads_keyword_performance_report
M10 SEARCH_QUERY_PERFORMANCE   2 -> 1   os_ads_search_query_performance_report (SP-timezone pair)
M11 CAMPAIGN_PERFORMANCE       2 -> 1   campaign_performance_facts
M12 AUDIT_EVENTS               3 -> 1   audit.audit_logs_v2
M13 CAMPAIGN_KEYWORDS          2 -> 1   os_ads_db_campaign_level_keywords
M14 CAMPAIGN_NETWORKS          2 -> 1   os_ads_db_campaign_targeting_mapping

Two notes on filters, both verified against
kamService/src/servicehelpers/fetchReportDataServiceHelper.js:

  * createFilterClauses wraps the LHS in lower() for every IN / LIKE / string
    comparison unless the column sets applyCaseInsensitiveFilter. lower() over an
    INT64 is a BigQuery type error, so every numeric attribute a caller filters on
    (action_type_id, is_negative) sets that flag.
  * There is no IS NULL / IS NOT NULL operator, so discriminators that used to be
    hardcoded in the WHERE clause are promoted to attributes and filtered with = / IN.
"""

from merge_lib import col, run

NUMERIC = {"applyCaseInsensitiveFilter": True}

KEYWORD_QUERY = """
    SELECT __ATTRIBUTES__, __METRICS__
    FROM `prj-onlinesales-prod-01.reporting.os_ads_keyword_performance_report` AS k
    INNER JOIN `prj-onlinesales-prod-01.reporting.campaign_tagging_data` AS ctd
      ON ctd.account_id = k.account_id AND ctd.campaign_id = k.campaign_id
     AND ctd.client_id = k.client_id
    INNER JOIN `prj-onlinesales-prod-01.reporting.marketing_campaign_dimensions` AS mcd
      ON ctd.client_id = mcd.client_id AND ctd.marketing_campaign_id = mcd.marketing_campaign_id
    LEFT JOIN `prj-onlinesales-prod-01.reporting.marketing_campaign_group_dimensions` AS mcgd
      ON ctd.client_id = mcgd.client_id
     AND ctd.marketing_campaign_group_id = mcgd.marketing_campaign_group_id
    INNER JOIN `prj-onlinesales-prod-01.reporting.marketplace_clients` AS mc
      ON mc.marketplace_client_id = k.marketplace_client_id
    LEFT JOIN `prj-onlinesales-prod-01.reporting.clients` AS cl
      ON cl.client_id = k.client_id
    INNER JOIN `prj-onlinesales-prod-01.reporting.static_currency_conversion` AS scc
      ON scc.from_currency = k.currency AND scc.to_currency = mc.currency
    WHERE mc.agency_id = '__AGENCY_ID__'
      AND k.date BETWEEN '__START_DATE_1__' AND '__END_DATE_1__'
      AND (mcd.campaign_origin != 'PACKAGE_BASED' OR mcd.campaign_origin IS NULL)
      AND __FILTER__
    GROUP BY __ATTRIBUTES_GROUP_BY__;
"""

SEARCH_QUERY_QUERY = """
    SELECT __ATTRIBUTES__, __METRICS__
    FROM `prj-onlinesales-prod-01.reporting.os_ads_search_query_performance_report` AS p
    LEFT JOIN `prj-onlinesales-prod-01.reporting.clients` AS cl
      ON cl.client_id = p.client_id
    JOIN `prj-onlinesales-prod-01.reporting.marketplace_clients` AS mc
      ON p.marketplace_client_id = mc.marketplace_client_id
    WHERE mc.agency_id = '__AGENCY_ID__'
      AND DATE(TIMESTAMP(p.date, 'UTC'), '__SP_TIMEZONE__') BETWEEN '__START_DATE_1__' AND '__END_DATE_1__'
      AND __FILTER__
    GROUP BY __ATTRIBUTES_GROUP_BY__;
"""

CAMPAIGN_PERF_QUERY = """
    SELECT __ATTRIBUTES__, __METRICS__
    FROM `prj-onlinesales-prod-01.reporting.campaign_performance_facts` AS cpf
    JOIN `prj-onlinesales-prod-01.reporting.campaign_tagging_data` AS ctd
      ON cpf.campaign_id = ctd.campaign_id AND cpf.client_id = ctd.client_id
    JOIN `prj-onlinesales-prod-01.reporting.marketing_campaign_dimensions` AS mcd
      ON ctd.marketing_campaign_id = mcd.marketing_campaign_id AND ctd.client_id = mcd.client_id
    JOIN `prj-onlinesales-prod-01.reporting.marketing_campaign_group_dimensions` AS mcgd
      ON mcd.marketing_campaign_group_id = mcgd.marketing_campaign_group_id
     AND mcd.client_id = mcgd.client_id
     AND mcgd.marketing_campaign_group_id = ctd.marketing_campaign_group_id
     AND mcgd.client_id = ctd.client_id
    JOIN `prj-onlinesales-prod-01.reporting.monetize_merchant_dimensions` AS mmd
      ON mcgd.client_id = mmd.client_id AND mmd.agency_id = '__AGENCY_ID__'
    JOIN `prj-onlinesales-prod-01.reporting.marketplace_clients` AS mc
      ON mc.agency_id = mmd.agency_id AND mc.marketplace_type = 'monetize'
    JOIN `prj-onlinesales-prod-01.reporting.static_currency_conversion` AS scc
      ON scc.from_currency = cpf.currency AND scc.to_currency = mc.currency
    WHERE cpf.date BETWEEN '__START_DATE_1__' AND '__END_DATE_1__'
      AND (mcgd.campaign_origin != 'PACKAGE_BASED' OR mcgd.campaign_origin IS NULL)
      AND mmd.merchant_id NOT LIKE 'NULL'
      AND mc.agency_id = '__AGENCY_ID__'
      AND __FILTER__
    GROUP BY __ATTRIBUTES_GROUP_BY__;
"""

AUDIT_QUERY = """
    SELECT __ATTRIBUTES__, __METRICS__
    FROM `prj-onlinesales-prod-01.audit.audit_logs_v2` AS al
    WHERE al.agency_id = '__AGENCY_ID__'
      AND al.timestamp >= TIMESTAMP('__START_DATE_1__', '__SP_TIMEZONE__')
      AND al.timestamp < TIMESTAMP(DATE_ADD('__END_DATE_1__', INTERVAL 1 DAY), '__SP_TIMEZONE__')
      AND __FILTER__;
"""

CAMPAIGN_KEYWORDS_QUERY = """
    SELECT __ATTRIBUTES__, __METRICS__
    FROM `prj-onlinesales-prod-01.reporting.os_ads_db_campaign_level_keywords` AS k
    JOIN `prj-onlinesales-prod-01.reporting.marketplace_clients` AS mc
      ON SAFE_CAST(k.marketplace_client_id AS STRING) = mc.marketplace_client_id
    WHERE mc.agency_id = '__AGENCY_ID__'
      AND k.is_deleted = 0
      AND __FILTER__
    GROUP BY __ATTRIBUTES_GROUP_BY__;
"""

CAMPAIGN_NETWORKS_QUERY = """
    SELECT __ATTRIBUTES__, __METRICS__
    FROM `prj-onlinesales-prod-01.reporting.os_ads_db_campaign_targeting_mapping` AS ctm
    LEFT JOIN `prj-onlinesales-prod-01.reporting.campaign_tagging_data` AS ctd
      ON SAFE_CAST(ctd.campaign_id AS INT64) = ctm.campaign_id
     AND SAFE_CAST(ctd.client_id AS INT64) = ctm.client_id
    WHERE ctm.target_type = 'NETWORK'
      AND ctm.is_deleted = 0
      AND __FILTER__
    GROUP BY __ATTRIBUTES_GROUP_BY__;
"""


SPECS = [
    # ------------------------------------------------------------------ M9
    {
        "path": "keyword_delivery/INTERNAL_PERF_KEYWORD_PERFORMANCE.json",
        "reportType": "INTERNAL_PERF_KEYWORD_PERFORMANCE",
        # INTERNAL_ prefix: the unprefixed name is owned by a live BEATS report.
        "externalReportType": "INTERNAL_KEYWORD_PERFORMANCE_REPORT",
        "filterTags": [
            "report_group:keyword", "report_group:merchant_breakdown", "report_group:campaign",
        ],
        "absorbs": [
            "keyword_delivery/INTERNAL_PERF_KW_COMPETITION.json",
            "keyword_delivery/INTERNAL_PERF_KW_PERF_IN_CAMPAIGNS.json",
            "shared/INTERNAL_PERF_MERCHANT_KEYWORD.json",
        ],
        "description": """
            Targeted-keyword performance for a marketplace over a period: spend, impressions,
            clicks and attributed sales (marketplace currency), grouped by any mix of keyword,
            match type, campaign, campaign group and merchant. This is the single keyword-
            performance report for all three call sites. Filter keyword only to see every
            campaign competing on that keyword across the marketplace (campaign competition);
            filter os_client_id + campaign_id to see a keyword's performance inside specific
            campaigns; filter os_client_id and add campaign_type = 'performance' plus
            campaign_subtype IN ('os_ads_search', 'smart_shopping') to get a merchant's keywords
            across its PLA performance campaigns -- that pair of filters replaces a WHERE clause
            the retired merchant-keyword report hardcoded. Package-based campaigns are always
            excluded. campaign_id is the lowercased marketing_campaign_id.
        """,
        "attributes": [
            "keyword", "keyword_match_type", "campaign_id", "campaign_name",
            "campaign_group_id", "effective_status", "campaign_creation_date",
            "campaign_type", "campaign_subtype", "os_client_id", "seller_id",
        ],
        "extra_attributes": {
            "campaign_type": col("LOWER(mcgd.campaign_type)", "STRING",
                                 "Campaign-group type, lowercased. Filter campaign_type = "
                                 "'performance' to restrict to PLA performance campaigns."),
            "campaign_subtype": col("LOWER(mcgd.campaign_subtype)", "STRING",
                                    "Campaign-group subtype, lowercased. Filter campaign_subtype "
                                    "IN ('os_ads_search', 'smart_shopping') for PLA performance "
                                    "campaigns."),
        },
        "metrics": ["spend", "impressions", "clicks", "attributed_sales"],
        "query": KEYWORD_QUERY,
    },
    # ------------------------------------------------------------------ M10
    {
        "path": "shared/INTERNAL_PERF_SEARCH_QUERY_PERFORMANCE.json",
        "reportType": "INTERNAL_PERF_SEARCH_QUERY_PERFORMANCE",
        # The unprefixed name is owned by a live PULSE report, and
        # INTERNAL_SEARCH_QUERY_PERFORMANCE_REPORT is still held by the predecessor this
        # report retires (INTERNAL_PERF_SEARCH_QUERY_PERF) -- so take a third, free name
        # rather than create a duplicate catalogue entry during the changeover.
        "externalReportType": "INTERNAL_SEARCH_QUERY_PERF_REPORT",
        "filterTags": ["report_group:search_query", "report_group:ctr", "report_group:keyword"],
        "absorbs": [
            "shared/INTERNAL_PERF_SEARCH_QUERY_PERF.json",
            "ctr/INTERNAL_PERF_KEYWORD_SELLER.json",
        ],
        "description": """
            PLA search-query performance (what users actually typed) for a marketplace over a
            period, from the timezone-aware search-query performance report: impressions, clicks,
            spend, CTR, and the AUTO-vs-manual match-type split of both impressions and clicks.
            Group by search_query alone for the marketplace-wide view, or by search_query +
            seller_id / os_client_id for the per-keyword-per-seller breakdown. Merchant name comes
            from a LEFT JOIN on clients, so rows survive when the client record is missing. Spend
            is in the source currency of the search-query report.
        """,
        "attributes": ["search_query", "os_client_id", "seller_id", "merchant_name"],
        "metrics": [
            "impressions", "clicks", "spend", "ctr",
            "auto_impressions", "auto_clicks", "manual_impressions", "manual_clicks",
        ],
        "query": SEARCH_QUERY_QUERY,
    },
    # ------------------------------------------------------------------ M11
    {
        "path": "shared/INTERNAL_PERF_CAMPAIGN_PERFORMANCE.json",
        "reportType": "INTERNAL_PERF_CAMPAIGN_PERFORMANCE",
        # INTERNAL_ prefix: the unprefixed name is owned by a live BEATS report.
        "externalReportType": "INTERNAL_CAMPAIGN_PERFORMANCE_REPORT",
        "filterTags": ["report_group:campaign"],
        "absorbs": [
            "shared/INTERNAL_PERF_CAMPAIGN_PERF_AGG.json",
            "shared/INTERNAL_PERF_CAMPAIGN_PERF_DAILY.json",
        ],
        "externalRequiredFilters": ["campaign_id"],
        "description": """
            Campaign-group performance for a marketplace over a period: impressions, clicks,
            marketplace-currency spend, attributed orders and revenue. Omit `date` for the
            period aggregate, or group by `date` for the day-by-day series. Group by
            campaign_group_id / campaign_id and any of the campaign, merchant and budget
            attributes below. The retired daily report hardcoded
            campaign_type IN ('PERFORMANCE', 'INVENTORY', 'OFFSITE') -- pass that as a
            campaign_type IN filter to reproduce it. Package-based campaigns and null-merchant
            rows are always excluded. Scope with a campaign_id filter for campaign-level work.
        """,
        "attributes": [
            "date", "campaign_id", "campaign_group_id", "campaign_group_name",
            "campaign_group_type", "campaign_group_subtype", "campaign_group_status",
            "campaign_type", "campaign_subtype", "daily_budget",
            "merchant_id", "merchant_name", "os_client_id",
        ],
        "metrics": ["impressions", "clicks", "spend", "orders", "revenue"],
        "query": CAMPAIGN_PERF_QUERY,
    },
    # ------------------------------------------------------------------ M12
    {
        "path": "shared/INTERNAL_PERF_AUDIT_EVENTS.json",
        "reportType": "INTERNAL_PERF_AUDIT_EVENTS",
        "externalReportType": "AUDIT_EVENTS_REPORT",
        "filterTags": ["report_group:campaign", "report_group:budget_pacing"],
        "absorbs": [
            "shared/INTERNAL_PERF_PRODUCT_SELECTION_CHANGES.json",
            "shared/INTERNAL_PERF_CAMPAIGN_STATUS_CHANGES.json",
            "budget_pacing/INTERNAL_PERF_BUDGET_CHANGES.json",
        ],
        "externalRequiredFilters": ["action_type_id"],
        "description": """
            Campaign audit-log events for a marketplace over a period, from audit_logs_v2, one
            row per event with timestamps in the marketplace timezone. ALWAYS filter
            action_type_id -- it selects which kind of event you get, and which attributes are
            populated: 17 = daily-budget change (old_budget, new_budget, currency, changed_by),
            16 = campaign status change (old_status, new_status), 50/51 = product added /
            removed from a campaign (sku_id, action, changed_by, changed_by_type). Attributes
            outside the selected event type return null. change_timestamp and change_time are
            the same value under both of the names the retired reports used. This report has no
            GROUP BY -- it is a row-level passthrough.
        """,
        "attributes": [
            "action_type_id", "os_client_id", "campaign_id", "campaign_name",
            "campaign_type", "campaign_subtype", "change_timestamp", "change_time",
            "old_status", "new_status", "old_budget", "new_budget", "currency",
            "sku_id", "action", "changed_by", "changed_by_type",
        ],
        "extra_attributes": {
            "action_type_id": {
                "selector": "al.action_type_id", "type": "INTEGER", **NUMERIC,
                "description": "Audit action type. 17 = daily-budget change, 16 = campaign "
                               "status change, 50 = product added, 51 = product removed. "
                               "Required filter -- it selects the event kind.",
            },
        },
        # `action` only means anything for the product-selection event types; the retired
        # config's CASE would have labelled a status change as 'removed'.
        "attribute_overrides": {
            "action": col(
                "CASE WHEN al.action_type_id = 50 THEN 'added' "
                "WHEN al.action_type_id = 51 THEN 'removed' ELSE NULL END",
                "STRING",
                "For product-selection events (action_type_id 50/51): whether the SKU was "
                "added to or removed from the campaign. Null for other event types."),
        },
        "metrics": ["placeholder_metric"],
        "query": AUDIT_QUERY,
    },
    # ------------------------------------------------------------------ M13
    {
        "path": "shared/INTERNAL_PERF_CAMPAIGN_KEYWORDS.json",
        "reportType": "INTERNAL_PERF_CAMPAIGN_KEYWORDS",
        "externalReportType": "CAMPAIGN_KEYWORDS_REPORT",
        "filterTags": ["report_group:campaign", "report_group:keyword"],
        "absorbs": [
            "shared/INTERNAL_PERF_CAMPAIGN_KW_TARGETED.json",
            "shared/INTERNAL_PERF_CAMPAIGN_KW_NEGATIVE.json",
        ],
        "externalRequiredFilters": ["campaign_id"],
        "description": """
            Keywords configured on a SEARCH campaign, excluding deleted ones. Filter
            is_negative = 0 for the active TARGETED keywords the campaign bids on (bidding_value
            is the merchant-set bid) or is_negative = 1 for the NEGATIVE keywords it explicitly
            excludes -- that flag replaces the hardcoded WHERE clause each retired report
            carried. bidding_value is null for negative keywords. Scope with a campaign_id filter.
        """,
        "attributes": ["keyword", "is_negative", "bidding_value", "campaign_id", "os_client_id"],
        "extra_attributes": {
            "is_negative": {
                "selector": "k.is_negative", "type": "INTEGER", **NUMERIC,
                "description": "1 for a negative (excluded) keyword, 0 for a targeted keyword "
                               "the campaign bids on. Filter this to pick which list you want.",
            },
        },
        "metrics": ["placeholder_metric"],
        "query": CAMPAIGN_KEYWORDS_QUERY,
    },
    # ------------------------------------------------------------------ M14
    {
        "path": "shared/INTERNAL_PERF_CAMPAIGN_NETWORKS.json",
        "reportType": "INTERNAL_PERF_CAMPAIGN_NETWORKS",
        "externalReportType": "CAMPAIGN_NETWORKS_REPORT",
        "filterTags": ["report_group:campaign"],
        "absorbs": [
            "shared/INTERNAL_PERF_CAMPAIGN_NETWORKS_VIA_CTD.json",
            "shared/INTERNAL_PERF_CAMPAIGN_NETWORKS_BY_ID.json",
        ],
        "description": """
            Targeted NETWORK mappings for a campaign (target_type = 'NETWORK', not deleted),
            reachable by either key. Filter `campaign_id` when you hold the
            marketing_campaign_id -- it resolves through campaign_tagging_data. Filter
            `internal_campaign_id` when you hold the internal numeric campaign_id and want to
            query the targeting table directly. The join to campaign_tagging_data is a LEFT
            JOIN, so rows with no tagging record still return under internal_campaign_id.
            resolved_campaign_id is the same value as internal_campaign_id, kept under the name
            the retired via-CTD report used.
        """,
        "attributes": [
            "campaign_id", "internal_campaign_id", "resolved_campaign_id", "target_details",
        ],
        "extra_attributes": {
            "internal_campaign_id": {
                "selector": "SAFE_CAST(ctm.campaign_id AS STRING)", "type": "STRING",
                "description": "Internal numeric campaign_id on the targeting table, as a "
                               "string. Filter this when you do not hold a marketing_campaign_id.",
            },
        },
        "metrics": ["placeholder_metric"],
        "query": CAMPAIGN_NETWORKS_QUERY,
    },
]

if __name__ == "__main__":
    print("Wave 3 — keyword / search-query / campaign / audit families")
    run(SPECS)
