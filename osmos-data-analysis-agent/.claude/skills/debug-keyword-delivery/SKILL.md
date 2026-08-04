---
name: debug-keyword-delivery
description: >-
  Debug a targeted-keyword delivery problem INSIDE a specific advertiser campaign
  for an OnlineSales marketplace. Use when the user says a keyword is not serving /
  not performing / stopped / regressed in their campaign, or has low delivery /
  dropped impressions / is being outbid by competitors. PLA only. Validates the
  keyword campaign-scoped, checks request-volume eligibility, checks keyword↔product
  category alignment, then analyses competition. Not for low RR on a keyword
  marketplace-wide (use debug-keyword-low-rr) or metric-level ROI/CPC/CTR/RR/BU
  questions (use those skills).
---

# Debugging targeted-keyword delivery in a campaign

> **Every data call below is `run_report(reportType=…, attributes=[…], metrics=[…], dateRanges=[…], filters=[…])`** against the report named at each step. Report groups are discoverable via the `get_<group>s_reports` tools. Resolve exact column names via `knowledge/tool-map.md` — never from memory.

You are debugging why a **targeted keyword isn't performing inside the user's
specific campaign** (either "not serving / regressed" or "low delivery / being
outbid"). **Read `references/common-rules.md`** for STEP 0 context setup, dates,
the checkpoint model, and output rules. Also pull `marketplace_client_id` and
`timezone` from context.

**Overrides vs the shared rules:** PLA only. This SOP ends in a **diagnosis /
ticket recommendation**, not the standard summary — there is no mandatory
pre-summary checkpoint / final-report table (you may note
findings if useful).

## SOP

This is a **menu of steps the user walks through with you**, not a script to run.
Per `common-rules.md`: every branch below is a question, every step ends the turn,
and the scope the user set — program, category, campaign — is the only one you touch.

**A branch is several sub-steps, not one.** Each fetch that produces a choice is a
checkpoint: present what came back, then let the user narrow before drilling further.
Do not run a whole chain in one turn just because you already hold the inputs.

### STEP 1 — Inputs
Ask: which keyword(s) aren't performing, and which campaign(s) they're expected to
perform in.

### STEP 1.5 — Resolve campaign IDs (MANDATORY id-type confirmation)
Before `CAMPAIGN_LOOKUP_REPORT`, ASK which ID type the IDs are: "Is [ID] a
`marketing_campaign_id`, `marketing_campaign_group_id`, `campaign_id`, or
`campaign_group_id`?" Do NOT guess/default — the tool errors without `id_type`.
Then `CAMPAIGN_LOOKUP_REPORT`; extract the
`marketing_campaign_id`s (what downstream tools need). If any ID fails, the result
carries `id_type` — re-ask whether the type was wrong.

### STEP 2 — Validate the keyword INSIDE the user's campaign(s)
The complaint is always "this keyword isn't performing in MY campaign X" — validate
**campaign-scoped**, not marketplace-wide. Call
`INTERNAL_KEYWORD_PERFORMANCE_REPORT` **twice in parallel** (current +
baseline), passing BOTH `client_ids` AND `marketing_campaign_ids` from STEP 1.5
(it errors without `client_ids` — `marketing_campaign_id` is per-client). Sources
from `os_ads_keyword_performance_report` (the advertiser's TARGETED keyword report,
distinct from search-query data). Returns per-keyword spend, impressions, CTR, CPM,
attributed sales, ROI within the user's campaigns.

Optional zoom-out: `INTERNAL_KEYWORD_PERFORMANCE_REPORT` (must pass `perf_campaign_type` = 'performance' + `perf_campaign_subtype` IN (os_ads_search, smart_shopping)) = ALL the merchant's targeted keywords across ALL its
PLA campaigns (keyword × campaign_name × match_type), ranked by spend — shows where
the keyword sits among the merchant's top performers and whether other campaigns are
serving it; also the auto-vs-manual gate (NO rows = purely AUTO → search-query
route). `MERCHANT_CATEGORY_PERFORMANCE_REPORT` = the same by category × campaign.

**Interpret:**
- Zero data in BOTH periods in the user's campaign(s) → the campaign never served
  this keyword → then **offer** STEP 3.
- Data in baseline but not current → regression → then **offer** STEP 3.
- Impressions in the campaign but very low CTR / zero clicks → served but not
  engaging → then **offer** STEP 4.
- Performing fine in the current period (healthy impressions/clicks/ROI) →
  **INVALID REQUEST.** Tell the user "'[kw]' is performing normally inside campaign
  [ID] — [numbers]. This doesn't appear to be a delivery issue." **STOP.**

### STEP 3 — Request-volume threshold
`SEARCH_QUERY_REQUESTS_PLA_REPORT` (must pass request `perf_days_with_requests`) with the keyword(s) + the current period's
`end_date` → does the keyword have > 100 requests in the trailing 7 days?
OnlineSales only creates a category mapping for a keyword above that threshold; below
it, no category exists and it can't receive responses.
- **below_threshold** → "Keyword lacks request volume (needs > 100 in 7 days, has
  [N]). No category has been created for it, so it cannot receive responses. This
  is expected — it needs more search traffic to become eligible." (conclude)
- **above_threshold** → issue is elsewhere → then **offer** STEP 4.

