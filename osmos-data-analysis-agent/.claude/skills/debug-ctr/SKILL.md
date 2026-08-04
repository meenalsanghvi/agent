---
name: debug-ctr
description: >-
  Debug a week-over-week CTR (click-through rate) change for an OnlineSales
  marketplace. Use when the user asks why CTR rose, fell, dropped, or changed for
  a marketplace / agency over a period, or to investigate a CTR issue flagged in
  the weekly report. Decomposes the move into clicks vs impressions, classifies it
  (impression dilution / engagement decline / volume decline), and gates on I/R
  (are our responses rendering as impressions). Not for ROI/ROAS (use debug-roas),
  CPC (use debug-cpc), budget utilisation (use debug-bu), response rate (use
  debug-rr), or single-campaign deep-dives (use debug-campaign).
---

# Debugging a CTR change

> **Every data call below is `run_report(reportType=…, attributes=[…], metrics=[…], dateRanges=[…], filters=[…])`** against the report named at each step. Report groups are discoverable via the `get_<group>s_reports` tools. Resolve exact column names via `knowledge/tool-map.md` — never from memory.

You are debugging a CTR move for an OnlineSales marketplace. **Read
`references/common-rules.md` first** — context setup, date handling, PLA-vs-Display
rules, the checkpoint model, the pre-summary checkpoint, the final-report
contents, output rules, and the PLA competition check all live there. Also pull
`marketplace_client_id` and `timezone` from context — several CTR tools need them.

**CTR = (Clicks ÷ Impressions) × 100.**

## Core principle — decompose first

**ALWAYS decompose a CTR change into clicks vs impressions before any
conclusion.** A CTR drop from impressions doubling (clicks up 70%) is a completely
different story from impressions flat with clicks halving. Every breakdown runs in
COMPARISON mode; lead with the merchants/keywords/categories driving the move by
contribution, always shown with the RAW baseline & current numbers.

If the user asks something specific, skip the SOP and call the matching tool.

## SOP — default investigation flow

This is a **menu of steps the user walks through with you**, not a script to run.
Per `common-rules.md`: every branch below is a question, every step ends the turn,
and the scope the user set — program, category, campaign — is the only one you touch.

**A branch is several sub-steps, not one.** Each fetch that produces a choice is a
checkpoint: present what came back, then let the user narrow before drilling further.
Do not run a whole chain in one turn just because you already hold the inputs.

### STEP 1 — Triage
`MERCHANT_PERFORMANCE_REPORT` in COMPARISON mode, filtered to the program the user
chose (`perf_channel`) → current+baseline clicks/impressions/CTR/spend, and the
per-merchant contribution you need later. Aggregate it for the marketplace total.

**Do NOT use `CTR_OVERALL_REPORT` for a program-scoped figure.** It reads a
multi-channel table and exposes no channel column, so its totals blend PLA and
Display with no way to separate them. Use it only when the user genuinely wants the
blended marketplace total, and say that is what it is.

Decompose clicks vs impressions before any classification.

### STEP 2 — Classify, then ASK which branch

Work out which scenario the triage data fits, **say so with the numbers behind it**
— then ask the user which branch to take. **Do not route yourself into a STEP 3.**

- **Scenario A — Impression Dilution:** impressions rose > 5%, clicks didn't keep
  pace → STEP 3-A
- **Scenario B — Engagement Decline:** clicks fell > 2%, impressions stable or
  slightly changed → STEP 3-B
- **Scenario C — Volume Decline:** clicks and impressions dropped proportionally,
  CTR change < 2% → STEP 3-C

Put these to the user with `AskUserQuestion`, marking your recommendation and the
evidence for it. Always offer a way out — a different cut, or stop here.

The thresholds are guides, not verdicts. When the numbers sit near a boundary (or
fit two scenarios), say so plainly rather than forcing one, and let the user pick.

**IMPRESSION-DRIVEN GATE (distinctive to CTR):** whenever impressions moved (up OR
down), you MUST run `PAGE_PERFORMANCE_PLA_REPORT` in COMPARISON mode and read **I/R**
(`ir` = impressions ÷ responses, pre vs post) — I/R is how many of our ad responses
actually rendered as impressions.

**The gate terminates on impression direction, not on I/R alone.** CTR is
clicks ÷ impressions, so which way impressions moved decides whether they can explain
the CTR change at all:

- **Impressions ROSE and I/R dropped** → the rise is not reaching users as
  impressions; a client-side serving/rendering issue, **not within our control**.
  **STOP and RAISE TO CLIENT:** report I/R fell [baseline]→[current]. Do NOT proceed
  to merchant/keyword analysis.
- **Impressions ROSE and I/R increased / held** → serving pipeline healthy, the rise
  is real and is diluting CTR. Go forward (page → merchant → keyword).
- **Impressions FELL** → they cannot be the CTR cause. A smaller denominator *raises*
  CTR, so a CTR decline alongside falling impressions means clicks fell faster, and
  the cause is on the **clicks** side. If I/R also dropped, that is a real client-side
  finding — report it separately as an impression/spend issue, **not** as the CTR
  diagnosis — and continue to the clicks side regardless.

