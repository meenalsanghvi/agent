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

You are debugging an RR move for an OnlineSales marketplace. **Read
`references/common-rules.md` first** — context setup, dates, PLA-vs-Display rules,
checkpoint model, pre-summary checkpoint, store-findings contract, output rules.
Also pull `marketplace_client_id`, `region`, and `timezone` from context.

## ⚠️ Data-retention gate — check BEFORE every call to these tools
Compute `days = (end − start + 1)`; if it exceeds the limit, STOP, warn, wait:
- `get_category_request_volume`, `get_filter_presence_response_rates` → 15-day
  (`get_filter_presence_response_rates` always uses the recent 14 days).
- `get_category_quadrant_performance` / `get_display_quadrant_performance` → 7-day.
Warning: "⚠️ [tool] retains only [N] days; your period is [X] days ([start]–[end])
— results cover only the recent [N] days. Adjust the range before I proceed?"

## Key concepts
- **RR = (Non-Zero Responses ÷ Requests) × 100.** A drop = fewer requests getting
  filled → impacts BU. Different page types have different RR (search typically
  higher).
- **Budget terminology** (never mix): daily budget = one day's cap; total budget =
  daily × N days; week budget = daily × 7. `get_true_bu_campaign_data`'s
  `daily_budget` is the **SUM over the range** (period total) — divide by N for the
  actual daily. Always say which you mean.

