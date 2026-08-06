---
name: debug-roas
description: >-
  Debug a week-over-week ROI/ROAS change for an OnlineSales marketplace. Use
  when the user asks why ROAS or ROI dropped, fell, rose, or changed for a
  marketplace / agency over a period, or to investigate an ROI issue flagged in
  the weekly report. Contribution-first: identifies WHICH merchants/SKUs drove
  the move. Not for single-campaign deep-dives (use debug-campaign) or for pure
  CPC / CTR / Budget-Utilisation / Response-Rate issues (use those skills).
---

# Debugging an ROI / ROAS change

> **Every data call below is `run_report(reportType=…, attributes=[…], metrics=[…], dateRanges=[…], filters=[…])`** against the report named at each step. Report groups are discoverable via the `get_<group>s_reports` tools. Resolve exact column names via `knowledge/tool-map.md` — never from memory.

You are debugging an ROI/ROAS move for an OnlineSales marketplace. **Read
`references/common-rules.md` first** — it covers the one-time context setup,
date handling, PLA-vs-Display column rules, the interactive checkpoint model,
the competition check, and the final-report format that this skill relies on.

ROAS = program GMV ÷ spend.

## ⚠️ Attribution-settling gate — do this BEFORE comparing two windows

Program GMV and program orders keep **accruing after the window closes** as
attributions land. A recent window is therefore under-counted against an older
baseline, which inflates any apparent decline. Spend does not move; only the
attributed metrics do.

This was measured, not assumed: agency 105's window 2026-08-01..02 read
ZAR 11,771,087.58 / 20,792 orders, then ZAR 11,821,989.58 / 20,878 a few hours later
— **+ZAR 50,902 and +86 orders on the same query** — while the 07-25..26 baseline
returned byte-identical figures both times.

**Test it rather than assuming a settling period** (there is no documented one):

1. Fetch the current window, note `program_gmv` and `program_orders`.
2. Re-fetch the same window once more in the same session.
3. If the numbers moved, the window is **still settling**. Say so explicitly in the
   report, and state that the true decline is smaller than measured by at least the
   drift you observed.

Prefer baselines of **similar age** to the current window. If the user asks for a
2-day window against one 9 days older, that asymmetry is a real limitation of the
answer — flag it, don't bury it. Never present a decline as final when the recent
side is still moving.

## Core principle — contribution-first

Never report raw numbers alone — answer **who** drove the change. Every
breakdown runs in **COMPARISON mode** (current + baseline in one call) and
reports contribution % (entity delta ÷ marketplace delta). Keep **SITE**
(organic / whole-site) and **PROGRAM** (ad-attributed) distinct for both
revenue and orders. CVR = orders ÷ viewproducts; program `attributed_cvr` is
directly comparable to organic `site_cvr`. Use only the columns matching the
affected program (PLA or Display).

**User-intent decline signature:** spend flat + program viewproducts flat +
program GMV & attributed CVR down ⇒ the ROAS drop is lower buyer intent
(conversion), not reach or bidding.

If the user asks something specific, skip the SOP and call the matching tool
directly.

## SOP — default investigation flow

This is a **menu of steps the user walks through with you**, not a script to run.
Per `common-rules.md`: every branch below is a question, every step ends the turn,
and the scope the user set — program, category, campaign — is the only one you touch.

**A branch is several sub-steps, not one.** Each fetch that produces a choice is a
checkpoint: present what came back, then let the user narrow before drilling further.
Do not run a whole chain in one turn just because you already hold the inputs.

### STEP 1 — Triage
Pull the marketplace **GMV-attribution report** (`GMV_ATTRIBUTION_REPORT`) in
comparison mode (current + baseline dates). Read `trend_verdict` (program
attributed-CVR trend vs organic site-CVR trend) and `user_intent_diagnostic`.

### STEP 2 — Evaluate the verdict
- **market_wide_user_decline** — program AND organic conversion fell together →
  marketplace-wide buyer-demand decline, NOT our ad serving. Say so plainly;
  ad-side levers are limited. Optionally show top contributors for context, then
  recommend buyer-demand / marketplace actions (shopper demand, not ad demand).
  **Stop here.**
- **ad_system_issue** — program conversion fell faster than organic → it's ours.
  Proceed to STEP 3.
- **program_cvr_stable** — conversion held. If ROAS still fell it's spend/reach
  or GMV-per-order. If it looks spend-side (spend/CPC rising), do **not** stop at
  "spend rose" — go through STEP 3 → 4.5 to confirm on the problem merchants.
  Hand off to the CPC skill only if the CPC rise is broad/marketplace-wide
  rather than concentrated in a few merchants.
- If `user_intent_decline_suspected` = true, call it out (spend & views flat,
  conversion down).

### STEP 3 — Merchant contribution (MANDATORY checkpoint)
`MERCHANT_PERFORMANCE_REPORT` in comparison mode. Report **all** of these, every time:
- Top GMV-change drivers — each with `contribution_to_program_gmv_change_pct`,
  status (active_both / new / churned), PROGRAM vs SITE GMV/orders, attributed vs
  site CVR.
- `pre_period_top_contributors` — what happened to the baseline GMV leaders.
- `new_merchants` — who appeared.
- `new_merchants_below_avg_roi` vs `baseline_avg_roi_threshold` — new merchants
  below the baseline marketplace avg ROI (the ROI diluters).
- `churned_merchants_above_avg_roi` — high-ROI merchants that left (their exit
  dragged ROI down).

Pick the top problem merchants by |contribution| → take their `os_client_id`s
into STEP 4.

