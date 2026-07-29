-- =====================================================================
-- id:                       shared.get_campaign_product_selection
-- source:                   tools/common_tools.py:492  (fn get_campaign_product_selection)
-- agent:                    shared
-- description:              Currently-active (in-stock) products selected in a specific campaign: merchant_id, product_id, name, availability, brand, category L1/L2/L3. Single call. Per-marketplace tables suffixed with marketplace_client_id.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {marketplace_client_id}  str -> __MARKETPLACE_CLIENT_ID__   (also used as TABLE SUFFIX)
-- injected_fragments:                                  (SQL spliced in by a helper/branch)
--   {campaign_filter}     <- "ctd.marketing_campaign_id = '{marketing_campaign_id}'"
--   {merchant_filter}     <- "AND opaps.merchant_id = '{merchant_id}'"   (empty if no merchant_id)
--   {availability_filter} <- "AND ompd.e_availability = 'in stock'"      (empty when in_stock_only=False)
-- tables:
--   reporting.os_product_ads_product_selection_{marketplace_client_id}   (per-marketplace, suffixed)
--   reporting.campaign_tagging_data
--   reporting.oltp_merchandise_product_dimensions_{marketplace_client_id} (per-marketplace, suffixed)
-- region_specific:          false   (NOTE: table names are per-marketplace, suffixed with marketplace_client_id, not reporting_{region})
-- timezone_aware:           false
-- comparison_mode:          single call
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   products               = all rows
--   category_l1_breakdown  = value_counts(category_l1)
--   category_hierarchy     = distinct sorted (l1, l2, l3)
--   summary.total_products / in_stock_count (availability=='in stock')
--   summary.unique_brands / unique_categories_l1 / _l2 / _l3 (nunique)
-- =====================================================================

    SELECT
        opaps.merchant_id,
        opaps.product_id,
        ompd.e_name AS product_name,
        ompd.e_availability AS availability,
        ompd.e_brand AS brand,
        ompd.category_l1,
        ompd.category_l2,
        ompd.category_l3
    FROM `prj-onlinesales-prod-01.reporting.os_product_ads_product_selection_{marketplace_client_id}` AS opaps
    INNER JOIN `prj-onlinesales-prod-01.reporting.campaign_tagging_data` AS ctd
        ON opaps.campaign_id = ctd.campaign_id
        AND opaps.account_id = ctd.account_id
    INNER JOIN `prj-onlinesales-prod-01.reporting.oltp_merchandise_product_dimensions_{marketplace_client_id}` AS ompd
        ON opaps.product_id = ompd.sku_id
        AND opaps.merchant_id = ompd.merchant_id
        AND opaps.client_id = ompd.client_id
    WHERE {campaign_filter}
        AND ompd.is_deleted = FALSE
        AND opaps.is_active = TRUE
        {merchant_filter}
        {availability_filter}
    LIMIT 1000