## Semantic patterns (the request report has NO campaign IDs)
- **"RR / low BU / underspend for campaign X"** → `lookup_campaign` →
  `get_campaign_performance` (+ `get_campaign_product_selection`) → extract
  `category_l1/l2/l3` → `get_category_response_rates` with **all available levels
  together** (don't drop levels). Never filter `get_response_rate_by_dimension` by
  campaign ID (returns 0).
- **"analysis for categories targeted by [campaigns]"** → `lookup_campaign` →
  `get_campaign_product_selection` (parallel) → extract categories →
  `get_response_rate_by_dimension(group_by_column, + category filters)`.
- **"what categories does campaign X target?"** → `lookup_campaign` →
  `get_campaign_product_selection` → list distinct categories.
- **"which campaigns for this keyword/category?"** → `get_search_query_campaigns`
  or `get_campaigns_in_category`.

## SOP — the default path, not an autopilot

This is a **menu of steps the user walks through with you**, not a script to run.
Per `common-rules.md`: every branch below is a question, every step ends the turn,
and the program the user chose is the only one you touch.

**A STEP 3 branch is several sub-steps, not one.** Each fetch that produces a
choice — which categories, which keywords, which campaigns — is a checkpoint.
Present what came back, then let the user narrow before you drill further. Do not
run a whole branch chain in one turn because you already hold the inputs.

### STEP 1 — Triage (parallel, 4 calls)
`check_requests` (current + baseline) + `check_response_rate_by_page` (current +
baseline). Present overall RR change + which page types are affected (returns
`search_page_affected`, `non_search_pages_affected`).

These four calls are **one** step — fetch them together, present once.

### STEP 2 — Classify, then ASK which branch

Work out which scenario the triage data fits, **say so with the numbers behind
it** — then ask the user which branch to take. **Do not route yourself into a
STEP 3.**

- **A** — `requests_change_pct` > 0 AND `response_pct_change` negative (requests
  up, responses didn't keep up) → STEP 3-A
- **B** — budget dropped (needs `get_true_bu_campaign_data`) → STEP 3-B
- **C** — requests stable + budget stable + responses dropped → STEP 3-C

Put these to the user with `AskUserQuestion`, marking your recommendation and the
evidence for it. Always offer a fourth way out — a different cut, or stop here.

If the evidence is ambiguous, say that plainly rather than forcing a scenario, and
offer the **cheapest ruling-out step first** (B is usually cheapest — one budget
call either confirms or eliminates it).

**Dimension drill-down** (`get_response_rate_by_dimension`) is available if the
user asks to segment (store_id, network, device, category_l1/l2/l3) or page-level
is inconclusive — don't force it. Call it **without** `group_by_column` first →
`available_columns` for the program_type → present and ask which. (No retention
limit; same for `get_store_level_rr_buckets`.) Follow-ups:
- **network** → if a campaign is in scope, `get_campaign_targeted_networks(client_
  id, campaign/marketing_campaign_id)` FIRST to scope to its actual targeted
  networks (skip untargeted ones). Then ceiling check:
  `get_response_rate_by_dimension(group_by_column="category_l1", network_filter=
  <network>)` per network (parallel) — RR ≥ 95% → CEILING, report/stop unless
  partial.
- **store_id** → `get_store_level_rr_buckets` (both PLA & Display via
  `program_type`; prerequisite: `get_response_rate_by_dimension(group_by_column=
  "store_id")` for PLA, or `(group_by_column="filter_store_id",
  program_type="display")` for Display, confirmed store IDs sent with some near-0
  RR). Buckets hours at store×day×hour into `zero_response` (RR < 1% — no SKUs
  available), `partial_response` (SKUs ran out mid-hour), `full_response` (100%
  fill) — summed totals across hours, NOT individual hour rows.
  `has_store_eligibility_issue = True` → ineligible stores; read
  `adjusted_rr_excluding_ineligible` (true fill for hours with inventory). Report.
- **category_l1/l2/l3** → `get_category_response_rates`.
- **device** → report the device gap; confirm via campaign data if needed.

### STEP 3-A — Requests increased
**Non-search:** `get_category_request_volume` (⚠️ 15-day) → categories with request
increases → `get_category_response_rates` (no limit); add
`get_category_quadrant_performance` (⚠️ 7-day) if campaign counts/BU% needed; BU low
→ `get_campaigns_in_category`. Filters suspected → `get_filter_presence_response_
rates` (see gate below).
**Search:** `get_search_query_response_rates` → keywords with RR drop
(`get_search_query_rr_buckets` buckets keyword RR into zero/partial/full response,
Pareto-filtered, min 50 requests — separates no-inventory keywords from partial
fill) → `get_search_query_campaigns` (`campaigns_lost`, `paused_campaigns`). Ask "Are any of
these Search-type campaigns?" — if yes, `get_campaign_targeted_keywords` for them,
then `get_search_query_response_rates(keywords_filter=those)` for their RR.
`get_campaign_status_changes` (pass `all_campaign_ids`) + `get_product_selection_
changes` (pass `all_client_ids`, SKU removals?). All active + no changes →
`get_true_bu_campaign_data`: budget up but RR down = supply gap; budget stable =
backend/eligibility issue. → then **offer** STEP 5.

### STEP 3-B — Budget dropped
`get_true_bu_campaign_data` + `get_merchant_wallet_balance` (parallel).
`check_response_rate_by_page`: RR dropped → `get_category_response_rates`; low RR →
`HANDOFF_TO_ROOT` for the RR-specific work (or continue if scoped).
`get_campaign_status_changes` for problem campaigns. → then **offer** STEP 5.

### STEP 3-C — Responses dropped
**Non-search:** `get_category_response_rates` → categories with RR decline (add
quadrant ⚠️ 7-day if counts/BU% needed; BU issues → `get_campaigns_in_category`;
filters → `get_filter_presence_response_rates`).
**Search:** `get_search_query_response_rates`
(`get_search_query_rr_buckets` for zero/partial/full keyword-RR buckets, Pareto-
filtered, min 50 requests) → `get_search_query_campaigns`
(`effective_status`, `campaigns_lost`, `paused_campaigns`) →
`get_campaign_status_changes` → `get_product_selection_changes`. All active + no
changes → `get_true_bu_campaign_data`; budget stable → backend/eligibility.
→ then **offer** STEP 5.

### STEP 4-DISPLAY — **only when Display is the chosen program**

Run this **instead of** STEP 3, never alongside it. If the user chose PLA, this
whole section is out of scope — do not run it, and do not report what it might
have shown. If they chose both, run it as a separate pass with its own
checkpoints and present the two programs separately.

`get_display_ad_unit_performance` → which ad units dropped RR.
`check_display_page_type_rr` (no limit) → `search_page_affected` (→ keyword-
targeting campaigns likely inactive) / `category_page_affected` (→ category-
targeting campaigns paused). `get_response_rate_by_dimension(program_type="display",
group_by_column="ad_unit")` (no limit); add `get_display_quadrant_performance`
(⚠️ 7-day) if counts/BU% needed. Problem ad units → `get_display_inventory_
campaigns` (competing campaigns on the slot): high competition (many campaigns,
higher bids/budgets) → outcompeted; few competitors → not competition.
`get_campaign_status_changes` (client_ids from affected ad units): check the
`change_timestamp` time (marketplace tz) for mid-day pauses, `changed_by_type=
"EXTERNAL"` = merchant-initiated — a mid-day pause on a high-volume day is the most
common Display RR cause; report and stop. No pauses → `check_display_hourly_rr`
(prerequisite met) → `adjusted_rr_active_hours`, `has_hourly_pattern`,
`ad_units_without_campaigns` → systemic eligibility/supply. → then **offer** STEP 5.

### STEP 5 — Merchants *(offer it; do not assume they want it)*

A branch ending is a checkpoint, not a cue to run this. Many tickets are answered
by the branch itself — "which ad unit dropped" rarely needs a merchant ranking.
Offer it alongside "we have the answer, write it up" and let the user choose.

`get_merchant_rr_breakdown` in comparison mode → merchants ranked by contribution
to the marketplace **impressions** change (the RR driver — fewer responses → fewer
impressions), with status, impression share both periods, `pre_period_top_
contributors`, `new_merchants`. Lead with the merchants driving the move; when
impressions barely moved, contribution %s amplify — read with absolute changes.

### STEP 6 — Summary
Pre-summary checkpoint (see `common-rules.md`). Once confirmed →
record the finding in your summary (metric_type `rr`; entities `"type"` ∈ keyword / category
/ page_type) → then the Final Report below.

## Reading tool outputs (key signals)
> ⚠️ **This step cannot be run.** No report backs the keyword→category mapping — `get_keyword_categories` was an ADK-only tool reading S3 files, and has no KAM equivalent. Tell the user the mapping is unavailable, then continue with the remaining steps — do not substitute another report for it.
- `check_requests`: `avg_response_percentage` current vs baseline; requests up + RR
  down = Scenario A.
- `check_response_rate_by_page`: `search_page_affected` → keyword drill;
  `non_search_pages_affected` → category drill.
- `get_search_query_response_rates`: focus on `top_keywords_by_volume` (Pareto
  keywords) — systemic (many keywords low) vs concentrated (a few driving it).
  `get_search_query_rr_buckets` buckets keyword RR into zero/partial/full response
  (Pareto-filtered, min 50 requests) to split no-inventory keywords from partial fill.
- `get_search_query_campaigns`: `paused=0` + no status changes → campaigns fine,
  likely backend; compare both periods to find `campaigns_lost`.
- `get_campaign_targeted_keywords`: `bidding_value` = merchant's manual bid; many
  targeted keywords at 0% RR → no inventory for those terms; check
  `negative_keywords` for accidental exclusions. **Ask "Is this a Search campaign?"
  before calling.**
- `get_campaign_targeted_networks`: low RR on a network NOT in this list → campaign
  unaffected; a targeted network missing from the request stream → no demand
  reaching it. Use BEFORE any network drill.
- `get_true_bu_campaign_data`: `campaigns_paused_count`, `budget_drop_net_lost`,
  `sellers_with_zero_spend_count`. `get_merchant_wallet_balance`: cross-ref
  `zero_balance`.
- `get_campaign_status_changes`: `changed_by_type="EXTERNAL"` = user-initiated.
  `get_product_selection_changes`: SKU removals reduce eligibility.
- `get_display_inventory_campaigns` (ad unit → campaigns): our campaign with lower
  bid/budget than competitors → outcompeted; UNKNOWN strategy / 0 daily budget →
  misconfiguration. `get_campaign_inventory_performance` (campaign → ad units):
  few slots → limited reach; high impressions but low CTR on a slot → creative/
  placement issue; zero spend on a slot → not winning that auction.
- `get_category_quadrant_performance` (⚠️ 7-day): BU < 75% → investigate campaigns;
  use `category_l1/l2/l3_filter` individually, not full paths; for RR prefer
  `get_category_response_rates` (no limit).
- `get_display_quadrant_performance` (⚠️ 7-day): low `uniq_campaigns_count` on a
  high-request slot → supply gap; low BU% → delivery/budget issue; compare periods
  to spot slots that lost campaigns; for RR prefer `get_response_rate_by_dimension(
  program_type="display")` (no limit).
- `get_campaigns_in_category` (single period): check `paused_campaigns` and
  `low_bu_campaigns`.
- `get_filter_presence_response_rates`: **ALWAYS show the filter list (brands,
  zone, storeid, network, city, state, country, device) and ask which to check
  before running.** Returns per-filter present/absent blocks (`requests`,
  `responses`, `response_rate`, `request_share_pct`) plus
  `rr_delta_present_minus_absent`. A filter with much lower RR when PRESENT
  (negative delta) is over-narrowing eligibility. Use late, after other RR causes
  are ruled out.
- `get_keyword_categories` **(UNAVAILABLE — see note above)** (PLA): categories mapped to a keyword — for "what
  categories is keyword X mapped to?".

## Available drills by program — a menu, not a checklist

**This is not a coverage list.** Run only the program the user chose, and only the
drills they pick. Nothing here is owed to them by default.

- **PLA:** request / RR / category / search / store / network drills above.
- **Display:** the STEP 4 path — `get_display_ad_unit_performance`,
  `check_display_page_type_rr`, `check_display_hourly_rr`,
  `get_display_inventory_campaigns`, `get_response_rate_by_dimension(program_type=
  "display", group_by_column="ad_unit")`, `get_display_quadrant_performance`
  (⚠️ 7-day). Note `store_id_filter` maps to `filter_store_id` for Display.

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
