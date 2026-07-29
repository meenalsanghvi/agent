# KAM report-config authoring prompt (config-only tools)

Author a **single** `KAM_AGENT_*` report config that reproduces one legacy
`weekly_analysis_agent` SOP tool's data fetch **through KAM's class system, with
ZERO kamService change** — reusing only classes already registered in
`kamService/src/utils/schema/schemaRegistry.js`. Then validate it against the KAM
**test** env.

You are invoked once per tool. Stay strictly inside the scope of the one tool you
are given. Do **not** edit kamService. Do **not** invent metric/attribute keys.

---

## 0. Inputs you are given
- `tool` — the legacy tool/function name (e.g. `get_page_level_performance`).
- `skill` — folder bucket (`shared|ctr|cpc|rr|bu|budget_pacing|keyword_delivery|roas|irrelevancy`).
- `sql_file` — path under `osmos-data-analysis-agent/query_inventory/<skill>/…`.
- `report_type` — target `KAM_AGENT_*` reportType.
- `classes` — the registry class(es) the ledger says this tool reuses.

## 1. Context to read first (do not skip)
1. The `sql_file` — the legacy SQL + its header (params, tables, timezone_aware,
   region_specific, comparison_mode, and the `python_derived_metrics` list).
2. Each class in `classes`: open **both**
   `kamService/src/utils/schema/<Class>AttributesClass.js` and
   `<Class>MetricsClass.js` (and its Base* parents when a selector is inherited via
   `...this.getCommon*()`), to read the **exact** attribute/metric keys + selectors.
3. `kamService/src/utils/schema/schemaRegistry.js` — confirm every class name in
   `classes` is registered (the PascalCase key used in the arrays). If a name is not
   registered, STOP and report `blocker: class-not-registered`.
4. Reference config: `kam_report_configs/ctr/KAM_AGENT_CTR_OVERALL.json` (shipped,
   validated). Match its shape.

## 2. The config JSON (write to `kam_report_configs/<skill>/<REPORT_TYPE>.json`)
```json
{
  "reportType": "<REPORT_TYPE>",
  "description": "<agent/skill + step> — <one line>. Reuses <Classes> (no kamService change). Backs the <tool> tool; the agent's Python layer computes <derived>.",
  "source": "GOOGLE_BIG_QUERY",
  "sourceInfo": { "appKey": "GCP_BQ_KAM_CREDENTIALS" },
  "cacheInfo": { "isCachingEnabled": true, "cachingExpiryInSec": 900 },
  "attributesClasses": ["<...>"],
  "metricsClasses": ["<...>"],
  "dateRanges": { "count": 1, "dataAvailabilityDays": 90, "maxDataFetchDaysDuration": 31 },
  "query": { "REPORTING": "<SQL template>", "MERCHANT": "", "GROUPED": "" },
  "application": "irisTestApplication"
}
```

## 3. Query-template rules (the substitution contract)
The engine (`fetchReportDataServiceHelper.js`) replaces these tokens at fetch time.
Author the template as `SELECT …` and let it fill in:
- `__METRICS__` → the requested metric selectors (each carries its own
  `SUM(CASE WHEN alias.date BETWEEN '__START_DATE_1__' AND '__END_DATE_1__' …)`).
- `__ATTRIBUTES__` → requested group-by dimension selectors. **Only for grouped
  reports.** Ungrouped (single-row marketplace aggregate) reports omit it.
- `__ATTRIBUTES_GROUP_BY__` → the GROUP BY list. Use `GROUP BY __ATTRIBUTES_GROUP_BY__`
  for grouped reports.
- `__FILTER__` → dynamic per-call filters. Always end the WHERE with `AND __FILTER__`
  (the engine strips it to nothing when no filters are passed).
- `__AGENCY_ID__`, `__START_DATE_1__`, `__END_DATE_1__`, `__LIMIT__`, `__OFFSET__`,
  `__CLIENT_ID__` (only if a client-scoped fetch).

**Grouped template shape:**
`SELECT __ATTRIBUTES__, __METRICS__ FROM <fact> AS <alias> <JOINs> WHERE <alias>.agency_id = '__AGENCY_ID__' AND <alias>.date BETWEEN '__START_DATE_1__' AND '__END_DATE_1__' AND __FILTER__ GROUP BY __ATTRIBUTES_GROUP_BY__;`

