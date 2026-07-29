# KAM inline + external report authoring (the proven workflow)

Author ONE `weekly_analysis_agent` query as an **inline (Gen1) KAM report** that is
**exposed through the external report system** and served (eventually) by
`osmos-reporting-mcp`. No schema classes, no kamService PR. Validated end-to-end on the
golden reference below.

**Golden reference (read it first):**
`kam_report_configs/shared/INTERNAL_PERF_PAGE_LEVEL.json` — a working inline+external
config. Copy its shape exactly. Validate with `kam_report_configs/post_external.py`.
External-system concepts are in `/Users/manav.kumawat/Downloads/index.html` (the KAM Field
Manual) — Parts IV–V; the rules below already distill it.

---

## Inputs you are given
- `tool` — legacy function name (e.g. `check_program_spend`).
- `skill` — bucket (roas|cpc|ctr|bu|rr|budget_pacing|keyword_delivery|keyword_low_rr|irrelevancy|campaign|shared).
- `sql_file` — `query_inventory/<skill>/<tool>.sql` (the source of truth — copy predicates faithfully).
- `report_type` (internal, e.g. `INTERNAL_PERF_<NAME>`), `external_report_type`
  (`<NAME>_REPORT`), and the `report_group` tag(s) from the taxonomy.

## Output
Write `kam_report_configs/<skill>/<report_type>.json`, then validate and report.

---

## STEP A — the inline base config (query → template)

Turn the `.sql` into a KAM template. The engine fills the tokens.

```json
{
  "reportType": "<INTERNAL_PERF_NAME>",
  "source": "GOOGLE_BIG_QUERY",
  "sourceInfo": { "appKey": "GCP_BQ_KAM_CREDENTIALS" },
  "cacheInfo": { "isCachingEnabled": true, "cachingExpiryInSec": 900 },
  "attributes": { "<key>": { "key":"<key>", "selector":"<alias>.<col>", "type":"STRING",
                             "externalColumnName":"...", "description":"...", "filterTags":[...] } },
  "metrics":    { "<key>": { "key":"<key>", "selector":"COALESCE(SUM(CASE WHEN <alias>.date BETWEEN '__START_DATE_1__' AND '__END_DATE_1__' THEN <expr> ELSE 0 END),0)",
                             "type":"FLOAT", "externalColumnName":"...", "description":"...", "filterTags":[...] } },
  "dateRanges": { "count": 1, "dataAvailabilityDays": 90, "maxDataFetchDaysDuration": 31 },
  "query": { "REPORTING": "<one-line SQL>", "MERCHANT": "", "GROUPED": "" },
  "application": "irisTestApplication"
  /* + the STEP B external fields */
}
```

**Query template shapes**
- Grouped: `SELECT __ATTRIBUTES__, __METRICS__ FROM <fact> AS <alias> <JOINs> WHERE <scope+date+structural> AND __FILTER__ GROUP BY __ATTRIBUTES_GROUP_BY__;`
- Ungrouped (single-row aggregate): `SELECT __METRICS__ FROM <fact> AS <alias> <JOINs> WHERE <scope+date> AND __FILTER__;` (no `__ATTRIBUTES__`, no GROUP BY)

**Placeholder mapping** (from the `.sql` header): `{agency_id}`→`__AGENCY_ID__`,
`{sd}`/`{ed}` (or `{start_date}`/`{end_date}`)→`__START_DATE_1__`/`__END_DATE_1__`.
Per-call entities (`{campaign_ids}`, `{client_ids}`, a keyword, `{marketplace_client_id}`)
→ KAM `filters` on an attribute (NOT hardcoded).

---

## STEP B — external exposure

Add to the config:
- `"externalReportType"`: `<NAME>_REPORT` — globally unique, SCREAMING_SNAKE, ends `_REPORT`.
- `"visibility"`: **`"INTERNAL_USER"`** (our lane — served by the existing
  `/osmosReportingMcp/beatsInternal` mount). NEVER `BEATS`/`PULSE`/`LOCALIUM_BEATS`/`OSMOSX_BEATS`.
- `"filterTags"`: report-level tag(s) from the taxonomy, e.g. `["report_group:bu"]`.
- `"externalRequiredFilters"`: external names of any mandatory filter (e.g. `["campaign_id"]`),
  else `[]`.
