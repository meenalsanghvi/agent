---
name: debug-keyword-low-rr
description: >-
  Debug LOW Response Rate (RR) on specific keyword(s) for an OnlineSales
  marketplace. Use when the user asks why a keyword (or list of keywords) has low
  RR, isn't getting responses, or has poor fill — marketplace/supply-side, not tied
  to one advertiser's campaign delivery. PLA only; diagnoses the current period (no
  baseline needed). Checks request-volume eligibility, category mapping, active
  supply in the category, relevancy, and filter over-narrowing. Not for a keyword
  not serving inside a specific campaign / being outbid (use debug-keyword-delivery)
  or metric-level RR across pages (use debug-rr).
---

# Debugging low RR on specific keyword(s)

You are diagnosing **why specific keyword(s) have low RR** (supply-side). **Read
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
`get_campaigns_in_category` call in STEP 5 is used ONLY to confirm supply exists
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
`campaign_group_id`), then `lookup_campaign(raw_ids=[...], id_type="<confirmed>")`
and keep the `marketing_campaign_id`s.

### STEP 2 — Request-volume threshold (MUST be first)
`check_keyword_request_volume(marketplace_client_id, timezone, search_queries=[...],
end_date=<current end_date>)`. OnlineSales only creates a category mapping once a
keyword gets > 100 requests in the trailing 7 days.
- **below_threshold** → "'[kw]' has only [N] requests in the last 7 days (threshold
  > 100). No category has been created, so it cannot receive responses. Expected —
  wait for more volume or raise a ticket for a manual mapping." **STOP for those
  keywords;** continue for keywords that pass.
- **above_threshold** → then **offer** STEP 3.

### STEP 3 — Keyword's mapped categories
> ⚠️ **This step cannot be run.** No report backs the keyword→category mapping — `get_keyword_categories` was an ADK-only tool reading S3 files, and has no KAM equivalent. Tell the user the mapping is unavailable, then continue with the remaining steps — do not substitute another report for it.
`get_keyword_categories` **(UNAVAILABLE — see note above)** → categories
mapped to each keyword (L1–L8, `source`=auto/manual, `count`,
`advertisable_sku_count`). Note them — reused throughout.
- **keywords_not_found** (passed threshold but no S3 mapping) → "'[kw]' passed the
  volume threshold but has no category mapping in the S3 files. Raise a ticket to
  add a manual mapping." **STOP for those keywords.**
- Has categories → then **offer** STEP 4.

### STEP 4 — (Only if campaign IDs given) keyword categories vs campaign products
`get_campaign_product_selection(marketplace_client_id, marketing_campaign_id)` per
campaign; compare product L1/L2/L3 vs the keyword's mapped categories (STEP 3).
- **No overlap** → "Category mismatch — '[kw]' is mapped to [X,Y] but the campaign's
  products are in [A,B]. It cannot serve this keyword. Recommend adding products in
  the mapped categories OR a manual category mapping." **STOP.**
- Overlap → then **offer** STEP 5. (No campaign IDs → skip STEP 4, go to STEP 5.)

### STEP 5 — Active campaigns serving the mapped category (supply check)
For each keyword's top mapped categories (highest `count` + `advertisable_sku_
count` from STEP 3), `get_campaigns_in_category(agency_id, start/end,
category_level="l1"/"l2"/"l3", category_l*_filter=..., top_n=50)` → active campaigns
with spend, daily budget, status.
- `paused_campaigns` — flag any paused that should be running.
- `low_bu_campaigns` (spend < 50% of budget) — **POTENTIAL ROOT CAUSE**: budget
  exhaustion / under-pacing of performing campaigns; highlight.
- No active campaign in the mapped category → "No advertiser is running a campaign
  in the categories mapped to '[kw]'. The keyword has no supply-side coverage."
  **STOP.**

### STEP 6 — Products relevancy spot-check
For the top 2–3 campaigns from STEP 5, `get_campaign_product_selection` and inspect
whether their products' L1/L2/L3 truly match the keyword's mapped categories.
**Relevancy note (you cannot run the relevancy algorithms):** suggest — "Verify
these products pass our search relevancy caches/algorithms (title match, taxonomy
match, inventory availability). If they look category-aligned but aren't served,
the relevancy cache is the likely culprit — raise internally for algorithm/cache
inspection."

### STEP 7 — Filter audit (only if STEPs 5–6 didn't conclude)
`get_response_rate_by_dimension(marketplace_client_id, start_date=<end_date − 6
days>, end_date=<end_date>, program_type="pla", group_by_columns=
"f_kw,network,store_id,page_type,category_l1")`.
**CRITICAL date rule:** this MUST use a 7-day trailing window (relative to the
period end_date), NOT the full range. Interpret: requests concentrating on one
`f_kw` but low RR across many network/store/category combos → filters too
restrictive on the supply side; find combos where RR = 0 / very low despite high
requests. "On the last 7 days of '[kw]' traffic, [network=X, store_id=Y] shows [N]
requests but RR [Z]% — too many filters narrow the pool; consider relaxing
store_id / network / page_type restrictions."

### STEP 8 — Budget-exhaustion deep-dive (only if STEP 5 flagged low-BU performers)
`get_true_bu_campaign_data(...)` on the flagged campaigns to confirm spend vs budget
daily. If confirmed → "Performing campaigns [IDs] in the mapped category are
budget-exhausted (spend ≥ [X]% of budget on [N] days). Recommend budget increase OR
better pacing."

### STEP 9 — Per-advertiser not performing (win-rate → delegate)
If the keyword has acceptable overall (marketplace) metrics but a SPECIFIC
advertiser's campaign still isn't serving → `HANDOFF_TO_ROOT`: "Delegate to the
keyword-delivery skill — the keyword has marketplace-level RR, but advertiser [X]'s
campaign [Y] is not being served."

## Possible root causes (summarise in final findings)
1. Request volume < 100 → no category mapping exists.
2. No category mapping in S3 files → manual mapping needed.
3. Category mismatch with the user's campaign products.
4. No active campaigns running in the mapped category.
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
