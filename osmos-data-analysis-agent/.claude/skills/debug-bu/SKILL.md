---
name: debug-bu
description: >-
  Debug a week-over-week Budget Utilisation (BU) change for an OnlineSales
  marketplace. Use when the user asks why BU, budget utilisation, or spend-vs-
  budget dropped, is low, or changed for a marketplace / agency / campaign, or why
  a campaign is underspending. Walks the delivery funnel (Requests → Responses/RR →
  Impressions/IR → Clicks/CTR → Spend/CPC) and stops at the first broken layer. Not
  for ROI/ROAS (use debug-roas), CPC (use debug-cpc), CTR (use debug-ctr), response
  rate in isolation (use debug-rr), or budget-pacing overspend (use
  debug-budget-pacing).
---

# Debugging a Budget Utilisation (BU) change

> **Every data call below is `run_report(reportType=…, attributes=[…], metrics=[…], dateRanges=[…], filters=[…])`** against the report named at each step. Report groups are discoverable via the `get_<group>s_reports` tools. Resolve exact column names via `knowledge/tool-map.md` — never from memory.

You are debugging a BU move for an OnlineSales marketplace. **Read
`references/common-rules.md` first** — context setup, date handling, PLA-vs-Display
rules, the checkpoint model, the pre-summary checkpoint, the final-report
contents, and output rules. Also pull `marketplace_client_id`, `region`, and
`timezone` from context — several BU tools need them.

## ⚠️ Data-retention gate — check BEFORE every call to these tools

Some tools query raw request tables with limited retention. Before calling one,
compute `days = (end_date − start_date + 1)`. If it exceeds the limit, STOP, warn
the user, and wait for confirmation:
- `CATEGORY_REQUEST_VOLUME_REPORT`, `FILTER_PRESENCE_RR_REPORT` →
  15-day limit (`FILTER_PRESENCE_RR_REPORT` always uses the recent 14 days).
  Both read `os_product_ads_request_report`, whose partitions expire after 15 days.

`CATEGORY_QUADRANT_REPORT` and `DISPLAY_QUADRANT_REPORT` have **no** retention
limit — their tables keep years of history. Do not warn about them or steer the
user to a different report on retention grounds.

Warning: "⚠️ [tool] queries a table that only retains [N] days of data. Your
period is [X] days ([start]–[end]) — results will only cover the most recent [N]
days. Adjust the range before I proceed?"

## Key concepts

- **BU = Spend ÷ Budget × 100.** Funnel: **Requests → Responses (RR) →
  Impressions (I/R) → Clicks (CTR) → Spend (CPC)**. A drop at ANY layer reduces BU.
  Diagnose top-down and **stop at the first broken layer.**
- **Budget drop ≠ BU drop.** A proportional budget + spend decrease is program
  shrinkage, not a BU problem.
- **Always assess ABSOLUTE BU%.** 0.01% → 0.02% is still critically low.

### Budget terminology — never mix these up
- **Daily budget:** a campaign's cap for a SINGLE day (the configured value).
- **Total budget (period):** sum of daily budgets across the period's days
  (daily × N). **Week budget** = daily × 7.
- `TRUE_BU_CAMPAIGN_REPORT` gives you both directly — do NOT derive one from the other:
  - `perf_daily_budget` is the **latest day's** budget in the window (`MAX_BY` on
    date), so it is a true single-day figure.
  - `perf_total_budget` is the **SUM across the window**.
  On a window where the budget didn't change, `total = daily × N`. When it did change,
  they will not divide evenly — that is correct, not a bug.
- `perf_daily_budget` can be **negative** — it is capped by remaining wallet balance,
  and an overdrawn wallet is genuinely negative. Do not clamp it to zero; report it as
  overdrawn. But exclude negatives before summing a budget aggregate, or the total
  understates.
- When reporting, always say which: "daily budget of X" vs "total budget of X over
  N days". Never just "budget".

