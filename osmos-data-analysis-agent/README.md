# Osmos marketplace data-analysis agent

A Claude Code agent that debugs marketplace ad-performance problems — ROAS, CPC, CTR,
budget utilisation, response rate, keyword delivery, campaign-level issues and budget
pacing — for OnlineSales marketplaces.

It has worked 14 real support tickets across 5 marketplaces. See
[`DEMO-2026-08-05.md`](DEMO-2026-08-05.md) for what it found, and the
`ticket-investigations-*.md` files for the full working.

---

## The one thing to understand first

**The agent does not write SQL.** Every report is a reviewed SQL template frozen in
kamService. The agent chooses *which columns, which date range, which filters* — and
nothing else. There are 43 such reports.

So when you ask "why did ROAS drop", it is not composing a query. It is picking reports
from a catalogue, requesting columns, and doing the arithmetic itself. If a number looks
wrong, the SQL is reviewable in a PR; the agent cannot have invented it.

```
you ask a question in plain language
        ↓
Claude Code — picks ONE runbook (debug-roas, debug-rr, …) by matching your request
        ↓  MCP, stdio or HTTP
reporting server — run_report(reportType, attributes, metrics, dateRanges, filters)
        ↓  HTTPS
kamService → BigQuery
```

---

## Getting started

### Run it

```bash
cd osmos-data-analysis-agent
claude
```

`.mcp.json` declares two servers; `.claude/settings.local.json` selects which is enabled:

| Server | What it is |
|---|---|
| `osmos-performance-local` | A ~400-line Python script on your laptop that calls the KAM **test** env directly. No Hades, no Redis, no tokens. Use this for local work. See [`LOCAL_DEMO.md`](LOCAL_DEMO.md). |
| `osmos-reporting-internal-performance` | The hosted MCP — what ships. Needs Hades scope on `/osmosReportingMcp/internalPerformance`. |

The local shim needs `requests` and network access to `test-data.onlinesales.ai`. Nothing
else.

### Ask it something

Just describe the problem. The right runbook triggers on its own:

```
Why did ROAS drop for takealot last week?

For agency 105, CPC 2026-08-01..02 vs 2026-07-25..26. Which page types moved it?

Keyword "iphone" isn't delivering in campaign 1322334. Why?
```

Or start with the front door when you want the full intake first:

```
/analyze takealot — how are we doing 2026-08-01 to 2026-08-02
```

**Give it exact dates when you have them.** It will not expand them to a week, and a
two-day window compared against a mismatched baseline is the single most common way to get
a misleading answer — see "Baselines" below.

---

## The eleven runbooks

One triggers per request. Do not try to invoke several.

| Ask about | Runbook |
|---|---|
| ROAS / ROI / GMV / attribution | `debug-roas` |
| CPC / cost-per-click / bidding | `debug-cpc` |
| CTR / clicks vs impressions | `debug-ctr` |
| Budget utilisation / spend / requests | `debug-bu` |
| Response rate / fill | `debug-rr` |
| A keyword not delivering in a named campaign | `debug-keyword-delivery` |
| Low RR on specific keywords, marketplace-wide | `debug-keyword-low-rr` |
| Irrelevant products served for a keyword | `debug-irrelevancy` |
| One campaign underperforming or not spending | `debug-campaign` |
| Campaign overspend / pacing | `debug-budget-pacing` |
| Open-ended "how are we doing" | `analyze` |

Each reads `references/common-rules.md` first — shared rules on dates, ID forms, program
scoping and the checkpoint model.

---

## What to expect while it runs

**It stops and asks.** After each significant step it presents what it found and waits.
That is deliberate: you steer the investigation rather than receiving a finished essay
built on a wrong assumption. Expect 3–5 checkpoints.

**It takes minutes, not seconds.** A focused single-campaign diagnosis runs ~6 minutes. A
marketplace-wide investigation can take 15–20. Large fetches exceed the MCP's 120-second
tool timeout and get backgrounded — that is normal, the results arrive.

**Large results come back as a file path, not rows.** Above 400 rows the server writes the
*complete* result set to a JSONL file and returns the path, row count and a 5-row sample.
The agent then analyses the file with shell tools. This is how it computes correct totals
without pulling 42,000 rows into context.

**It will tell you when it cannot answer.** That is a feature. If a report only exposes 1%
of the relevant data, you want to hear that rather than get a ranking of the 1%.