**Ungrouped template shape (like CTR_OVERALL):**
`SELECT __METRICS__ FROM <fact> AS <alias> <JOINs> WHERE … AND __FILTER__;`

Hard rules:
- **Table alias in the template MUST equal the class's default alias**
  (`getDefaultAlias`/the class constructor default: e.g. `mmf`, `mmd`, `mc`,
  `campaign_performance_facts`, `os_display_ads_ad_unit_facts`). Selectors are
  written against that alias — a mismatch produces unresolved SQL.
- **`static_currency_conversion`**: if any selector multiplies by
  `scc.conversion_factor`, the template MUST `LEFT JOIN … static_currency_conversion`
  with the alias the selector uses (`scc`, or the full name if the class references
  the full name — check the class), on
  `from_currency='USD' AND to_currency = <marketplace currency source>`. Match the
  legacy join's currency source (usually `mc.currency` via `marketplace_clients`).
- **Provide every JOIN a selector needs** (cross-table refs like `mc.currency`,
  `mmd.*`, `ctd.vendor`). The class does not add joins — you do.
- **Single-period, `count: 1`.** KAM does NOT auto-emit `_prev/_change/_perc` (verified
  on agency 105). The agent fetches current + baseline as **two separate calls** and
  combines in Python. Never rely on comparison variants in the config.
- Preserve legacy `WHERE` predicates that are **structural** (e.g.
  `page_type NOT IN ('','NA')`, `merchant_type = 'seller'`, `spend > 0` as HAVING) —
  hardcode them into the template. Predicates that are **per-call parameters**
  (program_type/channel, specific campaign_ids/client_ids, a keyword) become KAM
  `filters` on an existing attribute, OR hardcode only if always-constant.

## 4. Metric / attribute selection (NO invention)
- For each raw aggregate the legacy SQL SELECTs (e.g. `SUM(requests)`,
  `SUM(cost_usd*scc.conversion_factor)`), find the **matching class key** whose
  selector is semantically identical. Record the mapping
  `legacy_column → kam_metric_key`.
- For each group-by column (e.g. `page_type`), find the **attribute key**.
- If a needed aggregate/dimension has **no** matching key on the class (or the match
  is a different definition — e.g. converted vs unconverted spend), do **NOT** invent
  one and do **NOT** edit the class. STOP and report
  `blocker: missing-key: <legacy_column> (closest: <key or none>)`. That tool then
  belongs in the verify/needs-class queue, not here.
- Do NOT put derived metrics (cpc, ctr, ir, deltas, Pareto, contribution%, verdicts)
  in the config — those stay in the MCP's `metrics.py`. The config returns only the
  **raw additive aggregates** (+ ratios the class already defines, if the legacy tool
  used the class's own ratio).

## 5. Deliverables (return as a structured report)
1. Write the JSON file to `kam_report_configs/<skill>/<REPORT_TYPE>.json`.
2. Return:
   - `status`: `authored` | `blocked`
   - `report_type`, `file`
   - `classes_confirmed`: each class + "registered ✓" + default alias used
   - `metric_key_map`: `{ combine_name: kam_metric_key }` (feeds `report_map.py`)
   - `attribute_key_map`: `{ group_by_col: kam_attribute_key }` (if grouped)
   - `test_call`: the exact metrics/attributes/filters + a suggested agency
     (default 105) and current window `2026-07-19..2026-07-21` for `post_and_fetch.py`
   - `derived_metrics_note`: what stays in `metrics.py` (from the SQL header)
   - `blockers`: list (empty if authored)
   - `notes`: currency source, any structural WHERE kept, split decisions

## 6. Guardrails
- Never modify anything under `kamService/`. Read-only there.
- Never fabricate a key or a selector. Absent key ⇒ `blocked`.
- If the legacy tool issues **two different-table queries** (e.g. `__pla` +
  `__display`), they cannot share one class query → author **one config per table**
  with suffixed reportTypes (`…_PLA`, `…_DISPLAY`) and note it.
- If the tool has **no date range** (point-in-time, e.g. wallet balance), omit the
  date predicate + use `dateRanges.count: 1` and a template without `__START_DATE_1__`
  (metrics for such tables won't be date-CASE'd — confirm in the class).
- Keep the SQL a single line in the JSON (no newlines inside the string).
```