**Comparison mode:** most BU tools return SINGLE-period data — call them for both
periods in parallel and compute changes yourself. EXCEPTION (preferred):
`MERCHANT_PERFORMANCE_REPORT` supports comparison mode (pass baseline dates) →
merchants ranked by contribution to the marketplace SPEND change (the BU driver)
with status, spend share both periods, `pre_period_top_contributors`,
`new_merchants`. Report contribution %s, not raw spend alone.

## Semantic patterns (what the user means)
The request report has **no campaign IDs** — resolve a campaign to its categories
first:
- **"RR / low BU / underspend for campaign X"** → `CAMPAIGN_LOOKUP_REPORT` →
  `INTERNAL_CAMPAIGN_PERFORMANCE_REPORT` (aggregated: just `perf_campaign_id`; daily: also `perf_campaign_type` IN (PERFORMANCE, INVENTORY, OFFSITE) + group by `perf_date`) (spend, budget, clicks, impressions) +
  `CAMPAIGN_PRODUCT_SELECTION_REPORT` → extract distinct `category_l1/l2/l3` →
  `RR_PLA_REPORT` (must pass `perf_category_l1` != '' + `perf_page_type` NOT IN ('', 'NA')) with **all available category levels together**
  (don't drop levels). Add `CATEGORY_QUADRANT_REPORT` only if
  BU%/campaign counts are also needed.
- **"analysis for categories targeted by [campaigns]"** → `CAMPAIGN_LOOKUP_REPORT` →
  `CAMPAIGN_PRODUCT_SELECTION_REPORT` (parallel) → extract categories →
  `RR_PLA_REPORT` (PLA) / `RR_DISPLAY_REPORT` (Display) with `group_by_column` + those category filters.
  Steps must complete in order.
- **"what categories does campaign X target?"** → `CAMPAIGN_LOOKUP_REPORT` →
  `CAMPAIGN_PRODUCT_SELECTION_REPORT` → list distinct categories.
- **"which campaigns are active for this keyword/category?"** →
  `SEARCH_QUERY_CAMPAIGNS_REPORT` or `CAMPAIGNS_IN_CATEGORY_REPORT`.
- Never filter `RR_PLA_REPORT` (PLA) / `RR_DISPLAY_REPORT` (Display) by campaign ID — it returns 0.

## SOP — default investigation flow

This is a **menu of steps the user walks through with you**, not a script to run.
Per `common-rules.md`: every branch below is a question, every step ends the turn,
and the scope the user set — program, category, campaign — is the only one you touch.

**A branch is several sub-steps, not one.** Each fetch that produces a choice is a
checkpoint: present what came back, then let the user narrow before drilling further.
Do not run a whole chain in one turn just because you already hold the inputs.

If the user asks something specific, skip the SOP and call the matching tool
directly.

### STEP 1 — Triage (parallel)
Call in ONE parallel turn: `PAGE_PERFORMANCE_PLA_REPORT` (PLA, group by `perf_date`) / `DISPLAY_AD_UNIT_PERFORMANCE_REPORT` (Display), `TRUE_BU_CAMPAIGN_REPORT`,
`GMV_ATTRIBUTION_REPORT`. If baseline dates exist, call all three for baseline too
(6 calls). Then **present the available group-by dimensions** and ask which to
group by: `page_type`, `store_id`, `network`, `category_l1/l2/l3/l4/l5`, `device`.
**STOP — wait for the user's choice.** Then call `RR_PLA_REPORT` (PLA) / `RR_DISPLAY_REPORT` (Display)
with the chosen `group_by_column` (no retention limit; add category/other filters
only if the user asked to scope).

### STEP 2 — Evaluate
**2A — BU% thresholds:** < 5% critically low (investigate regardless); 5–30% low
(investigate); > 60% healthy. With baseline, `bu_change_pp = current − baseline`:
≈0 and bu% > 30% → stable, stop; ≈0 and bu% < 5% → still critical, proceed;
< −2pp → confirmed drop, proceed.

**2B — Dimension evaluation:** classify the pattern — **CONCENTRATED** (1–3 values
near-0 RR, rest healthy → segment-specific), **UNIFORM DROP** (all low → not
dimension-specific → 2C), **SPARSE** (only blank/single value → 2C). For a
CONCENTRATED drop, present the problem segments and use the known drill patterns:
- **network** → if a campaign is in scope, `CAMPAIGN_NETWORKS_REPORT` (filter `perf_internal_campaign_id`, not `perf_campaign_id`) first
  to confirm it targets those networks (else marketplace-wide noise). Check for an
  RR **CEILING**: `RR_PLA_REPORT` (PLA) / `RR_DISPLAY_REPORT` (Display) per network (parallel). RR ≥ 95% in a
  network×category combo → ceiling (no headroom; report and stop unless partial). No combos near 100%
  → not a ceiling → 2C.
  **Before stopping on a ceiling:** a near-100% RR can mean a floor-price house/filler
  campaign is absorbing unsold inventory, not that demand is healthy. Check the eligible
  campaigns' CPMs and end dates (`DISPLAY_INVENTORY_CAMPAIGNS_REPORT` /
  `CAMPAIGNS_IN_CATEGORY_REPORT`) — see the saturation warning in `debug-rr`. Judge a
  departed campaign by whether it could *fill*, never by whether its spend was material.
