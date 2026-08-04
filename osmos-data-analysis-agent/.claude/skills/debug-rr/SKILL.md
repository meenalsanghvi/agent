---
name: debug-rr
description: >-
  Debug a week-over-week Response Rate (RR) change for an OnlineSales marketplace.
  Use when the user asks why RR, response rate, or ad fill dropped, is low, or
  changed for a marketplace / agency / page / category / keyword. RR = non-zero
  responses ÷ requests; a drop means fewer requests get filled and it feeds BU.
  Walks requests → responses across page/category/keyword/store/network/device and
  the Display ad-unit path. Not for ROI/ROAS (use debug-roas), CPC (use debug-cpc),
  CTR (use debug-ctr), budget utilisation end-to-end (use debug-bu), or a single
  keyword's low RR (use debug-keyword-low-rr).
---

# Debugging a Response Rate (RR) change

> **Every data call below is `run_report(reportType=…, attributes=[…], metrics=[…], dateRanges=[…], filters=[…])`** against the report named at each step. Report groups are discoverable via the `get_<group>s_reports` tools. Resolve exact column names via `knowledge/tool-map.md` — never from memory.

You are debugging an RR move for an OnlineSales marketplace. **Read
`references/common-rules.md` first** — context setup, dates, PLA-vs-Display rules,
checkpoint model, pre-summary checkpoint, final-report contents, output rules.
Also pull `marketplace_client_id`, `region`, and `timezone` from context.

## ⚠️ Data-retention gate — check BEFORE every call to these tools
Compute `days = (end − start + 1)`; if it exceeds the limit, STOP, warn, wait:
- `CATEGORY_REQUEST_VOLUME_REPORT`, `FILTER_PRESENCE_RR_REPORT` → 15-day
  (`FILTER_PRESENCE_RR_REPORT` always uses the recent 14 days).

`CATEGORY_QUADRANT_REPORT` and `DISPLAY_QUADRANT_REPORT` have **no** retention limit —
their tables keep years of history. Do not warn about them on retention grounds.
Warning: "⚠️ [tool] retains only [N] days; your period is [X] days ([start]–[end])
— results cover only the recent [N] days. Adjust the range before I proceed?"

## Key concepts
- **RR = (Non-Zero Responses ÷ Requests) × 100.** A drop = fewer requests getting
  filled → impacts BU. Different page types have different RR (search typically
  higher).
- **Budget terminology** (never mix): daily budget = one day's cap; total budget =
  daily × N days; week budget = daily × 7. `TRUE_BU_CAMPAIGN_REPORT`'s
  `daily_budget` is the **SUM over the range** (period total) — divide by N for the
  actual daily. Always say which you mean.

