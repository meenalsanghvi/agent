---
name: debug-cpc
description: >-
  Debug a week-over-week CPC (cost-per-click) change for an OnlineSales
  marketplace. Use when the user asks why CPC rose, increased, fell, dropped, or
  changed for a marketplace / agency over a period, or to investigate a CPC issue
  flagged in the weekly report. Contribution-first: identifies which pages,
  subtypes, merchants, campaigns, and keywords/categories drove the spend/clicks
  move, and whether it is bid-competition driven. Not for ROI/ROAS (use
  debug-roas), CTR (use debug-ctr), budget utilisation (use debug-bu), response
  rate (use debug-rr), or single-campaign deep-dives (use debug-campaign).
---

# Debugging a CPC change

> **Every data call below is `run_report(reportType=…, attributes=[…], metrics=[…], dateRanges=[…], filters=[…])`** against the report named at each step. Report groups are discoverable via the `get_<group>s_reports` tools. Resolve exact column names via `knowledge/tool-map.md` — never from memory.

You are debugging a CPC move for an OnlineSales marketplace. **Read
`references/common-rules.md` first** — one-time context setup, date handling,
PLA-vs-Display column rules, the interactive checkpoint model, the pre-summary
checkpoint, the final-report contents, and the output rules all live there.

**CPC = Total Spend ÷ Total Clicks.** The move is driven by spend and clicks —
always attribute it by CONTRIBUTION.

## Core principle — contribution-first

Answer **who/what drove the CPC move**, never raw numbers alone. Every breakdown
runs in **COMPARISON mode** (current + baseline in one call) and reports
contribution to the marketplace **spend change** and **clicks change** (entity
delta ÷ total delta). Spend-contribution is the stable driver signal;
clicks-contribution can be large when total clicks barely moved — read it with
the absolute numbers. Keep **SITE** (organic) vs **PROGRAM** (ad) distinct for
merchant/SKU, and show `attributed_cvr` vs `site_cvr` so a CPC change can be tied
to whether conversions held.

**Decomposition:** CPC up = spend up faster than clicks (bidding pressure) or
clicks down; CPC down = clicks up (efficiency) or spend down (contraction).

If the user asks something specific, skip the SOP and call the matching tool.

## SOP — default investigation flow

This is a **menu of steps the user walks through with you**, not a script to run.
Per `common-rules.md`: every branch below is a question, every step ends the turn,
and the scope the user set — program, category, campaign — is the only one you touch.

**A branch is several sub-steps, not one.** Each fetch that produces a choice is a
checkpoint: present what came back, then let the user narrow before drilling further.
Do not run a whole chain in one turn just because you already hold the inputs.

### STEP 1 — Triage (page-level)
`PAGE_PERFORMANCE_PLA_REPORT` in COMPARISON mode. Identify pages by contribution to
the spend change. For each page report the spend-mix shift using
`spend_share_baseline_pct` (pre) vs `spend_share_current_pct` (post) — plain shares
each summing to ~100% within a period — **alongside** the signed
`contribution_to_spend_change_pct` (the driver; can exceed 100% or go negative
when pages offset).

**FLOOR-PRICE CHECKPOINT (distinctive to CPC):** after presenting the page data,
**ask the user** to check the relevant floor pricing for the affected page(s) — a
floor change (up or down) directly moves CPC:
- SEARCH page affected → ask them to check the **Keyword Floors**.
- Any other page (category/product/home/…) → ask them to check the **Category
  Floors**.
Phrase it metric-agnostic — ask for the floor "CPC (or CPM, whichever the
marketplace uses)". **You have NO tool to fetch floors.** Ask the user to check
them; never imply you will fetch or check floors yourself.

If multiple pages are affected → checkpoint and ask which to investigate first.

**Next-step steering (no fixed order):** STEP 1.5 (search-query drill), STEP 2
(subtype), and STEP 3 (merchants) are all available now.
- SEARCH page dominates → the primary next step is **STEP 1.5** (the search-query
  drill); offer THAT, not a bare "drill into competition" (competition is reached
  *through* the queries).
- A NON-SEARCH page dominates → go to **STEP 3** (merchants) directly. STEP 2 is
  optional narrowing, not a prerequisite.