- **store_id** → `RR_PLA_REPORT` (must pass group by `perf_store_id`, `perf_category`, `perf_day`, `perf_hour`) (session dates; `page_type_filter`)
  for hourly eligibility. `has_store_eligibility_issue = True` → specific stores
  ineligible; report and stop.
- **device** → likely no eligible SKUs / no campaigns targeting the device;
  confirm via `INTERNAL_CAMPAIGN_PERFORMANCE_REPORT` (aggregated: just `perf_campaign_id`; daily: also `perf_campaign_type` IN (PERFORMANCE, INVENTORY, OFFSITE) + group by `perf_date`).
- **category_l1/l2/l3** → `RR_PLA_REPORT` (must pass `perf_category_l1` != '' + `perf_page_type` NOT IN ('', 'NA')); add
  `CATEGORY_QUADRANT_REPORT` if BU%/spend also needed.
- Any other dimension → interpret what near-0 RR means (no targeting / no eligible
  products / config gap), report, and ask before 2C.

**2C — Classify the signal:** requests dropped → 3-REQUESTS; budget increased but
spend didn't follow → 3-BUDGET; requests stable but responses dropped → 3-RR;
mixed → requests first, then budget; both stable → 3-RR.

### STEP 3-REQUESTS
1. Which pages lost requests (from `PAGE_PERFORMANCE_PLA_REPORT` (PLA, group by `perf_date`) / `DISPLAY_AD_UNIT_PERFORMANCE_REPORT` (Display))? 2. Checkpoint if multiple
pages. 3. PLA: `RR_PLA_REPORT` (must pass `perf_category_l1` != '' + `perf_page_type` NOT IN ('', 'NA')) (+ `CATEGORY_QUADRANT_REPORT`
if BU%/spend needed); Display: skip to STEP 4. 4. `get_merchant_bu_
breakdown` → concentrated or widespread? 5. Concentrated →
`WALLET_BALANCE_REPORT` → `AUDIT_EVENTS_REPORT` (must pass `perf_action_type_id` = 16). 6. → then **offer** STEP 6.

