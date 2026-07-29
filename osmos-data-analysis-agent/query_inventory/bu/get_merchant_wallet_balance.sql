-- =====================================================================
-- id:                       bu.get_merchant_wallet_balance
-- source:                   tools/bu_analysis_tools.py:900  (fn get_merchant_wallet_balance)
-- agent:                    bu
-- description:              Per-merchant remaining wallet balance (remaining_budget_amount_usd -> marketplace currency) for the marketplace. Point-in-time; no date range.
-- proposed_kam_report_type: TBD
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {agency_id}   str    -> __AGENCY_ID__
--   {top_n}       int    -> __TOP_N__
--   {seller_filter} frag -> __SELLER_IDS__   (optional; see injected_fragments)
--   {client_filter} frag -> __CLIENT_IDS__   (optional; see injected_fragments)
-- injected_fragments:                                  (SQL spliced in by a helper)
--   {seller_filter}  <- seller_ids set -> "AND c.seller_id IN ('id', ...)"  else ""
--   {client_filter}  <- client_ids set -> "AND c.client_id IN ('id', ...)"  else ""
-- tables:
--   reporting.clients
--   reporting.marketplace_clients
--   reporting.static_currency_conversion
-- region_specific:          false
-- timezone_aware:           false
-- comparison_mode:          single call
-- python_derived_metrics:   (computed in app layer AFTER KAM returns raw aggregates)
--   remaining_balance             = round(fillna(remaining_balance, 0), 2)
--   merchants_with_zero_balance   = rows where remaining_balance == 0
--   total_remaining_balance       = SUM(remaining_balance)
--   total_merchant_count          = len(rows);  zero_balance_count = len(zero-balance rows)
-- =====================================================================

SELECT
    c.client_id AS os_client_id,
    c.seller_id AS merchant_id,
    c.alias AS merchant_name,
    COALESCE(
        CASE
            WHEN c.remaining_budget_amount_usd >= 0.01
                THEN (c.remaining_budget_amount_usd * scc.conversion_factor)
            ELSE 0
        END,
        0) AS remaining_balance
FROM `prj-onlinesales-prod-01.reporting.clients` AS c
JOIN `prj-onlinesales-prod-01.reporting.marketplace_clients` AS mc
    ON c.agency_id = mc.agency_id
JOIN `prj-onlinesales-prod-01.reporting.static_currency_conversion` AS scc
    ON scc.to_currency = mc.currency
WHERE c.agency_id = '{agency_id}'
    AND scc.from_currency = 'USD'
    AND c.seller_id IS NOT NULL
    AND c.seller_id != ''
    AND mc.marketplace_client_id != c.client_id
    {seller_filter}
    {client_filter}
ORDER BY remaining_balance DESC
LIMIT {top_n}
