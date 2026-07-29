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

You are debugging a BU move for an OnlineSales marketplace. **Read
`references/common-rules.md` first** — context setup, date handling, PLA-vs-Display
rules, the checkpoint model, the pre-summary checkpoint, the store-findings
contract, and output rules. Also pull `marketplace_client_id`, `region`, and
`timezone` from context — several BU tools need them.

## ⚠️ Data-retention gate — check BEFORE every call to these tools

Some tools query raw request tables with limited retention. Before calling one,
compute `days = (end_date − start_date + 1)`. If it exceeds the limit, STOP, warn
the user, and wait for confirmation:
- `get_category_request_volume`, `get_filter_presence_response_rates` →
  15-day limit (`get_filter_presence_response_rates` always uses the recent 14 days).
- `get_category_quadrant_performance` / `get_display_quadrant_performance` →
  7-day limit.

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
- `get_true_bu_campaign_data`'s `daily_budget` is the **SUM over the queried
  range** (i.e. total budget for the period), NOT one day's budget — divide by the
  number of days for the actual daily budget.
- When reporting, always say which: "daily budget of X" vs "total budget of X over
  N days". Never just "budget".

**Comparison mode:** most BU tools return SINGLE-period data — call them for both
periods in parallel and compute changes yourself. EXCEPTION (preferred):
`get_merchant_bu_breakdown` supports comparison mode (pass baseline dates) →
merchants ranked by contribution to the marketplace SPEND change (the BU driver)
with status, spend share both periods, `pre_period_top_contributors`,
`new_merchants`. Report contribution %s, not raw spend alone.

