-- =============================================================================
-- Untagged-category audit — cross-client
-- =============================================================================
-- Finds surfaces where ad requests arrive WITHOUT a usable category_l1 and
-- receive essentially zero ads, while tagged requests on the same page fill
-- normally. That contrast is the evidence: it rules out "thin advertiser
-- supply" and points at the request itself being unmatchable.
--
-- Source mirrors RR_PLA_REPORT (kam_report_configs/rr/INTERNAL_PERF_RR_PLA.json):
--   facts : reporting.os_product_ads_filtered_level_report
--   join  : reporting.clients ON marketplace_client_id = client_id
--   RR    : non_zero_responses / requests
--
-- ⚠️ IMPORTANT CAVEAT — read before drawing conclusions
-- A CATEGORY-page request is servable with EITHER a category OR an mcid.
-- A PRODUCT-page request carries a SKU in the input.
-- Neither `mcid` nor the input SKU exists in this table, so a blank
-- category_l1 here does NOT by itself prove the request was malformed.
-- `requested_products` is NOT the input SKU — it is a slot count, exactly
-- 10x `requests` on every row.
-- FirstCry is the control: 741,369 untagged category requests that fill at
-- 28.07%, ABOVE its tagged rate. Untagged is therefore not inherently
-- unfillable. Confirm against the raw request log before concluding.
-- =============================================================================


-- -----------------------------------------------------------------------------
-- QUERY 1 — Category-page audit, all marketplaces  (the main one)
-- -----------------------------------------------------------------------------
WITH ag AS (
  SELECT agency_id,
         ANY_VALUE(name)           AS agency_name,
         ANY_VALUE(category_level) AS category_level
  FROM `prj-onlinesales-prod-01.reporting.agencies`
  GROUP BY agency_id
),
base AS (
  SELECT
    mc.agency_id,
    CASE WHEN COALESCE(TRIM(r.category_l1), '') = '' THEN 'UNTAGGED' ELSE 'TAGGED' END AS st,
    SUM(r.requests)           AS req,
    SUM(r.non_zero_responses) AS resp
  FROM `prj-onlinesales-prod-01.reporting.os_product_ads_filtered_level_report` AS r
  JOIN `prj-onlinesales-prod-01.reporting.clients` AS mc
    ON r.marketplace_client_id = mc.client_id
  WHERE r.date BETWEEN '2026-07-27' AND '2026-08-03'
    AND UPPER(r.page_type) = 'CATEGORY'
  GROUP BY 1, 2
),
p AS (
  SELECT agency_id,
    SUM(IF(st = 'UNTAGGED', req,  0)) AS untag_req,
    SUM(IF(st = 'UNTAGGED', resp, 0)) AS untag_resp,
    SUM(IF(st = 'TAGGED',   req,  0)) AS tag_req,
    SUM(IF(st = 'TAGGED',   resp, 0)) AS tag_resp,
    SUM(req)  AS total_req,
    SUM(resp) AS total_resp
  FROM base
  GROUP BY 1
)
SELECT
  COALESCE(ag.agency_name, '(unknown)')                                AS marketplace,
  p.agency_id,
  ag.category_level,
  CAST(p.total_req  AS INT64)                                          AS cat_requests,
  ROUND(SAFE_DIVIDE(p.total_resp  * 100, NULLIF(p.total_req, 0)),  2)  AS blended_rr,
  CAST(p.untag_req  AS INT64)                                          AS untagged_req,
  ROUND(SAFE_DIVIDE(p.untag_req   * 100, NULLIF(p.total_req, 0)),  2)  AS pct_untagged,
  ROUND(SAFE_DIVIDE(p.untag_resp  * 100, NULLIF(p.untag_req, 0)),  3)  AS untagged_rr,
  ROUND(SAFE_DIVIDE(p.tag_resp    * 100, NULLIF(p.tag_req, 0)),    2)  AS tagged_rr,
  -- defect = meaningful untagged volume, ~zero fill, WHILE tagged fills fine
  CASE WHEN p.untag_req >= 10000
        AND SAFE_DIVIDE(p.untag_resp, NULLIF(p.untag_req, 0)) < 0.01
        AND p.tag_req > 0
        AND SAFE_DIVIDE(p.tag_resp,   NULLIF(p.tag_req, 0))   > 0.05
       THEN 'DEFECT' ELSE '' END                                       AS flag
FROM p
LEFT JOIN ag USING (agency_id)
WHERE p.total_req > 1000
ORDER BY untagged_req DESC;


-- -----------------------------------------------------------------------------
-- QUERY 2 — Same audit across ALL page types (not just CATEGORY)
-- AJIO's largest exposure is on PRODUCT, so don't scope to category only.
-- -----------------------------------------------------------------------------
WITH ag AS (
  SELECT agency_id, ANY_VALUE(name) AS agency_name
  FROM `prj-onlinesales-prod-01.reporting.agencies` GROUP BY agency_id
),
base AS (
  SELECT mc.agency_id, r.page_type,
    CASE WHEN COALESCE(TRIM(r.category_l1), '') = '' THEN 'UNTAGGED' ELSE 'TAGGED' END AS st,
    SUM(r.requests) AS req, SUM(r.non_zero_responses) AS resp
  FROM `prj-onlinesales-prod-01.reporting.os_product_ads_filtered_level_report` AS r
  JOIN `prj-onlinesales-prod-01.reporting.clients` AS mc
    ON r.marketplace_client_id = mc.client_id
  WHERE r.date BETWEEN '2026-07-27' AND '2026-08-03'
  GROUP BY 1, 2, 3
),
p AS (
  SELECT agency_id, page_type,
    SUM(IF(st='UNTAGGED', req, 0))  AS untag_req,
    SUM(IF(st='UNTAGGED', resp, 0)) AS untag_resp,
    SUM(IF(st='TAGGED',   req, 0))  AS tag_req,
    SUM(IF(st='TAGGED',   resp, 0)) AS tag_resp,
    SUM(req) AS total_req
  FROM base GROUP BY 1, 2
)
SELECT
  COALESCE(ag.agency_name, '(unknown)') AS marketplace,
  p.agency_id, p.page_type,
  CAST(p.total_req AS INT64)                                        AS total_requests,
  CAST(p.untag_req AS INT64)                                        AS untagged_requests,
  ROUND(SAFE_DIVIDE(p.untag_req  * 100, NULLIF(p.total_req, 0)), 2) AS pct_untagged,
  ROUND(SAFE_DIVIDE(p.untag_resp * 100, NULLIF(p.untag_req, 0)), 4) AS untagged_rr,
  ROUND(SAFE_DIVIDE(p.tag_resp   * 100, NULLIF(p.tag_req, 0)),   2) AS tagged_rr