- `"description"`: 1–2 sentences written FOR the model — name the key dimensions + metrics.

On **each column you expose**, add:
- `"externalColumnName"`: the external name (translation keys on THIS field).
- `"description"`: what it is.
- `"filterTags"`: **must intersect the report's `filterTags`** or the column is silently
  dropped (the intersection rule).

**columnMetadata** — every `externalColumnName` must have an entry in the columnMetadata
collection (columnName + description + filterTags). `post_external.py` derives these from
the config and posts them automatically. ⚠️ columnMetadata lives in Mongo — a stale entry
causes phantom "metric not configured" errors; `post_external.py` re-posts every run.

**Never expose:** raw `agency_id` / `marketplace_client_id`; `_prev`/`_change`/`_perc`
variants. (Under `INTERNAL_USER` it IS fine to expose the working IDs the analyst needs —
`os_client_id`, `campaign_id`, `merchant_id` — unlike advertiser-facing catalogues.)
**Reuse canonical external names** where semantics match: `clicks`, `impressions`, `spend`,
`ctr`, `cpc`, `cpm`, `roas`, `orders`, `revenue`, `requests`, `responses`, `page_type`,
`date`, `os_client_id`, `campaign_id`. No synonyms.

---

## STEP C — validate
```
cd kam_report_configs
HTTP_PROXY= HTTPS_PROXY= NO_PROXY="*" python3 post_external.py \
  --config <skill>/<report_type>.json --agency 105 --current 2026-07-19 2026-07-21
```
Expect: columnMetadata 200 · config OK · catalogue shows `<NAME>_REPORT` present · fetch
`useExternalNames` returns rows under the EXTERNAL names. Agency 105 = takealot (ZAR,
Africa/Johannesburg). For point-in-time reports pass any window (dates inert).

---

## THE GOTCHAS (this is why the one example worked — honour every one)

1. **`AND __FILTER__` terminator.** The WHERE must end `… AND __FILTER__` (engine strips
   `AND __FILTER__` when no filters). A bare `WHERE __FILTER__` → "Unrecognized name __FILTER__".
2. **Fetch needs ≥1 metric.** Pure-attribute reports (directories, dimension lookups) MUST
   include a `placeholder_metric` (`"selector":"0","type":"FLOAT"`) and request it. Reports
   with real metrics don't.
3. **Agency scoping.** Most fact tables have **no `agency_id`** — they have
   `marketplace_client_id`. Join `marketplace_clients AS mc ON <fact>.marketplace_client_id
   = mc.marketplace_client_id` and filter `mc.agency_id = '__AGENCY_ID__'`. Only tables that
   truly carry `agency_id` (e.g. `monetize_merchant_facts`, `clients`) may filter it
   directly — the `.sql` tells you. **Never join `marketplace_client_id = client_id`** (two
   different id spaces); comparing them with `!=` is only ever an intentional exclusion filter.
4. **Converted currency inline (the superpower).** Write it directly:
   `SUM(<alias>.cost * scc.conversion_factor)` (or `cost_usd * …`), with
   `LEFT JOIN static_currency_conversion AS scc ON scc.from_currency='USD' AND
   scc.to_currency = mc.currency`. No class needed. Match the `.sql`'s currency source.
5. **Metric selectors carry their own date window** — `SUM(CASE WHEN <alias>.date BETWEEN
   '__START_DATE_1__' AND '__END_DATE_1__' THEN … ELSE 0 END)`. Keep a coarse
   `<alias>.date BETWEEN …` in the WHERE too. `count: 1` (single period) — comparison is
   two separate fetches combined in Python; the external system won't emit `_prev` anyway.
6. **Table alias in the template = the alias your selectors use** (short is fine for inline:
   `pf`, `mmf`, `cvcpf`, `mc`, `scc`). Every JOIN a selector references must be present.
7. **Structural WHERE stays; ORDER BY / LIMIT go.** Keep predicates like
   `page_type NOT IN ('','NA')`, `merchant_type='seller'`, channel filters. Drop legacy
   `ORDER BY`/`LIMIT` (the engine does order/pagination via `__ATTRIBUTES_ORDER_BY__` /
   `__LIMIT__`/`__OFFSET__` and request params). A `spend > 0` type gate → a HAVING or leave
   to the caller.