Run whatever the user picks — never silently substitute another step.

### STEP 1.5 — Search-driven? Go straight to the queries (marketplace-level, NO merchant needed)
When SEARCH dominates, the culprits ARE the search queries — no merchant pick
needed. `INTERNAL_SEARCH_QUERY_PERF_REPORT` MARKETPLACE-WIDE (no client/campaign
filter), COMPARISON mode, `sort_by="spend"` — rank by CURRENT spend so material,
still-running queries lead. **Never sort by `cpc_change` alone** (it floats
tiny-spend queries with huge % swings and stopped queries to the top). Lead the
table with each query's RAW current+baseline spend & CPC, its `cpc_change`, AND
`contribution_to_spend_change`, plus the AUTO-vs-manual split; show ≈10–20 rows.
Contested queries = the high-spend ones whose CPC moved most in the picked
direction. Separately flag any high-baseline-CPC query that CHURNED (current
spend ≈ 0) — a stopped high-CPC query drags the average down but is a "query
stopped" story, distinct from CPC compression on live queries.

Competition on those queries (still marketplace-level, NO merchant):
- `INTERNAL_SEARCH_QUERY_PERF_REPORT`
  → who SERVED on the query pre/post, AUTO vs manual, `new_competitors`. CPC drop
  → a new/cheaper rival pulls the average down; CPC rise → a rival bidding up.
- `INTERNAL_KEYWORD_PERFORMANCE_REPORT` →
  rivals that TARGETED the query and their bids pre/post, `new_in_post`.
Drop to merchants (STEP 3) only to attribute the query move to specific sellers,
or if the user asks for the merchant view.

### STEP 2 — Subtype buckets (OPTIONAL narrowing — not a prerequisite)
`CAMPAIGN_SUBTYPE_CPC_REPORT` (comparison, marketplace-level, PLA). Which
subtype bucket (`smart_shopping` / `os_ads_search`) drove the CPC move, by
contribution to spend change. Offer it; never force it ahead of a merchant
request. Use it INSTEAD of jumping straight to SKU.

### STEP 3 — Merchants (contribution)
`MERCHANT_PERFORMANCE_REPORT` in comparison mode. Report drivers by contribution to
the spend change (with `cpc_change`, status, PROGRAM vs SITE, attributed vs site
CVR), plus `pre_period_top_contributors`, `new_merchants`,
`new_merchants_above_avg_cpc` (new merchants above `baseline_avg_cpc_threshold` —
pushing CPC up) and `churned_merchants_below_avg_cpc` (cheap merchants that left —
their exit raised CPC). Take the top problem merchants' `os_client_id`s forward.

**MERCHANT-SCOPED GATE:** STEP 4, STEP 5, STEP 6, and
`INTERNAL_KEYWORD_PERFORMANCE_REPORT` (must pass `perf_campaign_type` = 'performance' + `perf_campaign_subtype` IN (os_ads_search, smart_shopping)) / `MERCHANT_CATEGORY_PERFORMANCE_REPORT` all
REQUIRE a merchant's `os_client_id`. Do NOT offer or run them until STEP 3 has
identified the problem merchant(s) — before then the only merchant-related option
is "rank the merchants (STEP 3)".

### STEP 4 — Category vs category-average
`CATEGORY_PERFORMANCE_REPORT` (must pass use `perf_category_l1_raw` / `_l2_raw` / `_l3_raw`) for the top problem merchants. Read each
category's verdict:
- **cpc_benign** — lower CPC, conversions held → no CPC problem.
- **competition_reduced** — category-wide CPC fell (reduced competition), merchant
  okayish.
- **merchant_cpc_concern** — merchant ROI fell with the CPC change → investigate
  (optionally STEP 5 / SKU).

### STEP 5 — Driving campaign + competition (CONDITIONAL — single merchant only)
**GATE:** run ONLY when scoped to ONE merchant (the user asked about that
merchant/campaign, or a checkpoint narrowed to one). Do NOT run it automatically
for every problem merchant — the default flow stops at merchant/category level
(STEPs 1–4). If multiple merchants are still in play, checkpoint and ask which to
drill.