FROM p
LEFT JOIN ag USING (agency_id)
WHERE p.untag_req >= 50000
  AND SAFE_DIVIDE(p.untag_resp, NULLIF(p.untag_req, 0)) < 0.01
ORDER BY untagged_requests DESC;


-- -----------------------------------------------------------------------------
-- QUERY 3 — Single-marketplace drill (swap the agency_id)
-- Shows every category_l1 value on the category page, blanks first.
-- -----------------------------------------------------------------------------
SELECT
  COALESCE(NULLIF(TRIM(r.category_l1), ''), '(BLANK)')                AS category_l1,
  CAST(SUM(r.requests) AS INT64)                                      AS requests,
  CAST(SUM(r.non_zero_responses) AS INT64)                            AS responses,
  ROUND(SAFE_DIVIDE(SUM(r.non_zero_responses) * 100,
                    NULLIF(SUM(r.requests), 0)), 4)                   AS response_rate_pct,
  ROUND(SUM(r.requests) * 100.0 / SUM(SUM(r.requests)) OVER (), 2)    AS pct_of_requests
FROM `prj-onlinesales-prod-01.reporting.os_product_ads_filtered_level_report` AS r
JOIN `prj-onlinesales-prod-01.reporting.clients` AS mc
  ON r.marketplace_client_id = mc.client_id
WHERE mc.agency_id = '434'                       -- 434 Apollo | 444 bigbasket | 392 AJIO | 366 FirstCry (control)
  AND r.date BETWEEN '2026-07-27' AND '2026-08-03'
  AND UPPER(r.page_type) = 'CATEGORY'
GROUP BY category_l1
ORDER BY requests DESC;


-- -----------------------------------------------------------------------------
-- QUERY 4 — Contamination check: values in category_l1 that aren't categories
-- Found: product URLs (takealot), merchandising labels (AJIO), test data (1mg)
-- -----------------------------------------------------------------------------
SELECT
  COALESCE(ag.agency_name, '(unknown)') AS marketplace,
  mc.agency_id, r.page_type, r.category_l1,
  CAST(SUM(r.requests) AS INT64)           AS requests,
  CAST(SUM(r.non_zero_responses) AS INT64) AS responses
FROM `prj-onlinesales-prod-01.reporting.os_product_ads_filtered_level_report` AS r
JOIN `prj-onlinesales-prod-01.reporting.clients` AS mc
  ON r.marketplace_client_id = mc.client_id
LEFT JOIN (SELECT agency_id, ANY_VALUE(name) AS agency_name
           FROM `prj-onlinesales-prod-01.reporting.agencies` GROUP BY agency_id) AS ag
  ON ag.agency_id = mc.agency_id
WHERE r.date BETWEEN '2026-07-27' AND '2026-08-03'
  AND (   LOWER(r.category_l1) LIKE 'http%'       -- product URLs
       OR LOWER(r.category_l1) LIKE '%test%'      -- test data in production
       OR LOWER(r.category_l1) LIKE '% on sale%'  -- merchandising labels
       OR LENGTH(r.category_l1) > 40 )            -- suspiciously long
GROUP BY 1, 2, 3, 4
ORDER BY requests DESC;


-- -----------------------------------------------------------------------------
-- QUERY 5 — ⚠️ UNVERIFIED. Run this once the raw request table is known.
-- This is the query that actually settles cause. Fill in <dataset>.<table>
-- and the real column names for the input mcid / input sku.
-- -----------------------------------------------------------------------------
-- SELECT
--   page_type,
--   IF(COALESCE(TRIM(category_l1),'')='', 'no_category', 'has_category') AS cat_state,
--   IF(COALESCE(TRIM(mcid),      '')='', 'no_mcid',     'has_mcid')      AS mcid_state,
--   IF(COALESCE(TRIM(sku_id),    '')='', 'no_sku',      'has_sku')       AS sku_state,
--   COUNT(*)                                          AS requests,
--   COUNTIF(responses > 0)                            AS filled,
--   ROUND(COUNTIF(responses > 0) * 100 / COUNT(*), 3) AS fill_pct
-- FROM `prj-onlinesales-prod-01.<dataset>.<raw_request_table>`
-- WHERE date BETWEEN '2026-07-27' AND '2026-08-03'
--   AND marketplace_client_id IN ('10084549','10088009','10058742','712346')
--       -- Apollo, bigbasket, AJIO, FirstCry(control)
-- GROUP BY 1,2,3,4
-- ORDER BY page_type, requests DESC;
--
-- Expected discriminator:
--   has_mcid + no_category + 0% fill  -> mcid path is broken (platform bug)
--   no_mcid  + no_category + 0% fill  -> request genuinely malformed (client tagging)
--   FirstCry should come back has_mcid + no_category + ~28% fill (the control)