---

## Things that will bite you

### Programs are not interchangeable

PLA (`channel = os_product_ads`) and Display (`guaranteed_display_ads`,
`auction_display_ads`) sit on different fact tables. The agent asks which you mean and
locks it. Product selection, keyword targeting and SKU drill-downs are **PLA-only
concepts** — asking for them under a Display lock returns nothing, correctly.

### Baselines

For a short window, match the day of week. In one investigation a Thursday–Friday baseline
against a Saturday–Sunday current window **inverted the conclusion**: CTR read +5.1% and
was actually −4.0%. The agent will push back if your baseline looks wrong; let it.

### Attributed metrics are still settling

`program_gmv` and `program_orders` keep accruing for days after a window closes. A recent
window compared to an older one **overstates any decline**. Measured: the same query
returned ZAR 11,771,088 and then ZAR 11,821,990 hours apart for the same window, while the
older baseline was byte-identical. Spend does not drift; only the attributed side does.

### Campaign IDs come in two forms

The ID in the UI is the *marketing* campaign ID. Some reports key on an *internal* ID.
**Passing the wrong one returns zero rows and no error.** The column name tells you which:
`perf_campaign_id` is the marketing ID, `perf_internal_campaign_id` the internal one.
`CAMPAIGN_LOOKUP_REPORT` maps between them.

If a campaign you know is live comes back empty, suspect the ID form before you conclude
anything — and cross-check against a campaign that is demonstrably spending.

### Filters are advisory, not enforced

- Filters on **metric** columns are **silently ignored** — kamService builds filters into
  the `WHERE` clause and a metric selector is an aggregate, so it is dropped with no error.
  Filter on attributes; apply metric thresholds yourself afterwards.
- `externalRequiredFilters` is declarative. An unfiltered call on a report that declares a
  required filter will run anyway, and may return the whole marketplace.

### A near-100% response rate is a warning, not health

A floor-price house campaign can win every auction and hold a slot at 99.99% fill. When it
hits its end date, fill collapses and it looks exactly like a serving failure. Before
treating high RR as healthy, check what is filling the slot and at what CPM.

---

## Where things live

```
.claude/skills/<name>/SKILL.md          the runbooks
.claude/skills/<name>/references/       common-rules.md, intake-protocol.md
.claude/agents/sku-drilldown.md         sub-agent for per-SKU work (PLA only)
knowledge/reports.md                    report catalogue — columns, required filters, known issues
knowledge/tool-map.md                   legacy tool name → report mapping
kam_report_configs/                     the 43 report configs (source of truth for the SQL)
scripts/build_plugin_knowledge.py       regenerates knowledge/ from the configs
ticket-investigations-*.md              worked examples — start here to see it in action
```

**`knowledge/reports.md` and `knowledge/tool-map.md` are generated.** Do not hand-edit
them — change `scripts/build_plugin_knowledge.py` and re-run it. `--check` fails on drift.

---

## Current status

| | |
|---|---|
| 43 report configs | posted to the KAM test env, values verified |
| 11 runbooks | all exercised on real tickets |
| `sku-drilldown` sub-agent | **never exercised** — no runtime evidence |
| Production | **not ready** — three blockers below |

Nothing here is a config problem; all three are registration/transport:

| Blocker | Why it stops production |
|---|---|
| 173 `perf_*` entries missing from `config/columnMetadata.json` | They exist only in the test env's MongoDB. A file-based deploy leaves every external column unresolvable — all 43 reports fail with "attribute not configured". |
| `GCP_PERF_BQ_KAM_CREDENTIALS` not registered in prod | Every report uses this appKey. Unregistered, BigQuery init fails with HTTP 500. |
| `INTERNAL_PERFORMANCE` rejected by `commonValidators.js` | kamService PR #510 adds the visibility enum; still open. The 15 config PRs (#546–#560) merge after it. |

---

## Contributing a runbook change

1. Edit the `SKILL.md`. Shared rules go in `.claude/skill-common-rules.md`, then run
   `scripts/sync-skill-common.sh`.
2. If you touched a report config, re-run `scripts/build_plugin_knowledge.py`.
3. **Run the runbook on a real ticket.** Every defect found in this agent so far came from
   a run, not from reading the code — static checks passed cleanly throughout and caught
   none of them.
