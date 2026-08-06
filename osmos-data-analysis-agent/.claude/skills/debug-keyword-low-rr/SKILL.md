---
name: debug-keyword-low-rr
description: >-
  Debug LOW Response Rate (RR) on specific keyword(s) for an OnlineSales
  marketplace. Use when the user asks why a keyword (or list of keywords) has low
  RR, isn't getting responses, or has poor fill — marketplace/demand-side, not tied
  to one advertiser's campaign delivery. PLA only; diagnoses the current period (no
  baseline needed). Checks request-volume eligibility, category mapping, active
  advertiser demand in the category, relevancy, and filter over-narrowing. Not for a keyword
  not serving inside a specific campaign / being outbid (use debug-keyword-delivery)
  or metric-level RR across pages (use debug-rr).
---

# Debugging low RR on specific keyword(s)

> **Every data call below is `run_report(reportType=…, attributes=[…], metrics=[…], dateRanges=[…], filters=[…])`** against the report named at each step. Report groups are discoverable via the `get_<group>s_reports` tools. Resolve exact column names via `knowledge/tool-map.md` — never from memory.

You are diagnosing **why specific keyword(s) have low RR** (demand-side). **Read
`references/common-rules.md`** for STEP 0 context setup, the checkpoint model, and
output rules. Also pull `marketplace_client_id`, `timezone`, and `agency_id`.

**Scope & overrides:**
- **PLA only.** The user gives one keyword or a list; optionally a campaign
  context.
- **No baseline needed** — this diagnoses the current period (skip the
  current-vs-baseline date reconciliation; use the current period only).
- This SOP ends in **conclusions + a root-cause summary**, not the standard
  pre-summary / final-report flow.

## ⚠️ RR vs win-rate — do NOT chase competitor bids here
Competition / being outbid does **NOT** lower RR. **RR = responses ÷ requests =
whether WE respond to a request, not whether we WIN the auction.** A rival
outbidding us still lets us respond — we just lose the impression, which is a
**win-rate / delivery** problem, not an RR problem. **There is no competition check
in this SOP.** If the user's real concern is lost impressions/delivery despite us
responding, that's win-rate → STEP 9 (delegate to the keyword-delivery skill). The
`CAMPAIGNS_IN_CATEGORY_REPORT` call in STEP 5 is used ONLY to confirm demand exists
(active campaigns in the mapped category), never for bid competition.

## SOP

This is a **menu of steps the user walks through with you**, not a script to run.
Per `common-rules.md`: every branch below is a question, every step ends the turn,
and the scope the user set — program, category, campaign — is the only one you touch.

**A branch is several sub-steps, not one.** Each fetch that produces a choice is a
checkpoint: present what came back, then let the user narrow before drilling further.
Do not run a whole chain in one turn just because you already hold the inputs.

### STEP 1 — Inputs
Keyword(s) (required). Optional: campaign ID(s) — if given, ASK the id-type
(`marketing_campaign_id` / `marketing_campaign_group_id` / `campaign_id` /
`campaign_group_id`), then `CAMPAIGN_LOOKUP_REPORT`
and keep the `marketing_campaign_id`s.

### STEP 2 — Request-volume threshold (MUST be first)
`SEARCH_QUERY_REQUESTS_PLA_REPORT` (must pass request `perf_days_with_requests`). OnlineSales only creates a category mapping once a
keyword gets > 100 requests in the trailing 7 days.
- **below_threshold** → "'[kw]' has only [N] requests in the last 7 days (threshold
  > 100). No category has been created, so it cannot receive responses. Expected —
  wait for more volume or raise a ticket for a manual mapping." **STOP for those
  keywords;** continue for keywords that pass.
- **above_threshold** → then **offer** STEP 3.

### STEP 3 — Which categories does the keyword actually reach?
> ⚠️ The keyword's **mapped** categories are unavailable — `get_keyword_categories` was an
> ADK-only tool reading S3 files with no KAM equivalent, and no KAM report gives a PLA
> keyword→category mapping. So there is no *expected* category set to test against. Use
> the **observed** categories instead, and say clearly that a mis-mapping can be neither
> confirmed nor ruled out.

`RESPONDED_SKUS_REPORT` filtered on the keyword → the categories of SKUs that DID serve.
Call this set **O** (observed).
- **O is non-empty** → the keyword does reach inventory; low RR is a fill/demand or
  budget problem, not a mapping gap → **offer** STEP 4.
