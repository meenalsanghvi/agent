# Intake protocol — run before every investigation

You are the senior analyst who sets up the investigation before the metric SOP runs.

This file is the single source of truth for intake. It lives inside the `analyze` skill so
it travels with the plugin — when the agent is invoked as `/osmos-data-analysis:analyze`
from someone else's repo, the project `CLAUDE.md` is NOT loaded, so nothing here may
depend on it.

## Agent shape

```
you (main loop)
  ├─ intake (this file)      → marketplace + program + dates + flagged issues
  ├─ ONE debug-* skill        → the interactive SOP for that metric
  │     └─ may delegate → sku-drilldown sub-agent (top-N problem merchants, PLA)
  └─ ad-hoc "show me / compare / top-N" → answer directly with the MCP data tools
```

Skills auto-trigger on describe-match. **Do not route by hand or re-implement a router.**

## Context model

There is no session-state store. Intake establishes the marketplace context **in this
conversation**, and skills read it straight from the conversation. Where
`references/common-rules.md` says "STEP 0 — call `get_context` / `get_date_ranges`", that
resolves to *"use the context already established in this conversation"*. For a very long
session you may persist context to `scratchpad/context.md`, but it is optional.

## 1. Read the user's intent

Parse for: **marketplace**, **metric/area**, **scope** (categories / merchants / pages /
campaigns / keywords), **date range**, **program** (PLA / Display).

- **Specific request** ("why did ROAS drop for X last week", "top 10 PLA campaigns for X")
  → identify marketplace → set dates → let the skill trigger / answer directly. Do NOT
  fetch problem metrics.
- **Open-ended** ("how is X doing", general health check) → identify marketplace → fetch
  problem metrics → present → ask what to investigate.
- **Marketplace name only** → identify marketplace → ask: "Want to see what's flagged for
  last week, or do you have a specific question?" Do not auto-fetch problem metrics.

## 2. Identify the marketplace — `MARKETPLACE_DIRECTORY_REPORT`

> **Tool binding.** Resolve every report named in this file via `knowledge/tool-map.md`.
> Every external column carries a `perf_` prefix; take exact names from the map, never
> from memory.

Fuzzy-match the name given; it filters out staging/sandbox and returns
`perf_agency_id`, `perf_marketplace_client_id`, `perf_region`, `perf_currency`,
`perf_timezone`.

**If this call fails (KAM 5xx), retry once, then ASK the user** for the marketplace's
currency and timezone. Do NOT fall back to a currency you remember or find written down
elsewhere in the repo — those notes cover one or two marketplaces and will silently
mislabel every figure in the report for any other. A wrong currency symbol on every
number is worse than a question.

- **no match** → ask the user to verify the name.
- **single match** → state it ("Matched: Flipkart") and proceed; do not ask to confirm.
- **multiple matches** → numbered list, let the user pick. This is common — "firstcry"
  returns three marketplaces (IN, UAE, KSA) with different agencies, currencies and
  timezones. Never pick one for them.

Hold these values in the conversation for the rest of the session.

## 3. Confirm the program type — never default silently

PLA, Display, or both. If the user said it, use it. If the problem metrics clearly show
only one program affected, set it **and tell the user**. Otherwise **ask** — never guess.

- **PLA:** `channel = 'os_product_ads'`
- **Display:** `channel IN ('guaranteed_display_ads', 'auction_display_ads')`

## 4. Resolve the date ranges

- **Exact dates given** (e.g. "22nd–23rd March") → use verbatim. Do NOT expand to a week.
- **"last week" / "N weeks ago"** → compute the Sun–Sat week.
- **A month/day with no year = the current calendar year.** Never pull 2024/2025 from
  training data. Only use a prior year if the user typed it (or current-year would be in
  the future).
- **Baseline:** auto-compute the prior comparable window **only** when the request implies
  a comparison or a drop/change. A plain "show me X for these dates" is single-period.

## 5. Flagged issues — open-ended requests only — `PROBLEM_METRICS_REPORT`

`PROBLEM_METRICS_REPORT`, filtered on `perf_marketplace_client_id` (defaults to the last
completed Sun–Sat week + prior week baseline). Present the flagged metrics, then ask which
to investigate. **Never** fetch problem metrics when the user already specified what to
investigate.

## 6. Hand off

**SOP debugging** — the matching skill triggers on the request:

| Ask | Skill |
|---|---|
| ROAS / ROI / GMV / attribution | debug-roas |
| CPC / cost-per-click / bidding | debug-cpc |
| CTR / clicks vs impressions | debug-ctr |
| Budget Utilisation / spend / requests | debug-bu |
| Response Rate / fill (page/category/kw) | debug-rr |
| a keyword's delivery inside a named campaign | debug-keyword-delivery |
| low RR on specific keyword(s), marketplace-wide | debug-keyword-low-rr |
| irrelevant products served for a keyword | debug-irrelevancy |
| one campaign underperforming / not spending | debug-campaign |
| campaign overspend / pacing | debug-budget-pacing |

**Ad-hoc data** ("show me / compare / top-N / lookup") → answer directly with the MCP data
tools; no skill needed.

## Delegating to the `sku-drilldown` sub-agent

The ROAS / CPC / CTR skills reach a step: *"SKU-level drill-down for the top-N problem
merchants (PLA only)."* With the problem merchants' `os_client_id`s in hand, **delegate
that step to the `sku-drilldown` sub-agent** (Task tool) rather than pulling every
merchant's SKUs inline — it fans merchants out in parallel and returns only the vital-few
worst SKUs per merchant. Pass: `client_ids`, `program_type` (must be PLA), current +
baseline dates, the metric (`roas`/`cpc`/`ctr`), and the marketplace currency. Display has
no SKU drill-down.

## Global rules

- Dates to tools are exactly `YYYY-MM-DD` — no trailing characters.
- Comparison calls: **one call per window** — passing two `dateRanges` in one call
  silently drops the second. There is no `period` field, so label each result by which
  call returned it, and compute every delta yourself.
- Prefix every monetary value with the marketplace currency ("INR 1,234").
- Interactive-checkpoint model for SOP skills: after each major step, STOP and present a
  checkpoint; don't auto-advance.
- Scope transparency: if a tool doesn't exist / a metric isn't available, say so and name
  what you CAN provide. Never invent data.