Never report a rendering issue as the CTR cause when impressions fell.

At this checkpoint the ONLY options are: (1) Analyze page-level performance, or
(2) Analyze merchant-level breakdown. **Do NOT offer search-query analysis here** —
that needs page-level data first to confirm the search page is affected.

### STEP 3-A — Impression dilution
`PAGE_PERFORMANCE_PLA_REPORT` (comparison). Apply the I/R gate per page using
`ir_change` — **with the direction rule from STEP 2**: impressions rose + I/R dropped
→ raise to client and stop; impressions rose + I/R held → continue; impressions fell
→ report I/R separately and continue to the clicks side. Then: impression share
shifted to low-CTR pages → mix
effect; new page type with high impressions + low CTR → new inventory diluting;
all pages similar → systemic (→ STEP 4). Checkpoint if multiple pages affected.
- **SEARCH page CTR drop (PLA):** `INTERNAL_SEARCH_QUERY_PERF_REPORT` (comparison,
  `sort_by="impressions"`) → top keywords by impressions with CTR change; find
  keywords where impressions rose but CTR dropped. `INTERNAL_SEARCH_QUERY_PERF_REPORT`
  for those keywords → which new sellers appeared with low CTR, dragging keyword
  CTR down. Report keyword, baseline vs current CTR, new sellers vs keyword avg.
- **NON-SEARCH page (category/product) CTR drop (PLA):** `get_category_level_
  performance` (`category_level="l1"`, + baseline) → which L1 categories gained
  low-CTR impressions (read `ctr_change` + `contribution_to_impressions_change`).
  Drill **progressively** into the dominant child: L1 → (`category_l1_filter`,
  l2) → (`+category_l2_filter`, l3). Report category at the level you stopped,
  baseline vs current CTR, impressions change%.
- `AUDIT_EVENTS_REPORT` (must pass `perf_action_type_id` = 16) → new low-quality campaigns activated?

### STEP 3-B — Engagement decline
`PAGE_PERFORMANCE_PLA_REPORT` (current + baseline). Search CTR drop → keyword/bid
changes; category → relevance; product page → creative/positioning. Checkpoint if
multiple pages.
- **SEARCH page (PLA):** `INTERNAL_SEARCH_QUERY_PERF_REPORT` (comparison,
  `sort_by="impressions"`) → keywords where clicks didn't keep pace / dropped.
  `INTERNAL_SEARCH_QUERY_PERF_REPORT` → which sellers lost CTR; new low-CTR sellers
  dragging the keyword. Report keyword, CTR pre/post, auto-vs-manual split,
  new/churned sellers + each seller's contribution. **If clicks fell because we
  lost position, that points OUTWARD** — competition is a possible cause; note it,
  and STEP 4.5 OFFERS a competition check (only on user request). (New-low-CTR-
  seller dilution is a marketplace mix shift, distinct from our campaign being
  outbid.)
- **NON-SEARCH page (PLA):** `CATEGORY_PERFORMANCE_REPORT` (l1, + baseline) →
  which L1 categories lost CTR (clicks falling vs impressions). Drill
  progressively to L3; `group_by_merchant=True` at any level to see which
  merchants drive the decline. Report category, CTR pre/post, clicks% vs
  impressions%.
- `SKU_PERFORMANCE_REPORT` (comparison, if merchant-concentrated) → ranks
  SKUs by contribution to the impressions change, with `status` + `ctr change` →
  which products losing clicks. `AUDIT_EVENTS_REPORT` (must pass `perf_action_type_id` IN (50, 51)) → new SKUs with no
  clicks / removed high-CTR products. `AUDIT_EVENTS_REPORT` (must pass `perf_action_type_id` = 16) → rule out
  pauses.

### STEP 3-C — Volume decline
CHECKPOINT: "CTR stable (< 2% change). Both clicks and impressions dropped. Root
cause is volume/traffic, not CTR. Investigate further or redirect to BU/RR?"
- User wants CTR → page-level, then STEP 4.
- User wants redirect → `HANDOFF_TO_ROOT: Volume decline, CTR stable. User wants
  [BU/RR].`

### STEP 4 — Merchants
`MERCHANT_PERFORMANCE_REPORT` (comparison). **MANDATORY checkpoint — lead with the
high-impact spenders, then report ALL of these every time, even if empty:**
- `high_impact_merchants` (Pareto — highest CURRENT spenders, ~80% cumulative,
  with `cumulative_spend_share_pct`) — RAW baseline & current spend, impressions,
  clicks, CTR, then change % + cumulative share.
- Top CTR-drop merchants (`active_both`) — same RAW + change-% format.
- `new_merchants_below_avg_ctr` — with their CTR vs `baseline_avg_ctr_threshold`.
- `churned_merchants_above_avg_ctr` — with their baseline CTR vs threshold.

**Never show only change %** — always include RAW baseline & current (spend,
impressions, clicks, CTR). Then pick top problem merchants (usually among the
high-impact spenders, but could be any bucket) → their `os_client_id`s for the
drill.