### STEP 4 — Category alignment
> ⚠️ The keyword's **mapped** categories are unavailable — `get_keyword_categories` was
> an ADK-only tool reading S3 files with no KAM equivalent. There is no ground-truth
> mapping to compare against, so this step tests alignment from the campaign side only.
> Say that plainly; do not substitute another report for the mapping.

`CAMPAIGN_PRODUCT_SELECTION_REPORT` — the
campaign's currently selected products with `category_l1/l2/l3` and `product_name`.

### STEP 5 — Judge alignment from the campaign side
Build **P** = the campaign's unique product categories (L1/L2/L3). Then two checks:

a) **Does the keyword string appear in any `product_name`?** (case-insensitive
   substring, and its obvious variants).
b) **Is the keyword serving at all?** `INTERNAL_KEYWORD_PERFORMANCE_REPORT` (must pass `perf_campaign_type` = 'performance' + `perf_campaign_subtype` IN (os_ads_search, smart_shopping)) — per-keyword
   impressions/clicks/spend with `keyword_match_type`. Impressions > 0 means it is
   eligible and serving; 0 with the keyword present means eligible but never won.

Verdicts:
- **Serving, and the keyword appears in product names** → alignment is fine; delivery
  is not a relevance problem → PROCEED to STEP 6 (competition/bid).
- **Serving, but the keyword does not appear in any product name** → it is matching
  via category or a relevance cache rather than the title. Note it, then PROCEED to
  STEP 6 — this is normal for broad/auto matching, not a bug on its own.
- **Not serving, and the keyword appears in product names** → the products look
  relevant yet nothing serves. **RAISE TO ENGINEERING**: "Keyword [K] appears in
  product name(s) [...] in campaign [id], yet `RESPONDED_SKUS_REPORT` returns no rows —
  suspected eligibility or serving issue." **STOP** (root cause).
- **Not serving, and no product name or category plausibly relates to the keyword** →
  the campaign genuinely has nothing relevant to serve. Recommend adding relevant
  products, or removing the keyword. **STOP** (root cause).

State in the report that the keyword→category mapping check was **skipped** because the
mapping is unavailable, so a mis-mapping cannot be confirmed or ruled out here.

### STEP 6 — Competition analysis (run ALL THREE views)
**6a. Search-query Share of Voice** — `SEARCH_QUERY_MATCH_PERFORMANCE_REPORT`.
- `sov` = user's campaign impressions for the query ÷ total impressions for that
  query across ALL advertisers × 100. Low = others won the auctions.
- `top_search_impressions_share` = % of OUR OWN impressions in a top-of-search slot
  (a within-campaign placement metric, NOT a competitive share).
- Cues: LOW sov + LOW top-share → hard outbidding → 6b; LOW sov + HIGH top-share →
  bid pacing / budget exhaustion capping entries (not quality); HIGH sov + LOW
  top-share → quality/relevance issue; HIGH sov + HIGH top-share → competition is
  NOT the cause (re-check categories/status/product selection).

**6b. Competitor-campaign view** — `INTERNAL_KEYWORD_PERFORMANCE_REPORT` in
COMPARISON mode → every rival that MANUALLY targets the keyword, current vs baseline
spend/impressions/clicks/CPC/CPM + changes + status + contribution + `campaign_name`
+ `effective_status` + `campaign_creation_date` + `new_in_post`. Sort rivals by
impressions DESC; identify the top 3–5 capturing traffic. Compare vs the user's
campaign on the RIGHT bid metric (read `bidding_strategy` from `CAMPAIGN_LOOKUP_REPORT`:
CPC/AUTO_CPC → CPC; CPM/AUTO_CPM → CPM — CPC is meaningless for a CPM-bid campaign).
Higher rival value = outbid. Prioritise `new_in_post`, `new_entrants_in_period`
(campaigns created in the window), and any rival whose cpc/cpm rose; report each
rival WITH its contribution to the spend change. Cross-reference timing: our decline
start date D vs a rival created on/just before D.

**6c. Served-on competition (REQUIRED — do NOT skip)** — 6b only shows MANUAL
targeters; a Smart Shopping / AUTO rival winning via auto-matching has no manual
bid and won't appear there. `INTERNAL_SEARCH_QUERY_PERF_REPORT` MARKETPLACE-WIDE (no `marketing_campaign_ids`)
→ every rival that SERVED on the query pre/post, with `keyword_match_type` (AUTO vs
EXACT/PHRASE/BROAD) and `new_competitors`. A new AUTO competitor at a higher
effective cpc/cpm is bid pressure 6b cannot see. Compare on OUR bid model.

**Conclusion (combine 6a+6b+6c):** "'[kw]' captured [sov]% SOV across [N] matched
queries (only [X]% top-of-search). [Rival] (created [date]) is winning
[impressions] at [CPC/CPM matching the bid model], vs the user's campaign [ID] at
[our CPC/CPM]. The combination of [low SOV / new competitor on D / higher rival
bids] is consistent with the decline."

If no competitors AND SOV high but still underperforming →
`AUDIT_EVENTS_REPORT` (must pass `perf_action_type_id` = 16) on the user's campaign (recent pause/edit) + suggest
checking product stock in the overlapping categories.

## Available drills by program — a menu, not a checklist

**This is not a coverage list.** Run only the program the user chose, and only the
drills they pick. Nothing here is owed to them by default. If a drill from the other
program would genuinely change the diagnosis, say so in one line and let the user
decide — do not run it to find out.
**PLA only.**