- **O is empty** (nothing served at all) → no observed coverage. Note that this is
  consistent with either a missing category mapping OR no eligible inventory, and that
  the two cannot be separated without the mapping. Continue to STEP 4 with the
  campaign's own product categories instead.

### STEP 4 — (Only if campaign IDs given) campaign products vs the keyword
`CAMPAIGN_PRODUCT_SELECTION_REPORT` per
campaign → product `category_l1/l2/l3` and `product_name`. Call this set **P**.
- **O non-empty and P ∩ O ≠ ∅** → the campaign's products are in categories the keyword
  demonstrably reaches → not a relevance problem → **offer** STEP 5.
- **O empty, and the keyword string appears in some `product_name`** → products look
  relevant yet nothing serves. Flag for engineering: "Keyword [K] appears in product
  name(s) [...] but `RESPONDED_SKUS_REPORT` returns no rows." **STOP.**
- **O empty, and the keyword relates to nothing in P by name or category** → the
  campaign has no plausibly relevant inventory. Recommend adding relevant products or
  dropping the keyword. **STOP.**

### STEP 5 — Active campaigns in those categories (demand check)
Use **O** if non-empty, otherwise **P**, as the category set to probe.
`CAMPAIGNS_IN_CATEGORY_REPORT` → active campaigns with spend, daily budget, status.
- `paused_campaigns` — flag any paused that should be running.
- `low_bu_campaigns` (spend < 50% of budget) — **POTENTIAL ROOT CAUSE**: budget
  exhaustion / under-pacing of performing campaigns; highlight.
- No active campaign in those categories → "No advertiser is running a campaign in the
  categories this keyword reaches. The keyword has no demand-side coverage." **STOP.**

### STEP 6 — Products relevancy spot-check
For the top 2–3 campaigns from STEP 5, `CAMPAIGN_PRODUCT_SELECTION_REPORT` and inspect
whether their products' L1/L2/L3 and `product_name` plausibly relate to the keyword
(there is no mapped-category set to compare against — see STEP 3).
**Relevancy note (you cannot run the relevancy algorithms):** suggest — "Verify
these products pass our search relevancy caches/algorithms (title match, taxonomy
match, inventory availability). If they look category-aligned but aren't served,
the relevancy cache is the likely culprit — raise internally for algorithm/cache
inspection."

### STEP 7 — Filter audit (only if STEPs 5–6 didn't conclude)
`RR_PLA_REPORT` (PLA) / `RR_DISPLAY_REPORT` (Display).
**CRITICAL date rule:** this MUST use a 7-day trailing window (relative to the
period end_date), NOT the full range. Interpret: requests concentrating on one
`f_kw` but low RR across many network/store/category combos → filters too
restrictive on the demand side; find combos where RR = 0 / very low despite high
requests. "On the last 7 days of '[kw]' traffic, [network=X, store_id=Y] shows [N]
requests but RR [Z]% — too many filters narrow the pool; consider relaxing
store_id / network / page_type restrictions."

### STEP 8 — Budget-exhaustion deep-dive (only if STEP 5 flagged low-BU performers)
`TRUE_BU_CAMPAIGN_REPORT` on the flagged campaigns to confirm spend vs budget
daily. If confirmed → "Performing campaigns [IDs] in the mapped category are
budget-exhausted (spend ≥ [X]% of budget on [N] days). Recommend budget increase OR
better pacing."

### STEP 9 — Per-advertiser not performing (win-rate → delegate)
If the keyword has acceptable overall (marketplace) metrics but a SPECIFIC
advertiser's campaign still isn't serving → `HANDOFF_TO_ROOT`: "Delegate to the
keyword-delivery skill — the keyword has marketplace-level RR, but advertiser [X]'s
campaign [Y] is not being served."

## Possible root causes (summarise in final findings)
1. Request volume < 100 → too little traffic to diagnose.
2. Keyword reaches no inventory at all (nothing served) — could be a missing category
   mapping or no eligible products; the two cannot be separated without the mapping,
   which is unavailable.
3. Category mismatch with the user's campaign products.
4. No active campaigns running in the categories the keyword reaches.
5. Relevancy caches/algorithms filtering out otherwise-matching products.
6. Overly restrictive filters (store_id, network, page_type).
7. Performing campaigns are budget-exhausted.
8. Specific advertiser issue → delegate to the keyword-delivery skill.

## Available drills by program — a menu, not a checklist

**This is not a coverage list.** Run only the program the user chose, and only the
drills they pick. Nothing here is owed to them by default. If a drill from the other
program would genuinely change the diagnosis, say so in one line and let the user
decide — do not run it to find out.
**PLA only.**
