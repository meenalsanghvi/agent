# Queries that still need a KAM report built (5)

**Update (2026-07-27):** the 2 "just needs scoped validation" reports have been **rebuilt and
validated GREEN** (`SEARCH_QUERY_RR_DISPLAY`, `SEARCH_QUERY_RR_DISPLAY_AD_UNIT` — see bottom).
The **5 below remain** — now **rebuilt + staged on disk** (appKey = `GCP_BQ_KAM_CREDENTIALS_EXTERNAL_DATASET`,
visibility = `INTERNAL_PERFORMANCE`), blocked only on a KAM BigQuery credential that can read their datasets.

**How to (re)build:** author with `.claude/kam-authoring-prompt-v2.md` (inline + external,
`INTERNAL_USER`) from the listed `.sql`, then validate:
```
cd kam_report_configs
HTTP_PROXY= HTTPS_PROXY= NO_PROXY="*" python3 post_external.py \
  --config <skill>/<REPORT_TYPE>.json --agency 105 --current 2026-07-19 2026-07-21 [--filter KEY:OP:VAL]
```
Known test ids (agency 105 = takealot, ZAR): advertiser os_client_id `10009172` (marketing
campaign ids `1105688`,`1322334`); merchant os_client_id `277661`; keyword/search_query `iphone`;
display ad_unit `cart-bottom`.

---

## Blocked on a KAM BigQuery credential (5)

**All 5 are now rebuilt + STAGED on disk** (no longer deleted) with the best-guess fix applied:
`sourceInfo.appKey = "GCP_BQ_KAM_CREDENTIALS_EXTERNAL_DATASET"` and `visibility = INTERNAL_PERFORMANCE`.
Query logic is known-good (posts cleanly; only the BQ fetch is denied). They are **not validated** —
the fetch fails because no BQ credential available to us can read the source dataset.

**appKey test run 2026-07-27 (which credential can read these datasets?):**
- `GCP_BQ_KAM_CREDENTIALS` (default) → Access Denied on both `audit` and `reporting_<region>`.
- `KAM_EXPORT_GCP_BQ_CREDENTIALS` (the only other cred provisioned in test) → also Access Denied.
- `GCP_BQ_KAM_CREDENTIALS_EXTERNAL_DATASET` and `GCP_BQ_KAM_INTERNAL_CREDENTIALS` → **"key not found
  for application: kamService"**, i.e. **not provisioned in the test env** (so untestable here; they
  exist in the kamService codebase config and are likely provisioned in staging/prod).
- Conclusion: **genuine KAM-side blocker** in test; but the fix on our side is just `appKey` once a
  working credential is provisioned. `…_EXTERNAL_DATASET` is the by-name candidate (datasets external
  to `reporting`) — set as the staged best-guess above.

### Need read on `prj-onlinesales-prod-01.audit.audit_logs_v2` (ledger PR2-E)
| suggested report_type | suggested external name | source query (.sql) | notes |
|---|---|---|---|
| INTERNAL_PERF_BUDGET_CHANGES | BUDGET_CHANGES_REPORT | query_inventory/budget_pacing/check_budget_changes_on_date.sql | audit action_type_id=17; JSON_EXTRACT_SCALAR; agency_id direct; `__SP_TIMEZONE__`; required filter campaign_id (scope_id) |
| INTERNAL_PERF_CAMPAIGN_STATUS_CHANGES | CAMPAIGN_STATUS_CHANGES_REPORT | query_inventory/shared/get_campaign_status_changes.sql | audit action 16; expose os_client_id(entity_id)+campaign_id(scope_id) |
| INTERNAL_PERF_PRODUCT_SELECTION_CHANGES | PRODUCT_SELECTION_CHANGES_REPORT | query_inventory/shared/get_product_selection_changes.sql | audit action 50/51; sku_id + added/removed |

### Need read on `prj-onlinesales-prod-01.reporting_<region>.os_product_ads_request_report` (ledger PR2-B)
| suggested report_type | suggested external name | source query (.sql) | notes |
|---|---|---|---|
| INTERNAL_PERF_CATEGORY_REQUEST_VOLUME | CATEGORY_REQUEST_VOLUME_REPORT | query_inventory/rr/get_category_request_volume.sql | region dataset token `__SP_REPORTING_DB_REGION__` (resolves → `_belgium` on test 105); `__SP_MARKETPLACE_CLIENT_ID__` scalar filter (confirmed working); `__SP_TIMEZONE__`; ~15-day retention |
| INTERNAL_PERF_FILTER_PRESENCE_RR | FILTER_PRESENCE_RR_REPORT | query_inventory/rr/get_filter_presence_response_rates.sql | same region table; ungrouped single-row conditional aggregation (present/absent counts per filter) |

**Unblock owner:** platform/KAM team — one of:
1. **Preferred (config-only fix on our side):** confirm a KAM BQ credential that already has read on
   `audit.audit_logs_v2` + `reporting_<region>.os_product_ads_request_report` (likely
   `GCP_BQ_KAM_CREDENTIALS_EXTERNAL_DATASET`), and **provision it in test** (+ confirm in prod). We then
   just point `appKey` at it (already staged) and validate — no grant needed.
2. **Else:** grant the default `GCP_BQ_KAM_CREDENTIALS` service account BQ read on those two datasets.

For the region dataset also confirm the BQ **job location** matches (region datasets live in a
different location). Nothing else config-side — `__SP_*__` tokens + audit-JSON / conditional-agg
shapes are all inline-expressible and structurally validated.

---

## ✅ DONE — was "needs scoped validation", now built + GREEN (2)

Rebuilt on disk and validated green on agency 105 (the earlier timeout was only from an *unfiltered*
fetch; keyword-scoped fetch is fast). `filter_keywords` is populated on the display search ad units
(`search-top`, `search-middle-1`). Confirmed with `keyword=iphone`:
- `INTERNAL_PERF_SEARCH_QUERY_RR_DISPLAY` → iphone 26,915 req / 13,485 resp / 50.1% RR.
- `INTERNAL_PERF_SEARCH_QUERY_RR_DISPLAY_AD_UNIT` → iphone: search-top 99.99% RR + search-middle-1 0% RR
  (reconciles to the totals above).
Both flipped to `visibility: INTERNAL_PERFORMANCE` with the rest.

---

## Status
- **5 remain**, all blocked on a KAM BigQuery access grant (audit dataset ×3, region request-log ×2).
  No config change needed — build/rebuild from the `.sql` once the grant lands.
- Source `.sql` queries remain in `query_inventory/` — the basis for building.
- Everything else in the queue is built + green (65 on disk; see `REMAINING_QUEUE.md`).