**Merchant drill (branch on the affected page from STEP 3):**
- **SEARCH** → `INTERNAL_KEYWORD_PERFORMANCE_REPORT` (must pass `perf_campaign_type` = 'performance' + `perf_campaign_subtype` IN (os_ads_search, smart_shopping)):
  keywords × campaign, pre/post CTR. NO rows = purely AUTO →
  `INTERNAL_SEARCH_QUERY_PERF_REPORT` instead.
- **NON-SEARCH** → `MERCHANT_CATEGORY_PERFORMANCE_REPORT`:
  categories × campaign, pre/post CTR.
- **OVERALL** → run both, then `SKU_PERFORMANCE_REPORT` if still needed.
Checkpoint if multiple merchants.

### STEP 4.5 — Competition (CONDITIONAL — only on explicit user request)
A CTR drop is competition-driven when a rival outbid OUR campaign and pushed our
ads to lower-CTR positions (the MANUAL fingerprint: we lost position/impressions).
This is a **secondary** cause for CTR — do NOT run it automatically. When the
merchant step points outward (we lost position, not engagement or seller-mix
dilution), REPORT competition as a possible cause and OFFER it at the summary.
Only on an explicit user request, and only once narrowed to ONE problem merchant:
find the driving campaign (`INTERNAL_CAMPAIGN_PERFORMANCE_REPORT` (daily also needs `perf_campaign_type` IN (PERFORMANCE, INVENTORY, OFFSITE) + group by `perf_date`)), then follow the **COMPETITION CHECK in
`references/common-rules.md`** scoped to that campaign and its problem keywords.

### STEP 5 — Summary
Follow the pre-summary checkpoint in `references/common-rules.md`. Interpretation:
- CTR drop → CPC impact (fewer clicks per impression → CPC rises).
- CTR drop + impression spike → check RR/BU.
- Before concluding a relevance issue, always check campaign status changes.

Only after the user confirms → record the finding in your summary (metric_type `ctr`;
severity by CTR drop: high >15%, medium 5–15%, low <5%; impacted entities keyed by
`client_id` `"type": "merchant"` or `"type": "page_type"`) → then write the Final
Summary below.

## Additional drill tools (beyond the linear SOP)
- `CAMPAIGN_PRODUCT_SELECTION_REPORT` — current active products; needs
  `marketplace_client_id` + `marketing_campaign_id` (resolve a
  `marketing_campaign_group_id` via `CAMPAIGN_LOOKUP_REPORT` first).
- `MERCHANT_LOOKUP_REPORT` — convert `client_id` ↔ `merchant_id`.
- `CAMPAIGN_LOOKUP_REPORT` — call when the user gives a campaign ID, **but FIRST ask which
  ID type it is** (`marketing_campaign_id` / `marketing_campaign_group_id` /
  `campaign_id` / `campaign_group_id`); do NOT guess. Then
  `CAMPAIGN_LOOKUP_REPORT` — it errors without a
  valid `id_type` and returns all 4 resolved IDs.

## Available drills by program — a menu, not a checklist

**This is not a coverage list.** Run only the program the user chose, and only the
drills they pick. Nothing here is owed to them by default. If a drill from the other
program would genuinely change the diagnosis, say so in one line and let the user
decide — do not run it to find out.
- **PLA + Display — how program scoping works, report by report:**
  - `MERCHANT_PERFORMANCE_REPORT` reads a multi-channel table and is the ONLY report
    here that takes a program filter. Pass `perf_channel`.
  - The PLA- and Display-specific reports are already scoped by their source table.
    Do NOT pass any program filter to them.
  - `CTR_OVERALL_REPORT` is marketplace-total and **program-blended**. It cannot be
    scoped at all.
  - For Display ad-unit detail use `DISPLAY_AD_UNIT_PERFORMANCE_REPORT` — ONLY when
    `affected_program = "display"`.
- **PLA only:** search-query / keyword-seller drills, category drill, SKU-level
  CTR, merchant keyword/category drills, and the competition check.

## Final Summary

Write:

```
CTR Analysis Summary | Severity: HIGH/MEDIUM/LOW | Period: [dates]
Scenario: [A/B/C]
Root Cause: [description] | Programs: PLA/Display/Both
Key Findings: [numbered, always show clicks AND impressions decomposition]
Tables (ACTUAL values):
- Page Types: page_type | Baseline CTR | Current CTR | CTR Change |
  Impressions Change% | Clicks Change% | I/R (baseline→current, if impressions
  drove the change)
- Keywords (if search page investigated): search_query | Baseline CTR |
  Current CTR | CTR Change | Impressions Change% | Auto vs Manual Split |
  New Sellers (below avg CTR)
- Merchants (if investigated) — highest spenders FIRST: name | Client ID |
  Baseline Spend | Current Spend | Baseline Impr | Current Impr | Baseline Clicks |
  Current Clicks | Baseline CTR | Current CTR | CTR Change | Impressions Change% |
  Clicks Change% | Baseline Impr Share% | Current Impr Share% |
  Cumulative Spend Share%  (show RAW baseline & current, not only change %)
Recommendations: [actions]
Cross-References: [other agents' findings]
```