**a. Find the driving campaign** — `INTERNAL_CAMPAIGN_PERFORMANCE_REPORT` (daily also needs `perf_campaign_type` IN (PERFORMANCE, INVENTORY, OFFSITE) + group by `perf_date`) → one call returns the merchant's campaigns with
current+baseline CPC/spend, `cpc_change`, status, contribution to the spend
change. Identify the driving campaign(s) by contribution; lead with raw
current+baseline numbers. (`daily=True` + `marketing_campaign_ids` for date-level
rows.)

**a2. Branch on the affected page (from STEP 1)** — every row carries
`marketing_campaign_id` + `campaign_name` + contribution to the merchant's spend
change. Carry the top-contribution row's `marketing_campaign_id` (and the
keyword/category) forward — it's the handle the competition tools take.
- **SEARCH page** → `INTERNAL_KEYWORD_PERFORMANCE_REPORT` (must pass `perf_campaign_type` = 'performance' + `perf_campaign_subtype` IN (os_ads_search, smart_shopping)):
  the merchant's targeted keywords × campaign. High-contribution keywords whose
  CPC rose are the drivers. Zoom in on the winning row:
  `INTERNAL_KEYWORD_PERFORMANCE_REPORT`
  and `INTERNAL_SEARCH_QUERY_PERF_REPORT`. NO rows → purely AUTO → use the
  search-query route in (b).
- **NON-SEARCH page** (category/home/product) →
  `MERCHANT_CATEGORY_PERFORMANCE_REPORT`: categories ×
  campaign — which category/campaign drove the move. For the competitive
  landscape (**two hops**): (1)
  `CAMPAIGNS_IN_CATEGORY_REPORT` to
  read that campaign's `category_l1/l2/l3` in the campaign-category taxonomy
  (filtering by campaign id alone returns only OUR campaign); (2) re-call
  `CAMPAIGNS_IN_CATEGORY_REPORT` with those `category_l1/l2/l3_filter` values (no
  campaign filter) → RIVAL campaigns + `new_entrants_in_period`. Do NOT feed this
  tool's `product_type` text into `category_*_filter` — different taxonomy, won't
  match.
- **OVERALL / both pages** → run both.

**b. Decide manual vs auto by FETCHING the campaign's keywords.** ALWAYS call
`CAMPAIGN_KEYWORDS_REPORT` (must pass `perf_is_negative` = 0 for targeted, = 1 for negative) FIRST, before any manual-vs-auto statement. **Never claim a Smart
Shopping (or any) campaign "has no manual/targeted keywords" as an inference from
subtype — that is a forbidden hallucination.** Smart Shopping is AUTO by default
but CAN carry manual keywords (EXACT/PHRASE/BROAD); state "no manual keywords"
ONLY if the fetch returned count = 0. Any EXACT/PHRASE/BROAD `keyword_match_type`
in the data is PROOF manual targeting exists — never contradict it.
- **targeted_keyword_count > 0 (MANUAL)** →
  `INTERNAL_KEYWORD_PERFORMANCE_REPORT` on those keywords in comparison mode (baseline
  dates + `exclude_marketing_campaign_ids=[our campaign]`) → per-rival pre/post
  cpc/cpm/spend + CTR/ROI + `campaign_creation_date` (the rival campaign's creation
  date — lets you correlate a rival's entry with when our CPC moved) + `new_in_post`.
  Compare OUR campaign vs rivals on the bid model's metric (read `bidding_strategy`
  from `CAMPAIGN_LOOKUP_REPORT`): CPC for CPC/AUTO_CPC, CPM for CPM/AUTO_CPM. A rival higher
  on that metric, or a `new_in_post` rival, = we're outbid.
- **targeted_keyword_count = 0 (AUTO, no manual keywords)** — NOT a dead end and
  NOT a reason to stop. Auto campaigns compete on the queries their products
  match; pull those from DATA (never hand-derive from product names). MANDATORY:
  1. `INTERNAL_SEARCH_QUERY_PERF_REPORT` → OUR campaign's queries pre/post ranked by
     CURRENT spend; lead with raw spend & CPC + `cpc_change` +
     `contribution_to_spend_change`; ≈10–20 rows; read the `auto_*` columns.
     Contested = high-spend queries whose CPC moved most; note high-CPC queries
     that churned.
  2. `INTERNAL_KEYWORD_PERFORMANCE_REPORT` → the competitor side:
     a `new_in_post` rival, or one whose cpc/cpm rose, on a query where OUR CPC
     rose = the competitor that bid up the auction. This is the core deduction: a
     query we won cheaply in pre stops performing in post because a rival targeted
     it at a higher bid, forcing our auto campaign's CPC up.
  3. (Corroboration) `INTERNAL_SEARCH_QUERY_PERF_REPORT` (no campaign filter) → served-on
     competition pre/post with `keyword_match_type` + `new_competitors`.
  Only after running these may you characterise the auto campaign's competition.
