# Query Inventory — extracted BigQuery SQL from `weekly_analysis_agent`

Faithful extraction of **every** SQL query embedded in the ADK agent's tool
functions, one `.sql` file per query. This is the migration source-of-truth: the
step *before* authoring KAM report configs. It captures not just the SQL but
everything needed to reproduce each query through the org's **KAM service**
(`/api/report/fetch`) instead of hitting BigQuery directly.

## Why this exists

Today each tool function in `weekly_analysis_agent/tools/*.py` builds a SQL
string with Python f-strings, runs it via `run_query()`, then computes derived
metrics (deltas, %, ROI, CVR, CPC, Pareto, verdicts) in Python. When we move to
the Claude SDK we route data through KAM (which can later swap BigQuery for
another DB). KAM returns **raw aggregates**; the Python-side derived-metric layer
stays. So each record here preserves both halves.

## Layout

```
query_inventory/
  README.md                      # this file
  INDEX.md                       # generated: every query, its source, tables
  roas/            <- roi_analysis_tools.py
  cpc/             <- cpc_analysis_tools.py
  ctr/             <- ctr_analysis_tools.py
  bu/              <- bu_analysis_tools.py
  rr/              <- rr_analysis_tools.py
  budget_pacing/   <- budget_pacing_tools.py
  keyword_delivery/<- keyword_delivery_tools.py
  keyword_low_rr/  <- keyword_low_rr_tools.py
  irrelevancy/     <- irrelevancy_tools.py
  shared/          <- common_tools.py, state_tools.py
```

One `.sql` file per distinct query literal. If a tool function contains more than
one query, each gets its own file suffixed `__<n>` or a descriptive suffix
(e.g. `check_gmv_attribution__program.sql`).

## File format (`.sql`)

A comment header block (metadata) followed by the raw SQL body. **Placeholders
are preserved verbatim in the original Python f-string form** (`{agency_id}`,
`{sd}`, `{channel_filter}`, `reporting_{region}`, …) so every file traces back
to source; the header lists the KAM `__TOKEN__` each maps to for the later
config-authoring step.

```sql
-- =====================================================================
-- id:                     <agent>.<function_name>[.<suffix>]
-- source:                 tools/<file>.py:<line>  (fn <function> [-> inner])
-- agent:                  roas | cpc | ctr | bu | rr | budget_pacing | ... | shared
-- description:            one line — what this query returns
-- proposed_kam_report_type: KAM_AGENT_<...>            (or: TBD)
-- parameters:                                          (f-string {name} -> KAM __TOKEN__)
--   {agency_id}   str    -> __AGENCY_ID__
--   {sd}          date   -> __START_DATE_1__
--   {ed}          date   -> __END_DATE_1__
-- injected_fragments:                                  (SQL spliced in by a helper)
--   {channel_filter}  <- get_channel_filter(program_type)   e.g. "channel = 'os_product_ads'"
-- tables:
--   reporting.client_vendor_channel_performance_facts
--   reporting.static_currency_conversion
-- region_specific:        false                        (true -> dataset = reporting_{region})
-- timezone_aware:         false                        (true -> DATE(TIMESTAMP(col), '{timezone}'))
-- comparison_mode:        called once per period (current + baseline) | single call
-- python_derived_metrics: (computed in app layer AFTER KAM returns raw aggregates)
--   actual_roi       = program_gmv / spend
--   attributed_cvr   = program_orders / program_viewproducts * 100
--   *_change, *_change_pct, trend_verdict, ...
-- =====================================================================

WITH program_data AS (
    SELECT ...
    FROM `prj-onlinesales-prod-01.reporting.client_vendor_channel_performance_facts` cvcpf
    WHERE cvcpf.vendor = 'os_ads' AND {channel_filter}
      AND cvcpf.date >= '{sd}' AND cvcpf.date <= '{ed}'
    GROUP BY 1
)
SELECT ...
```

### Rules
- **Verbatim SQL.** Copy the query exactly as it appears in the source, including
  placeholders. Do not reformat, "fix", or resolve fragments.
- **One query per file.** A function that issues N distinct queries -> N files.
- **List every table** referenced (strip the `prj-onlinesales-prod-01.` prefix).
- **`python_derived_metrics`** = the post-query Python that turns raw aggregates
  into the tool's output. Summarize each derived field as `name = formula`.
- If `proposed_kam_report_type` is unknown, write `TBD`.