## Semantic patterns (what the user means)
The request report has **no campaign IDs** — resolve a campaign to its categories
first:
- **"RR / low BU / underspend for campaign X"** → `lookup_campaign` →
  `get_campaign_performance` (spend, budget, clicks, impressions) +
  `get_campaign_product_selection` → extract distinct `category_l1/l2/l3` →
  `get_category_response_rates` with **all available category levels together**
  (don't drop levels). Add `get_category_quadrant_performance` (⚠️ 7-day) only if
  BU%/campaign counts are also needed.
- **"analysis for categories targeted by [campaigns]"** → `lookup_campaign` →
  `get_campaign_product_selection` (parallel) → extract categories →
  `get_response_rate_by_dimension` with `group_by_column` + those category filters.
  Steps must complete in order.
- **"what categories does campaign X target?"** → `lookup_campaign` →
  `get_campaign_product_selection` → list distinct categories.
- **"which campaigns are active for this keyword/category?"** →
  `get_search_query_campaigns` or `get_campaigns_in_category`.
- Never filter `get_response_rate_by_dimension` by campaign ID — it returns 0.

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
Call in ONE parallel turn: `check_requests`, `get_true_bu_campaign_data`,
`check_program_spend`. If baseline dates exist, call all three for baseline too
(6 calls). Then **present the available group-by dimensions** and ask which to
group by: `page_type`, `store_id`, `network`, `category_l1/l2/l3/l4/l5`, `device`.
**STOP — wait for the user's choice.** Then call `get_response_rate_by_dimension`
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
- **network** → if a campaign is in scope, `get_campaign_targeted_networks` first
  to confirm it targets those networks (else marketplace-wide noise). Check for an
  RR **CEILING**: `get_response_rate_by_dimension(group_by_column="category_l1",
  network_filter=<low-RR network>)` per network (parallel). RR ≥ 95% in a
  network×category combo → ceiling (no headroom; report and stop unless partial). No combos near 100%
  → not a ceiling → 2C.
- **store_id** → `get_store_level_rr_buckets` (session dates; `page_type_filter`)
  for hourly eligibility. `has_store_eligibility_issue = True` → specific stores
  ineligible; report and stop.
- **device** → likely no eligible SKUs / no campaigns targeting the device;
  confirm via `get_campaign_performance`.
- **category_l1/l2/l3** → `get_category_response_rates`; add
  `get_category_quadrant_performance` (⚠️ 7-day) if BU%/spend also needed.
- Any other dimension → interpret what near-0 RR means (no targeting / no eligible
  products / config gap), report, and ask before 2C.

**2C — Classify the signal:** requests dropped → 3-REQUESTS; budget increased but
spend didn't follow → 3-BUDGET; requests stable but responses dropped → 3-RR;
mixed → requests first, then budget; both stable → 3-RR.

### STEP 3-REQUESTS
1. Which pages lost requests (from `check_requests`)? 2. Checkpoint if multiple
pages. 3. PLA: `get_category_response_rates` (+ `get_category_quadrant_performance`
⚠️ 7-day if BU%/spend needed); Display: skip to STEP 4. 4. `get_merchant_bu_
breakdown` → concentrated or widespread? 5. Concentrated →
`get_merchant_wallet_balance` → `get_campaign_status_changes`. 6. → then **offer** STEP 6.

### STEP 3-BUDGET
Focus on `campaigns_with_budget_increase` from `get_true_bu_campaign_data`.
1. `get_merchant_wallet_balance` → `get_campaign_status_changes` for those
campaigns. 2. `check_response_rate_by_page`: search RR dropped →
`get_search_query_response_rates`; non-search RR dropped →
`get_category_response_rates`; Display → `get_display_ad_unit_performance` →
`get_display_inventory_campaigns` for problem slots; **low RR → `HANDOFF_TO_ROOT`
for the RR skill**; RR stable → low CPC / delivery issue, continue. 3. Sellers with
budget increase but flat spend → `get_category_response_rates`; category RR = 100%
→ CEILING, report and stop for those sellers. 4. `get_merchant_bu_breakdown` →
STEP 6.

### STEP 3-RR
PLA: `check_response_rate_by_page`. Display: `get_display_ad_unit_performance` →
`check_display_page_type_rr`. RR stable → STEP 4-IR. RR dropped → funnel break:
- **PLA drill:** checkpoint if both search + non-search → ask which first.
  Search → `get_search_query_response_rates` → `get_search_query_campaigns` →
  `get_campaign_status_changes`. Non-search → `get_category_response_rates` →
  `get_campaigns_in_category`. Filters suspected → `get_filter_presence_response_
  rates` (⚠️ recent 14 days): for each client filter (brands, zone, storeid,
  network, city, state, country, device) it compares RR present vs absent — a
  filter with much lower RR when PRESENT is over-narrowing eligibility.
- **Display drill:** `check_display_page_type_rr` (no limit) →
  `get_response_rate_by_dimension(program_type="display", group_by_column=
  "ad_unit")` (no limit); add `get_display_quadrant_performance` (⚠️ 7-day) if
  counts/BU% needed. Problem ad units → `get_display_inventory_campaigns` (slot
  competition; high competition = outcompeted) → yes →
  `get_campaign_status_changes` (mid-day pauses, `changed_by_type="EXTERNAL"`) →
  no pauses → `check_display_hourly_rr` (scheduling).
After the drill → `get_merchant_bu_breakdown` → then **offer** STEP 6.

### STEP 4-IR
`get_page_level_performance`; compute I/R = impressions ÷ responses per page. I/R
stable → STEP 5-CTR. I/R dropped → PLA: `get_category_response_rates` /
`get_search_query_response_rates` (no limit; + `get_category_quadrant_performance`
⚠️ 7-day if counts/BU% needed); Display: `get_display_ad_unit_performance` →
`get_display_inventory_campaigns`. → `get_merchant_bu_breakdown` → then **offer** STEP 6.

### STEP 5-CTR
`check_ctr_overall` + page-level CTR from STEP 4. CTR dropped →
`get_merchant_ctr_breakdown` → `get_campaign_status_changes` →
`get_merchant_bu_breakdown` → then **offer** STEP 6. CTR stable → `HANDOFF_TO_ROOT: All funnel
layers stable. Route to CPC skill.`

### STEP 6 — Summary
6A. `get_merchant_bu_breakdown` if not done — three segments: largest spend drops;
top budget holders with low BU%; recent budget increases with flat spend.
6B. Severity: bu% < 5% → at least MEDIUM; > 15pp drop → HIGH; 5–15pp → MEDIUM;
< 5pp → LOW.
6C. Pre-summary checkpoint (see `common-rules.md`). Once confirmed →
record the finding in your summary (metric_type `bu`; `root_cause` a BU-specific label such
as "Request Drop on Search Pages" / "Budget Expansion Outpaced Spend" /
"Network×Category Ceiling" / "Funnel Break: RR Decline"; entities `"type"` ∈
page_type / merchant / category / campaign) → then the Final Report below.

## Additional / auxiliary tools
- `get_category_request_volume` — category-level request volume (⚠️ 15-day).
- `lookup_campaign`, `get_campaign_product_selection` — the campaign→categories
  resolution used by the semantic patterns.

## Available drills by program — a menu, not a checklist

**This is not a coverage list.** Run only the program the user chose, and only the
drills they pick. Nothing here is owed to them by default. If a drill from the other
program would genuinely change the diagnosis, say so in one line and let the user
decide — do not run it to find out.
- **PLA:** the request/RR/category/search drills above.
- **Display:** its own funnel path — `get_display_ad_unit_performance`,
  `check_display_page_type_rr`, `check_display_hourly_rr`,
  `get_display_inventory_campaigns` (slot competition),
  `get_response_rate_by_dimension(program_type="display", group_by_column=
  "ad_unit")`, and `get_display_quadrant_performance` (⚠️ 7-day). Take the Display
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