### STEP 3-BUDGET
Focus on `campaigns_with_budget_increase` from `TRUE_BU_CAMPAIGN_REPORT`.
1. `WALLET_BALANCE_REPORT` → `AUDIT_EVENTS_REPORT` (must pass `perf_action_type_id` = 16) for those
campaigns. 2. `PAGE_PERFORMANCE_PLA_REPORT` (PLA) / `DISPLAY_AD_UNIT_PERFORMANCE_REPORT` (Display, `perf_page_type` NOT IN ('','NA')): search RR dropped →
`SEARCH_QUERY_REQUESTS_PLA_REPORT` (PLA) / `RR_DISPLAY_REPORT` (Display); non-search RR dropped →
`RR_PLA_REPORT` (must pass `perf_category_l1` != '' + `perf_page_type` NOT IN ('', 'NA')); Display → `DISPLAY_AD_UNIT_PERFORMANCE_REPORT` →
`DISPLAY_INVENTORY_CAMPAIGNS_REPORT` for problem slots; **low RR → `HANDOFF_TO_ROOT`
for the RR skill**; RR stable → low CPC / delivery issue, continue. 3. Sellers with
budget increase but flat spend → `RR_PLA_REPORT` (must pass `perf_category_l1` != '' + `perf_page_type` NOT IN ('', 'NA')); category RR = 100%
→ CEILING, report and stop for those sellers — after checking it is real demand and not
floor-price filler (see the saturation warning in `debug-rr`).
4. `MERCHANT_PERFORMANCE_REPORT` →
STEP 6.

### STEP 3-RR
PLA: `PAGE_PERFORMANCE_PLA_REPORT` (PLA) / `DISPLAY_AD_UNIT_PERFORMANCE_REPORT` (Display, `perf_page_type` NOT IN ('','NA')). Display: `DISPLAY_AD_UNIT_PERFORMANCE_REPORT` →
`RR_DISPLAY_REPORT` (must pass `perf_page_type` NOT IN ('', 'NA')). RR stable → STEP 4-IR. RR dropped → funnel break:
- **PLA drill:** checkpoint if both search + non-search → ask which first.
  Search → `SEARCH_QUERY_REQUESTS_PLA_REPORT` (PLA) / `RR_DISPLAY_REPORT` (Display) → `SEARCH_QUERY_CAMPAIGNS_REPORT` →
  `AUDIT_EVENTS_REPORT` (must pass `perf_action_type_id` = 16). Non-search → `RR_PLA_REPORT` (must pass `perf_category_l1` != '' + `perf_page_type` NOT IN ('', 'NA')) →
  `CAMPAIGNS_IN_CATEGORY_REPORT`. Filters suspected → `get_filter_presence_response_
  rates` (⚠️ recent 14 days): for each client filter (brands, zone, storeid,
  network, city, state, country, device) it compares RR present vs absent — a
  filter with much lower RR when PRESENT is over-narrowing eligibility.
- **Display drill:** `RR_DISPLAY_REPORT` (must pass `perf_page_type` NOT IN ('', 'NA')) (no limit) →
  `RR_PLA_REPORT` (PLA) / `RR_DISPLAY_REPORT` (Display) (no limit); add `DISPLAY_QUADRANT_REPORT` if
  counts/BU% needed. Problem ad units → `DISPLAY_INVENTORY_CAMPAIGNS_REPORT` (slot
  competition; high competition = outcompeted) → yes →
  `AUDIT_EVENTS_REPORT` (must pass `perf_action_type_id` = 16) (mid-day pauses, `changed_by_type="EXTERNAL"`) →
  no pauses → `RR_DISPLAY_REPORT` (group by `perf_ad_unit` for ad-unit, `perf_hour` for hourly) (scheduling).
After the drill → `MERCHANT_PERFORMANCE_REPORT` → then **offer** STEP 6.

### STEP 4-IR
`PAGE_PERFORMANCE_PLA_REPORT`; compute I/R = impressions ÷ responses per page. I/R
stable → STEP 5-CTR. I/R dropped → PLA: `RR_PLA_REPORT` (must pass `perf_category_l1` != '' + `perf_page_type` NOT IN ('', 'NA')) /
`SEARCH_QUERY_REQUESTS_PLA_REPORT` (PLA) / `RR_DISPLAY_REPORT` (Display) (no limit; + `CATEGORY_QUADRANT_REPORT`
if counts/BU% needed); Display: `DISPLAY_AD_UNIT_PERFORMANCE_REPORT` →
`DISPLAY_INVENTORY_CAMPAIGNS_REPORT`. → `MERCHANT_PERFORMANCE_REPORT` → then **offer** STEP 6.