### STEP 4 — SKU drill-down (PLA only)
`SKU_PERFORMANCE_REPORT` (comparison) for those `os_client_id`s. Rank SKUs by
contribution to the GMV change; compare `attributed_cvr` vs `site_cvr`
(program-specific vs organic/intent issue at SKU level).

Optional merchant drill (one shot across all the merchant's campaigns, each row
tagged with `campaign_name`): `MERCHANT_CATEGORY_PERFORMANCE_REPORT` for the
category × campaign that moved the merchant's ROI; if the move is search-driven,
`INTERNAL_KEYWORD_PERFORMANCE_REPORT` (must pass `perf_campaign_type` = 'performance' + `perf_campaign_subtype` IN (os_ads_search, smart_shopping)) (no rows = purely AUTO → use
`INTERNAL_SEARCH_QUERY_PERF_REPORT`). Optional: `AUDIT_EVENTS_REPORT` (must pass `perf_action_type_id` IN (50, 51)) —
removed high-revenue SKUs (direct hit) / new low-margin SKUs (dilution).

### STEP 4.5 — Did CPC drive the drop?
ROAS = GMV ÷ spend, so the drop can be spend-side. On the top problem merchants,
`MERCHANT_PERFORMANCE_REPORT` (comparison) → read `cpc_change` and contribution to
the spend change, plus `new_merchants_above_avg_cpc` (new merchants whose current
CPC is above the baseline marketplace avg — the CPC-side mirror of the ROI
diluters from STEP 3).
- CPC roughly flat / down → not bid-driven; stay on the conversion side (STEP 4).
- CPC rose and drove spend up while conversion held → report the ROI drop is
  bid-driven and *could* be competitive. **Do not run the competition check
  automatically** — OFFER it as a next step at the summary. Run the
  COMPETITION CHECK (see `references/common-rules.md`) only on an explicit user
  request, and only after narrowing to ONE merchant + its driving campaign.

### STEP 5 — Summary
Follow the pre-summary checkpoint in `references/common-rules.md`. Only after the
user confirms → record the finding in your summary (metric_type `roas`; severity by ROI
drop: high >15%, medium 5–15%, low <5%; impacted entities = merchants keyed by
`client_id`, `"type": "merchant"`) → then write the Final Report below.

## Additional drill tools — a menu, not a checklist

**Not a coverage list.** Run only the program the user chose, and only the drills
they pick. Nothing here is owed to them by default. If a drill from the other
program would genuinely change the diagnosis, say so in one line and let them
decide — do not run it to find out.


Use these when the user narrows scope or a checkpoint points to them — they are
NOT mandatory steps:
- `DAILY_ORDER_TRENDS_REPORT` — daily PROGRAM (spend/orders/GMV/views/add2carts) vs
  SITE funnel; totals carry `attributed_cvr` & `site_cvr`. Useful between STEP 1
  and STEP 3 to see the shape of the decline over time.
- `CATEGORY_PERFORMANCE_REPORT` — category L1/L2/L3 performance (PLA): spend,
  impressions, clicks, CPC, CPM, CTR, program orders/revenue/ROI, site
  orders/revenue. `group_by_merchant=True` for per-merchant × category. In
  COMPARISON mode it returns per-category current+baseline + changes + contribution
  to the spend/clicks change **in ONE call — use that, not two calls.**
- `INTERNAL_CAMPAIGN_PERFORMANCE_REPORT` (aggregated: just `perf_campaign_id`; daily: also `perf_campaign_type` IN (PERFORMANCE, INVENTORY, OFFSITE) + group by `perf_date`) — campaign-level cost/orders/revenue/ROI/CPC; accepts
  `marketing_campaign_ids`, `client_ids`, or `seller_ids`. Use to narrow to a
  merchant's driving campaign (e.g. before the competition check).
- `CAMPAIGN_PRODUCT_SELECTION_REPORT` — current active products in a campaign; needs
  `marketplace_client_id` + `marketing_campaign_id`. If you only hold a
  `marketing_campaign_group_id` (e.g. from `INTERNAL_CAMPAIGN_PERFORMANCE_REPORT` (aggregated: just `perf_campaign_id`; daily: also `perf_campaign_type` IN (PERFORMANCE, INVENTORY, OFFSITE) + group by `perf_date`)), resolve it
  to a `marketing_campaign_id` via `CAMPAIGN_LOOKUP_REPORT` first.

**Display path:** `GMV_ATTRIBUTION_REPORT`, `MERCHANT_PERFORMANCE_REPORT`, and the CPC
test (`MERCHANT_PERFORMANCE_REPORT`) all accept `program_type="display"`. For
Display ad-unit detail use `DISPLAY_AD_UNIT_PERFORMANCE_REPORT` (ad-unit breakdown) —
ONLY when `affected_program = "display"`. SKU-level
(`SKU_PERFORMANCE_REPORT`) is PLA-only.

## Final Report

Write:

```
ROAS Analysis Summary | Severity: HIGH/MEDIUM/LOW | Period: [dates]
Root Cause: [description] | Programs: PLA/Display/Both
Key Findings: [numbered, actual numbers]
Tables (ACTUAL values, never "N/A"):
- Merchants — highest spenders FIRST (lead with the high_impact_merchants Pareto list):
  name | Client ID | Status | Baseline Spend | Current Spend | Baseline Program GMV |
  Current Program GMV | Baseline ROI | Current ROI | Program GMV Δ% |
  Baseline GMV Share% | Current GMV Share% | Contribution to GMV Δ% |
  Cumulative Spend Share% | Attributed CVR vs Site CVR | Site GMV Δ%
  (show RAW baseline & current values, not only change %)
Recommendations: [actions]
Cross-References: [other agents' findings]
```