## Semantic patterns (the request report has NO campaign IDs)
- **"RR / low BU / underspend for campaign X"** → `CAMPAIGN_LOOKUP_REPORT` →
  `INTERNAL_CAMPAIGN_PERFORMANCE_REPORT` (aggregated: just `perf_campaign_id`; daily: also `perf_campaign_type` IN (PERFORMANCE, INVENTORY, OFFSITE) + group by `perf_date`) (+ `CAMPAIGN_PRODUCT_SELECTION_REPORT`) → extract
  `category_l1/l2/l3` → `RR_PLA_REPORT` (must pass `perf_category_l1` != '' + `perf_page_type` NOT IN ('', 'NA')) with **all available levels
  together** (don't drop levels). Never filter `RR_PLA_REPORT` (PLA) / `RR_DISPLAY_REPORT` (Display) by
  campaign ID (returns 0).
- **"analysis for categories targeted by [campaigns]"** → `CAMPAIGN_LOOKUP_REPORT` →
  `CAMPAIGN_PRODUCT_SELECTION_REPORT` (parallel) → extract categories →
  `RR_PLA_REPORT` (PLA) / `RR_DISPLAY_REPORT` (Display).
- **"what categories does campaign X target?"** → `CAMPAIGN_LOOKUP_REPORT` →
  `CAMPAIGN_PRODUCT_SELECTION_REPORT` → list distinct categories.
- **"which campaigns for this keyword/category?"** → `SEARCH_QUERY_CAMPAIGNS_REPORT`
  or `CAMPAIGNS_IN_CATEGORY_REPORT`.

## SOP — the default path, not an autopilot

This is a **menu of steps the user walks through with you**, not a script to run.
Per `common-rules.md`: every branch below is a question, every step ends the turn,
and the program the user chose is the only one you touch.

**A STEP 3 branch is several sub-steps, not one.** Each fetch that produces a
choice — which categories, which keywords, which campaigns — is a checkpoint.
Present what came back, then let the user narrow before you drill further. Do not
run a whole branch chain in one turn because you already hold the inputs.

### STEP 1 — Triage (parallel, 4 calls)
`PAGE_PERFORMANCE_PLA_REPORT` (PLA, group by `perf_date`) / `DISPLAY_AD_UNIT_PERFORMANCE_REPORT` (Display) (current + baseline) + `PAGE_PERFORMANCE_PLA_REPORT` (PLA) / `DISPLAY_AD_UNIT_PERFORMANCE_REPORT` (Display, `perf_page_type` NOT IN ('','NA')) (current +
baseline). Present overall RR change + which page types are affected (returns
`search_page_affected`, `non_search_pages_affected`).

These four calls are **one** step — fetch them together, present once.

### STEP 2 — Classify, then ASK which branch

Work out which scenario the triage data fits, **say so with the numbers behind
it** — then ask the user which branch to take. **Do not route yourself into a
STEP 3.**

- **A** — `requests_change_pct` > 0 AND `response_pct_change` negative (requests
  up, responses didn't keep up) → STEP 3-A
- **B** — budget dropped (needs `TRUE_BU_CAMPAIGN_REPORT`) → STEP 3-B
- **C** — requests stable + budget stable + responses dropped → STEP 3-C

Put these to the user with `AskUserQuestion`, marking your recommendation and the
evidence for it. Always offer a fourth way out — a different cut, or stop here.

If the evidence is ambiguous, say that plainly rather than forcing a scenario, and
offer the **cheapest ruling-out step first** (B is usually cheapest — one budget
call either confirms or eliminates it).

**Dimension drill-down** (`RR_PLA_REPORT` (PLA) / `RR_DISPLAY_REPORT` (Display)) is available if the
user asks to segment (store_id, network, device, category_l1/l2/l3) or page-level
is inconclusive — don't force it. Call it **without** `group_by_column` first →
`available_columns` for the program_type → present and ask which. (No retention
limit; same for `RR_PLA_REPORT` (must pass group by `perf_store_id`, `perf_category`, `perf_day`, `perf_hour`).) Follow-ups:
- **network** → if a campaign is in scope, `CAMPAIGN_NETWORKS_REPORT` (filter `perf_internal_campaign_id`, not `perf_campaign_id`) FIRST to scope to its actual targeted
  networks (skip untargeted ones). Then ceiling check:
  `RR_PLA_REPORT` (PLA) / `RR_DISPLAY_REPORT` (Display) per network (parallel) — RR ≥ 95% → CEILING, report/stop unless
  partial. **But see the saturation warning below before you stop on a ceiling.**

> ### ⚠️ A near-100% baseline RR is a warning, not a clean bill of health
>
> Before treating RR ≥ 95% as a healthy ceiling, ask **what is filling the slot and at
> what price.** Run `DISPLAY_INVENTORY_CAMPAIGNS_REPORT` (Display) or
> `CAMPAIGNS_IN_CATEGORY_REPORT` (PLA) for the affected ad unit / category and read the
> CPMs and end dates of the eligible campaigns.
>
> A **floor-price house or filler campaign** — very low CPM against a large daily budget —
> wins essentially every auction, because nothing outbids the floor. That produces a
> 99.99% RR that reflects unsold inventory being absorbed, **not** advertiser demand. When
> such a campaign hits its end date, RR falls to whatever real demand supports, and the
> drop looks exactly like a serving failure.
>
> Tells to check:
> - one or more eligible campaigns at a CPM far below the others (e.g. 1.01 vs 150–400)
> - a campaign name or `end_date` implying a fixed window ("23 - 28 July")
> - **few eligible campaigns overall** — a slot with 2–3 eligible campaigns collapses to
>   near-zero when the filler leaves; one with ~65 degrades only partially
>
> **Do not test this by asking whether the lost campaigns' SPEND was material.** Filler
> spends almost nothing while answering everything — ZAR 1,782 of spend can fill 2.4M
> requests. Ask whether a departed campaign could *fill*, not whether it spent.
>
> If a filler expiry explains the drop, that is **not a platform defect** and must not be
> escalated as one. Report it as inventory coming off schedule, and ask whether a
> replacement placement was intended.
- **store_id** → `RR_PLA_REPORT` (must pass group by `perf_store_id`, `perf_category`, `perf_day`, `perf_hour`) (both PLA & Display via
  `program_type`; prerequisite: `RR_PLA_REPORT` (PLA) / `RR_DISPLAY_REPORT` (Display) for PLA, or `(group_by_column="filter_store_id",
  program_type="display")` for Display, confirmed store IDs sent with some near-0
  RR). Buckets hours at store×day×hour into `zero_response` (RR < 1% — no SKUs
  available), `partial_response` (SKUs ran out mid-hour), `full_response` (100%
  fill) — summed totals across hours, NOT individual hour rows.
  `has_store_eligibility_issue = True` → ineligible stores; read
  `adjusted_rr_excluding_ineligible` (true fill for hours with inventory). Report.
- **category_l1/l2/l3** → `RR_PLA_REPORT` (must pass `perf_category_l1` != '' + `perf_page_type` NOT IN ('', 'NA')).
- **device** → report the device gap; confirm via campaign data if needed.

### STEP 3-A — Requests increased
**Non-search:** `CATEGORY_REQUEST_VOLUME_REPORT` (⚠️ 15-day) → categories with request
increases → `RR_PLA_REPORT` (must pass `perf_category_l1` != '' + `perf_page_type` NOT IN ('', 'NA')) (no limit); add
`CATEGORY_QUADRANT_REPORT` if campaign counts/BU% needed; BU low
→ `CAMPAIGNS_IN_CATEGORY_REPORT`. Filters suspected → `get_filter_presence_response_
rates` (see gate below).
**Search:** `SEARCH_QUERY_REQUESTS_PLA_REPORT` (PLA) / `RR_DISPLAY_REPORT` (Display) → keywords with RR drop
(`SEARCH_QUERY_REQUESTS_PLA_REPORT` buckets keyword RR into zero/partial/full response,
Pareto-filtered, min 50 requests — separates no-inventory keywords from partial
fill) → `SEARCH_QUERY_CAMPAIGNS_REPORT` (`campaigns_lost`, `paused_campaigns`). Ask "Are any of
these Search-type campaigns?" — if yes, `CAMPAIGN_KEYWORDS_REPORT` (must pass `perf_is_negative` = 0 for targeted, = 1 for negative) for them,
then `SEARCH_QUERY_REQUESTS_PLA_REPORT` (PLA) / `RR_DISPLAY_REPORT` (Display) for their RR.
`AUDIT_EVENTS_REPORT` (must pass `perf_action_type_id` = 16) (pass `all_campaign_ids`) + `get_product_selection_
changes` (pass `all_client_ids`, SKU removals?). All active + no changes →
`TRUE_BU_CAMPAIGN_REPORT`: budget up but RR down = supply gap; budget stable =
backend/eligibility issue. → then **offer** STEP 5.

### STEP 3-B — Budget dropped
`TRUE_BU_CAMPAIGN_REPORT` + `WALLET_BALANCE_REPORT` (parallel).
`PAGE_PERFORMANCE_PLA_REPORT` (PLA) / `DISPLAY_AD_UNIT_PERFORMANCE_REPORT` (Display, `perf_page_type` NOT IN ('','NA')): RR dropped → `RR_PLA_REPORT` (must pass `perf_category_l1` != '' + `perf_page_type` NOT IN ('', 'NA')); low RR →
`HANDOFF_TO_ROOT` for the RR-specific work (or continue if scoped).
`AUDIT_EVENTS_REPORT` (must pass `perf_action_type_id` = 16) for problem campaigns. → then **offer** STEP 5.

### STEP 3-C — Responses dropped
**Non-search:** `RR_PLA_REPORT` (must pass `perf_category_l1` != '' + `perf_page_type` NOT IN ('', 'NA')) → categories with RR decline (add
quadrant if counts/BU% needed; BU issues → `CAMPAIGNS_IN_CATEGORY_REPORT`;
filters → `FILTER_PRESENCE_RR_REPORT`).
**Search:** `SEARCH_QUERY_REQUESTS_PLA_REPORT` (PLA) / `RR_DISPLAY_REPORT` (Display)
(`SEARCH_QUERY_REQUESTS_PLA_REPORT` for zero/partial/full keyword-RR buckets, Pareto-
filtered, min 50 requests) → `SEARCH_QUERY_CAMPAIGNS_REPORT`
(`effective_status`, `campaigns_lost`, `paused_campaigns`) →
`AUDIT_EVENTS_REPORT` (must pass `perf_action_type_id` = 16) → `AUDIT_EVENTS_REPORT` (must pass `perf_action_type_id` IN (50, 51)). All active + no
changes → `TRUE_BU_CAMPAIGN_REPORT`; budget stable → backend/eligibility.
→ then **offer** STEP 5.

### STEP 4-DISPLAY — **only when Display is the chosen program**

Run this **instead of** STEP 3, never alongside it. If the user chose PLA, this
whole section is out of scope — do not run it, and do not report what it might
have shown. If they chose both, run it as a separate pass with its own
checkpoints and present the two programs separately.

`DISPLAY_AD_UNIT_PERFORMANCE_REPORT` → which ad units dropped RR.
`RR_DISPLAY_REPORT` (must pass `perf_page_type` NOT IN ('', 'NA')) (no limit) → `search_page_affected` (→ keyword-
targeting campaigns likely inactive) / `category_page_affected` (→ category-
targeting campaigns paused). `RR_PLA_REPORT` (PLA) / `RR_DISPLAY_REPORT` (Display) (no limit); add `DISPLAY_QUADRANT_REPORT`
if counts/BU% needed. Problem ad units → `get_display_inventory_
campaigns` (competing campaigns on the slot): high competition (many campaigns,
higher bids/budgets) → outcompeted; few competitors → not competition.
`AUDIT_EVENTS_REPORT` (must pass `perf_action_type_id` = 16) (client_ids from affected ad units): check the
`change_timestamp` time (marketplace tz) for mid-day pauses, `changed_by_type=
"EXTERNAL"` = merchant-initiated — a mid-day pause on a high-volume day is the most
common Display RR cause; report and stop. No pauses → `RR_DISPLAY_REPORT` (group by `perf_ad_unit` for ad-unit, `perf_hour` for hourly)
(prerequisite met) → `adjusted_rr_active_hours`, `has_hourly_pattern`,
`ad_units_without_campaigns` → systemic eligibility/supply. → then **offer** STEP 5.

### STEP 5 — Merchants *(offer it; do not assume they want it)*

A branch ending is a checkpoint, not a cue to run this. Many tickets are answered
by the branch itself — "which ad unit dropped" rarely needs a merchant ranking.
Offer it alongside "we have the answer, write it up" and let the user choose.

`MERCHANT_PERFORMANCE_REPORT` in comparison mode → merchants ranked by contribution
to the marketplace **impressions** change (the RR driver — fewer responses → fewer
impressions), with status, impression share both periods, `pre_period_top_
contributors`, `new_merchants`. Lead with the merchants driving the move; when
impressions barely moved, contribution %s amplify — read with absolute changes.

### STEP 6 — Summary
Pre-summary checkpoint (see `common-rules.md`). Once confirmed →
record the finding in your summary (metric_type `rr`; entities `"type"` ∈ keyword / category
/ page_type) → then the Final Report below.

## Reading tool outputs (key signals)
- `PAGE_PERFORMANCE_PLA_REPORT` (PLA, group by `perf_date`) / `DISPLAY_AD_UNIT_PERFORMANCE_REPORT` (Display): `avg_response_percentage` current vs baseline; requests up + RR
  down = Scenario A.
- `PAGE_PERFORMANCE_PLA_REPORT` (PLA) / `DISPLAY_AD_UNIT_PERFORMANCE_REPORT` (Display, `perf_page_type` NOT IN ('','NA')): `search_page_affected` → keyword drill;
  `non_search_pages_affected` → category drill.
- `SEARCH_QUERY_REQUESTS_PLA_REPORT` (PLA) / `RR_DISPLAY_REPORT` (Display): focus on `top_keywords_by_volume` (Pareto
  keywords) — systemic (many keywords low) vs concentrated (a few driving it).
  `SEARCH_QUERY_REQUESTS_PLA_REPORT` buckets keyword RR into zero/partial/full response
  (Pareto-filtered, min 50 requests) to split no-inventory keywords from partial fill.
- `SEARCH_QUERY_CAMPAIGNS_REPORT`: `paused=0` + no status changes → campaigns fine,
  likely backend; compare both periods to find `campaigns_lost`.
- `CAMPAIGN_KEYWORDS_REPORT` (must pass `perf_is_negative` = 0 for targeted, = 1 for negative): `bidding_value` = merchant's manual bid; many
  targeted keywords at 0% RR → no inventory for those terms; check
  `negative_keywords` for accidental exclusions. **Ask "Is this a Search campaign?"
  before calling.**
- `CAMPAIGN_NETWORKS_REPORT` (filter `perf_internal_campaign_id`, not `perf_campaign_id`): low RR on a network NOT in this list → campaign
  unaffected; a targeted network missing from the request stream → no demand
  reaching it. Use BEFORE any network drill.
- `TRUE_BU_CAMPAIGN_REPORT`: `campaigns_paused_count`, `budget_drop_net_lost`,
  `sellers_with_zero_spend_count`. `WALLET_BALANCE_REPORT`: cross-ref
  `zero_balance`.
- `AUDIT_EVENTS_REPORT` (must pass `perf_action_type_id` = 16): `changed_by_type="EXTERNAL"` = user-initiated.
  `AUDIT_EVENTS_REPORT` (must pass `perf_action_type_id` IN (50, 51)): SKU removals reduce eligibility.
- `DISPLAY_INVENTORY_CAMPAIGNS_REPORT` (ad unit → campaigns): our campaign with lower
  bid/budget than competitors → outcompeted; UNKNOWN strategy / 0 daily budget →
  misconfiguration. `CAMPAIGN_INVENTORY_REPORT` (campaign → ad units):
  few slots → limited reach; high impressions but low CTR on a slot → creative/
  placement issue; zero spend on a slot → not winning that auction.
- `CATEGORY_QUADRANT_REPORT`: BU < 75% → investigate campaigns;
  use `category_l1/l2/l3_filter` individually, not full paths; for RR prefer
  `RR_PLA_REPORT` (must pass `perf_category_l1` != '' + `perf_page_type` NOT IN ('', 'NA')) (no limit).
- `DISPLAY_QUADRANT_REPORT`: low `uniq_campaigns_count` on a
  high-request slot → supply gap; low BU% → delivery/budget issue; compare periods
  to spot slots that lost campaigns; for RR prefer `RR_PLA_REPORT` (PLA) / `RR_DISPLAY_REPORT` (Display) (no limit).
- `CAMPAIGNS_IN_CATEGORY_REPORT` (single period): check `paused_campaigns` and
  `low_bu_campaigns`.
- `FILTER_PRESENCE_RR_REPORT`: **ALWAYS show the filter list (brands,
  zone, storeid, network, city, state, country, device) and ask which to check
  before running.** Returns per-filter present/absent blocks (`requests`,
  `responses`, `response_rate`, `request_share_pct`) plus
  `rr_delta_present_minus_absent`. A filter with much lower RR when PRESENT
  (negative delta) is over-narrowing eligibility. Use late, after other RR causes
  are ruled out.
- `get_keyword_categories` — **UNAVAILABLE.** It was an ADK-only tool reading S3 files
  and has no KAM equivalent, so "what categories is keyword X mapped to?" cannot be
  answered. Say so rather than substituting another report.

## Available drills by program — a menu, not a checklist

**This is not a coverage list.** Run only the program the user chose, and only the
drills they pick. Nothing here is owed to them by default.

- **PLA:** request / RR / category / search / store / network drills above.
- **Display:** the STEP 4 path — `DISPLAY_AD_UNIT_PERFORMANCE_REPORT`,
  `RR_DISPLAY_REPORT` (must pass `perf_page_type` NOT IN ('', 'NA')), `RR_DISPLAY_REPORT` (group by `perf_ad_unit` for ad-unit, `perf_hour` for hourly),
  `DISPLAY_INVENTORY_CAMPAIGNS_REPORT`, `RR_PLA_REPORT` (PLA) / `RR_DISPLAY_REPORT` (Display), `DISPLAY_QUADRANT_REPORT`
  . Note `store_id_filter` maps to `filter_store_id` for Display.

If a drill from the other program would genuinely change the diagnosis, say so in
one line and let the user decide. Do not run it to find out.

## Final Report

Write:

```
RR Analysis Summary | Severity: HIGH/MEDIUM/LOW | Period: [dates]
Root Cause: [description] | Programs: PLA/Display/Both | Pages: Search/Category/etc.
Key Findings: [numbered, actual numbers]
Tables (ACTUAL values):
- Page Types: page_type | RR | Requests [+ Baseline RR | Change if 2 periods]
- Keywords (if search): keyword | RR | Requests [+ Baseline RR | Change]
- Categories (if non-search): path | RR | Requests [+ Baseline RR | Change]
- Merchants — highest spenders FIRST: name | Client ID | Baseline Spend |
  Current Spend | Baseline Impressions | Current Impressions | Baseline CTR |
  Current CTR | Baseline Impr Share% | Current Impr Share% | Cumulative Spend Share%
  [+ Change% columns if 2 periods]  (show RAW baseline & current, not only change %)
Recommendations: [actions]
Cross-References: [other agents' findings]
```