### STEP 5-CTR
`MERCHANT_PERFORMANCE_REPORT` filtered to the program (`perf_channel`) + page-level CTR
from STEP 4. **Not `CTR_OVERALL_REPORT`** — it is program-blended and cannot be scoped
to PLA or Display. CTR dropped → `MERCHANT_PERFORMANCE_REPORT` →
`AUDIT_EVENTS_REPORT` (must pass `perf_action_type_id` = 16) →
`MERCHANT_PERFORMANCE_REPORT` → then **offer** STEP 6. CTR stable → `HANDOFF_TO_ROOT: All funnel
layers stable. Route to CPC skill.`

### STEP 6 — Summary
6A. `MERCHANT_PERFORMANCE_REPORT` if not done — three segments: largest spend drops;
top budget holders with low BU%; recent budget increases with flat spend.
6B. Severity: bu% < 5% → at least MEDIUM; > 15pp drop → HIGH; 5–15pp → MEDIUM;
< 5pp → LOW.
6C. Pre-summary checkpoint (see `common-rules.md`). Once confirmed →
record the finding in your summary (metric_type `bu`; `root_cause` a BU-specific label such
as "Request Drop on Search Pages" / "Budget Expansion Outpaced Spend" /
"Network×Category Ceiling" / "Funnel Break: RR Decline"; entities `"type"` ∈
page_type / merchant / category / campaign) → then the Final Report below.

## Additional / auxiliary tools
- `CATEGORY_REQUEST_VOLUME_REPORT` — category-level request volume (⚠️ 15-day).
- `CAMPAIGN_LOOKUP_REPORT`, `CAMPAIGN_PRODUCT_SELECTION_REPORT` — the campaign→categories
  resolution used by the semantic patterns.

## Available drills by program — a menu, not a checklist

**This is not a coverage list.** Run only the program the user chose, and only the
drills they pick. Nothing here is owed to them by default. If a drill from the other
program would genuinely change the diagnosis, say so in one line and let the user
decide — do not run it to find out.
- **PLA:** the request/RR/category/search drills above.
- **Display:** its own funnel path — `DISPLAY_AD_UNIT_PERFORMANCE_REPORT`,
  `RR_DISPLAY_REPORT` (must pass `perf_page_type` NOT IN ('', 'NA')), `RR_DISPLAY_REPORT` (group by `perf_ad_unit` for ad-unit, `perf_hour` for hourly),
  `DISPLAY_INVENTORY_CAMPAIGNS_REPORT` (slot competition),
  `RR_PLA_REPORT` (PLA) / `RR_DISPLAY_REPORT` (Display), and `DISPLAY_QUADRANT_REPORT`. Take the Display
  branch at STEP 3-RR / 3-BUDGET / 4-IR when `affected_program = "display"`.

## Final Report

Write:

```
BU Analysis Summary | Severity: HIGH/MEDIUM/LOW | Period: [dates]
Broken Layer: [Requests/RR/IR/CTR/CPC] | Root Cause: [description] | Programs: PLA/Display/Both
Key Findings: [numbered, include the ABSOLUTE BU%]
Tables (ACTUAL values, never "N/A"):
- Page Types | Categories | Campaigns (as investigated)
- Merchants — highest spenders FIRST: name | Client ID | Status | Baseline Spend |
  Current Spend | Baseline Impr | Current Impr | Baseline Spend Share% |
  Current Spend Share% | Contribution to Spend Δ% | Cumulative Spend Share%
Recommendations: [actions]
Cross-References: [other agents' findings]
```