- **Broad / category-level bid pressure** →
  `CAMPAIGNS_IN_CATEGORY_REPORT` for the campaign's categories in comparison mode →
  per-rival pre/post cpc/cpm, `new_entrants_in_period`, `subtype_summary`.

Report whether the CPC move is bid-competition driven (rivals raised bids / new
entrants in post) vs the merchant's own bid change — citing the contested
queries/categories and the specific rival, on OUR campaign's bid model.

### STEP 6 — SKU (optional, PLA)
`SKU_PERFORMANCE_REPORT` for a specific merchant if category/subtype isn't
enough. Spend up + clicks stable → bidding pressure; clicks down + spend stable →
CTR issue (consider handing off to the **CTR skill**).

### STEP 7 — Summary
Follow the pre-summary checkpoint in `references/common-rules.md`. Only after the
user confirms → record the finding in your summary (metric_type `cpc`; severity by CPC
increase: high >15%, medium 5–15%, low <5%; impacted entities = merchants keyed by
`client_id`, `"type": "merchant"`) → then write the Final Report below.

## Additional drill tools (beyond the linear SOP)
- `AUDIT_EVENTS_REPORT` (must pass `perf_action_type_id` IN (50, 51)) — product additions/removals (audit log); needs
  `client_ids` or `marketing_campaign_ids` + timezone. Use to check whether a
  catalog change (added expensive-click SKUs / removed cheap ones) moved CPC.

## Available drills by program — a menu, not a checklist

**This is not a coverage list.** Run only the program the user chose, and only the
drills they pick. Nothing here is owed to them by default. If a drill from the other
program would genuinely change the diagnosis, say so in one line and let the user
decide — do not run it to find out.
- **PLA + Display:** `PAGE_PERFORMANCE_PLA_REPORT` and `MERCHANT_PERFORMANCE_REPORT`
  accept `program_type` — the STEP 1 triage and STEP 3 merchant breakdown work for
  both. Use the columns matching `affected_program`.
- **PLA only:** subtype buckets (STEP 2), category-vs-average (STEP 4), the STEP 5
  campaign/keyword/category competition drills, and SKU (STEP 6). There is no
  Display-specific CPC drill here — for Display, the investigation stays at
  page/merchant level.

## Final Report

Write:

```
CPC Analysis Summary | Severity: HIGH/MEDIUM/LOW | Period: [dates]
Root Cause: [description] | Programs: PLA/Display/Both
Key Findings: [numbered, actual numbers]
Tables (ACTUAL values, never "N/A"):
- Page types (triage): page type | Baseline CPC | Current CPC | CPC Change |
  Baseline Spend Share% | Current Spend Share% | Contribution to Spend Δ%
  (show pre AND post spend share, not only the signed contribution)
- Merchants — highest spenders FIRST (lead with the high_impact_merchants Pareto list):
  name | Client ID | Status | Baseline Spend | Current Spend | Baseline Clicks |
  Current Clicks | Baseline CPC | Current CPC | CPC Change | Spend Change% |
  Baseline Spend Share% | Current Spend Share% | Contribution to Spend Δ% |
  Cumulative Spend Share% | Attributed CVR vs Site CVR
  (show RAW baseline & current values, not only change %)
- Subtype buckets: subtype | CPC (cur vs base) | CPC Change |
  Baseline Spend Share% | Current Spend Share% | Contribution to Spend Δ%
- Categories (if investigated): category | Merchant CPC | Category-Avg CPC |
  Merchant GMV Share% | Merchant ROI Δ% | Verdict
Recommendations: [actions]
Cross-References: [other agents' findings]
```