8. **Program type** (pla/display) is a per-call filter, not hardcoded — expose the channel
   attribute (or accept it as a filter). PLA `channel='os_product_ads'`; Display
   `channel IN ('guaranteed_display_ads','auction_display_ads')`.
9. **Cross-tenant / point-in-time.** A directory (agencies) omits `__AGENCY_ID__` entirely
   (cross-tenant). A point-in-time lookup omits the date predicate (no `__START_DATE_1__`).
10. **SQL is a single line** in the JSON (no newlines). Config JSON must be valid.
11. **`filterTags` must intersect** between the report and each exposed column, or the
    column vanishes from the catalogue silently.
12. **columnMetadata is GLOBAL by columnName and a POST REPLACES its filterTags.** Shared
    canonical columns (`spend`, `clicks`, `impressions`, `ctr`, …) are used by MANY reports
    (ours AND production BEATS/PULSE/LOCALIUM). A naive per-report post STRIPS the other
    reports' tags and breaks them. **Always post columnMetadata via `post_external.py`
    (it now MERGES: union of production-file tags + current test-env tags + this report's
    tags) — never post columnMetadata directly with replace.** After a wave, run
    `python sync_column_metadata.py` to re-union everything and confirm no clobber.

---

## TAG TAXONOMY (decide once — each distinct `report_group:<v>` mints a `get_<v>s_reports` MCP tool)

Tag a report by **what its data IS**, using 1–2 of these. Primary = its home domain;
add a shared-data-family tag when the report is reused across skills.

| `report_group:` value | Covers |
|---|---|
| `roas` | GMV attribution, order trends, target ROI |
| `cpc` | page/subtype/merchant/SKU CPC |
| `ctr` | CTR overall, merchant/SKU CTR |
| `bu` | program spend, requests, wallet, true-BU, ad-unit |
| `rr` | response-rate by page/dimension/store, display RR |
| `keyword` | targeted-keyword perf, competition, search-query, low-RR |
| `campaign` | single-campaign perf, status, product selection, targeting |
| `budget_pacing` | delivery mode, pacing buckets, minute-level |
| `irrelevancy` | responded SKUs / relevancy |
| `page_performance` | page-type aggregates (shared by cpc/ctr/rr/bu) |
| `merchant_breakdown` | per-merchant breakdowns (shared across metrics) |
| `category` | category-level performance / response rates |
| `sku` | SKU-level drill-downs |
| `search_query` | what users typed (search-query reports) |
| `intake` | marketplace directory, problem metrics |

Rule of thumb: `check_program_spend`→`bu`; `get_merchant_ctr_breakdown`→
`merchant_breakdown`+`ctr`; `get_category_response_rates`→`category`+`rr`;
`get_page_level_performance`→`page_performance`.

---

## Deliverables (return a structured report)
- `status`: `authored` | `blocked`
- `file`, `report_type`, `external_report_type`, `filterTags`
- `column_map`: `{ external_name: internal_selector_summary }` (attrs + metrics)
- `validation`: paste the `post_external.py` result — catalogue-present? rows returned? spend converted?
- `notes`: currency source, structural WHERE kept, scoping (mc-join vs direct agency_id),
  program-type handling, any per-call filters exposed.
- `blockers`: empty, or the exact SQL construct KAM can't express (should be rare now that
  converted currency is inline — genuine blockers are things like `JSON_EXTRACT_SCALAR`
  audit shapes or per-marketplace suffixed tables).

## Guardrails
- Never modify `kamService/`. Inline configs need no class.
- **Do NOT create throwaway/helper reports in the shared test catalogue**, and do NOT post
  columnMetadata by hand. For a merchant-scoped validation, reuse a KNOWN id (agency 105
  merchant `os_client_id` = `277661`) — never mint a "clients directory" report to discover ids.
- Timezone-aware queries: write `DATE(TIMESTAMP(col,'UTC'), '__SP_TIMEZONE__')` — the SP token
  resolves per-agency (confirmed: agency 105 → 'Africa/Johannesburg'). Region-specific
  datasets: `reporting__SP_REPORTING_DB_REGION__.table` (token → `_<region>` or empty).
- Copy the `.sql`'s aggregates/predicates faithfully — do not invent metrics or change
  attribution definitions.
- If a construct genuinely can't be templated (rare), mark `blocked` with the reason —
  don't emit SQL you haven't reasoned through.
