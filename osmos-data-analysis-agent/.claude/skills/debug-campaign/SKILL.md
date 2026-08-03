---
name: debug-campaign
description: >-
  Single-campaign deep-dive for an OnlineSales marketplace. Use when the user asks
  about ONE specific campaign: low impressions, high CPC, not spending / budget
  unutilised, a targeted keyword on the campaign not spending, the campaign
  underperforming overall, or paused unexpectedly. PLA only. Confirms the campaign
  can even serve (products/wallet/budget/status) before drilling, then branches by
  complaint type. Not for marketplace-wide metric moves (use debug-roas / debug-cpc
  / debug-ctr / debug-bu / debug-rr) — hand those back.
---

# Single-campaign diagnostic

You are doing a **single-campaign deep-dive**. Entry points: low impressions, high
CPC, not spending / budget unutilised, a targeted keyword not spending, overall
underperforming, paused unexpectedly. **Read `references/common-rules.md`** for
STEP 0 context setup, the checkpoint model, output rules, and the **PLA competition
check** (invoked from 3g). Also pull `agency_id`, `marketplace_client_id`,
`currency`, `timezone`.

**Overrides:** PLA only. Single-campaign scope is inherent (the single-campaign
gate for the competition check is always met). This SOP ends in a diagnosis or a
handoff (STEP 4), not the standard summary.

> **This is a menu of steps the user walks through with you, not a script to run.**
> Per `common-rules.md`: every branch is a question, every step ends the turn, and the
> scope the user set is the only one you touch. A branch is several sub-steps —
> checkpoint between them rather than running the chain because you hold the inputs.

## STEP 1 — Inputs
Campaign ID(s); complaint type; any time window (else the auto-computed
current-vs-baseline).

## STEP 1.5 — Resolve campaign IDs (MANDATORY id-type confirmation)
ASK the id-type before `lookup_campaign`; don't guess — "Is [ID] a
`marketing_campaign_id`, `marketing_campaign_group_id`, `campaign_id`, or
`campaign_group_id`?" `lookup_campaign(raw_ids=
[...], id_type="<confirmed>")` resolves: `marketing_campaign_id` (downstream),
`client_id` (advertiser os_client_id — required by targeted-keyword tools),
`campaign_subtype`, `bidding_strategy` (CPC/CPM/AUTO_CPC/AUTO_CPM — decides
CPC-vs-CPM competitor comparison), `campaign_status`, `campaign_name`.

## STEP 1.6 — Determine subtype FROM the lookup (do NOT ask)
Read `campaign_subtype` from the lookup output — the data is authoritative (the
user may misremember).
- **OS_ADS_SEARCH ("SEARCH")** — advertiser targets keywords MANUALLY only; keyword
  rows have `keyword_match_type` ∈ BROAD/EXACT/PHRASE; no AUTO rows.
- **SMART_SHOPPING** — AUTO by default (algorithm picks products for the query);
  AUTO rows always exist, BUT the advertiser CAN add manual keywords too.

**Implication: targeted-keyword analysis applies to BOTH subtypes — do NOT skip it
for Smart Shopping.** Run the audit and let the data show whether manual keywords
exist. Brief acknowledgement is fine ("Resolved [ID] as a SEARCH campaign —
proceeding"); don't pose it as a question.

## STEP 2 — Campaign health snapshot (always)
`get_campaign_performance` (current + baseline): spend vs budget (under-pacing /
on-pace / exhausted?), impressions/clicks/CTR/CPC trend, ROI/orders trend, daily
rollup (when did it start?). Optional merchant zoom-out to see if spend/keywords
are concentrated here vs sibling campaigns: `get_merchant_keyword_performance`
(also the auto-vs-manual gate — NO rows = purely AUTO) / `get_merchant_category_
performance`.

**Network targeting — do NOT call by default, and NEVER in parallel with the
snapshot.** Not every client configures networks, so an empty result is normal.
Call `get_campaign_targeted_networks` only if the user asks about networks / where
the campaign serves; if it returns networks, scope any later network-level
diagnostic to them.

## STEP 2.5 — BASIC CHECKS (ALWAYS, before any keyword/category analysis)
Confirm the campaign can even serve — a keyword/category drill is wasted if it
can't:
- `get_campaign_product_selection` → active, in-stock products? Empty/sparse → that's
  the problem.
- `get_merchant_wallet_balance(client_ids=[advertiser os_client_id])` → wallet
  balance? Zero/near-zero → can't spend regardless of keywords.
- `get_true_bu_campaign_data` → is there budget, and is it being consumed?
- `get_campaign_status_changes` → is it ACTIVE (not paused)?

**If ANY fails, that IS the answer — report and stop; do NOT proceed to
keyword/category analysis.** Only once all pass → then **offer** STEP 3.

## STEP 3 — Branch by complaint type

**Confirm the branch before taking it.** The complaint in the ticket usually names
it, but if the wording is loose ("the campaign isn't working"), or the health
snapshot points somewhere other than what they described, **ask** with
`AskUserQuestion` rather than choosing. Run one branch; offer the others as options
at the checkpoint.

Each branch below is several sub-steps — checkpoint between them, do not run a whole
branch in one turn.

### 3a. Low impressions / high CPC (BOTH subtypes)
Common pattern: aggressive manual bids on a few keywords eat the budget at high CPC,
starving reach. `check_targeted_keyword_performance_in_campaigns(agency_id,
client_ids=[advertiser os_client_id], marketing_campaign_ids=[ID], search_queries=
[], start/end)` (`client_ids` REQUIRED) → all keywords served, per-keyword
spend/impr/clicks/CPC/CTR/ROI by `keyword_match_type` (AUTO vs BROAD/EXACT/PHRASE).
Aggregate into an AUTO-vs-MANUAL table (match_type | spend | impressions | clicks |
CPC | CTR). Interpret from the DATA (not the expected subtype):
- **AUTO + MANUAL present** → standard bid pressure; find keywords with CPC well
  above the AUTO baseline AND high spend share (top 1–3 → COMPETITION CHECK via 3g).
- **MANUAL only (typical SEARCH)** → no AUTO baseline; compare manuals against each
  other (highest CPC/spend = offenders).
- **AUTO only (Smart Shopping, no manual)** → bid-pressure narrative doesn't apply →
  go to 3b (product/pacing) and 3c (BU funnel).
Conclusion (when offenders found): "Campaign [ID] spent ₹[X] at avg CPC ₹[Y].
[table]. [K1] consumed [%] of spend at CPC ₹[Z] = [N×] the AUTO baseline. Recommend
reducing manual bid on [K1,K2] to free budget for volume."

**Search-query SOV check — REQUIRED for any low-impressions complaint.**
`get_search_query_match_performance(agency_id, client_ids, marketing_campaign_ids,
start/end)`. `sov` = our impressions for a query ÷ total across ALL advertisers ×
100 (low = others captured the query). `top_search_impressions_share` = % of OUR
own impressions in a top-of-search slot (within-campaign placement, not competitive
share). Interpret: LOW sov on high-impression queries → others winning → COMPETITION
CHECK (3g) on top low-SOV queries; LOW top-share → we land low → CPC/quality,
combine with the keyword bid table (above) to identify which keywords need bid
adjustment; Smart Shopping AUTO-only + low SOV → algorithm not matching → 3b (not a
bid issue); Smart Shopping AUTO + manual where manual rows have high SOV but AUTO
has low SOV → manual keywords are working, the algorithm is constrained (likely
catalog/eligibility), mixed bag → also check 3b; SEARCH low SOV on high-volume
queries → bids too low or outbid → 3g. Report SOV at two
levels: top-5 highest-impression queries (SOV + top-share) and the AUTO-vs-MANUAL
rollup.

### 3b. Product / catalog health (BOTH; primary for Smart-Shopping-no-manual)
`get_campaign_product_selection` (sparse selection → narrow eligibility → low
impressions); `get_product_selection_changes` (products removed in-window?);
`get_campaign_status_changes` (effective_status flip?).

### 3c. Not spending / budget unutilised (BOTH)
If the user names a SPECIFIC keyword not spending → use 3f instead.
`get_true_bu_campaign_data` (spend vs budget daily), `get_campaign_status_changes`
(pauses), `check_targeted_keyword_performance_in_campaigns` (most keywords serving
zero?). SEARCH / Smart-Shopping-with-manual mostly zero → escalate to the
keyword-delivery skill (`HANDOFF_TO_ROOT`). Smart-Shopping AUTO-only mostly zero →
product/eligibility (3b) **AND** the AUTO competition check below before concluding.

**AUTO / Smart Shopping competition check (don't skip for lack of manual
keywords).** If AUTO and STEP 2.5 basics pass, it can still fail to spend because
rivals win the auctions. Check BOTH surfaces:
- **Keyword / search query:** source spend-driving queries from
  `get_search_query_performance(marketing_campaign_ids=[campaign])` (low/zero
  presence or a drop = losing the auction), feed through
  `get_targeted_keyword_competition` (comparison, exclude our campaign).
- **Category (TWO-HOP at FULL L3):** `get_campaigns_in_category(marketing_campaign_
  ids=[campaign], category_level="l3", + baseline)` for OUR category_l1/l2/l3 and
  OUR cpc/cpm, then re-call with those `category_l*_filter` and NO campaign filter
  for RIVALS pre/post. Then you MUST do BOTH before concluding ("N new entrants"
  alone is NOT a conclusion):
  (i) **Category RR** — `get_category_response_rates(agency_id, + baseline,
  category_l*_filter, page_type)`: RR healthy/stable but spend/impr fell →
  auction-loss/outbid; RR low/dropped → eligibility/supply (relevance/catalog/
  serving), NOT a bid problem → pivot to 3b.
  (ii) **Bid comparison — PRE vs POST, OURS vs OTHERS, on cpc/cpm — NOT spend.**
  Banned non-conclusions: "we're not a top spender", "category saturated / 50+
  campaigns", "our spend is negligible". OUR cpc/cpm comes from hop (a) (always
  present even at ₹10 spend; don't look for ourselves in hop b). Table: row 1 = OUR
  campaign (baseline→current cpc/cpm), next rows = top rivals / new_entrants, on OUR
  bid model. Only rivals bidding ABOVE us in post prove we're outbid; at/below → not
  the cause, look at RR/eligibility.
  **AUTO-campaign caveat (AUTO + barely spending now):** current effective cpc/cpm
  is 0/unobservable — the auto-bidder's bid isn't in reporting. Do NOT present ₹0 as
  "our bid". State rivals are likely bidding above our auto-generated bid, and
  RECOMMEND the backend/engineering retrieve the actual auto bid to confirm. (Manual
  campaigns: configured bid is known — compare directly, don't ask the backend.)
Verdict: RR healthy AND rivals (esp. `new_in_post`) bidding higher → competitive
auction loss → recommend raising the bid. RR low → eligibility/supply, not
competition.

### 3f. A specific targeted keyword not spending
> ⚠️ **Option (a) below cannot be run.** `get_keyword_categories` was an ADK-only tool
> reading S3 files and has no KAM equivalent, so the keyword's *mapped* categories are
> unavailable. Reach the verdict from (b) and (c) instead, and say the mapping check was
> skipped — do not substitute another report for it.
Run STEP 2.5 basics first (a campaign-level block explains a zero keyword too). Then:
1. `check_requests` for the WHOLE marketplace over the LAST 7 DAYS (`program_type=
   "pla"`, no page filter) → marketplace RR (fixed trailing-7-day window, NOT the
   baseline).
2. **RR ≈ 100%** (we respond to ~every request): supply healthy, we're not winning
   the auction → COMPETITION CHECK (3g) on the keyword; ours below rivals on the bid
   metric, or a `new_in_post` rival → recommend raising the bid.
3. **RR low** (we're not responding): eligibility/relevance —
   (a) `get_keyword_categories` **(UNAVAILABLE — see note above)** (mapped categories) vs `get_campaign_product_
   selection` (products' categories): no match → category-mapping/relevance gap;
   (b) does the keyword string appear in any `product_name`?
   (c) if the keyword matches BOTH the product category AND the product name yet
   still serves zero → **RAISE TO ENGINEERING**: "Keyword [K] matches product
   category and appears in product name(s) [...], RR is low, yet serves zero —
   suspected serving bug."

### 3d. Underperforming overall
Use STEP 2's snapshot to pick the broken metric: ROI/ROAS →
`get_sku_level_performance` + `check_gmv_attribution` → `HANDOFF_TO_ROOT` to the
ROAS skill if marketplace-wide; CPC → 3a flow; CTR → `get_search_query_performance
(marketing_campaign_ids=[ID], baseline)`; BU → 3c flow.

### 3e. Paused unexpectedly
`get_campaign_status_changes(... marketing_campaign_ids=[ID])` → exact pause event
(who/when); `get_product_selection_changes` → product list emptied? If status is
ACTIVE but no impressions → escalate as a system issue.

### 3g. COMPETITION CHECK (shared — invoked from 3a / 3c / 3f)
This check is **auto-invoked by branches 3a/3c/3f — never gated on an explicit user
request** (that user-request gating is for the marketplace-metric skills like ROAS/
CTR, not this SOP). The single-campaign gate is already met; the only remaining gate
is STEP 2.5 (run only once internal causes are ruled out). The calling branch names the surface: 3a → the
high-CPC offender keywords AND low-SOV queries; 3c → the AUTO campaign's
spend-driving queries (fallback: head terms from product names if it serves almost
nothing); 3f → the single targeted keyword. Then follow the **COMPETITION CHECK in
`references/common-rules.md`**.

## STEP 4 — Handoff when scope exceeds one campaign
- Marketplace-wide RR/CTR/ROI drop across many campaigns → `HANDOFF_TO_ROOT` to the
  relevant metric skill.
- A specific keyword + campaign issue → `HANDOFF_TO_ROOT` to the keyword-delivery
  skill.

## Available drills by program — a menu, not a checklist

**This is not a coverage list.** Run only the program the user chose, and only the
drills they pick. Nothing here is owed to them by default. If a drill from the other
program would genuinely change the diagnosis, say so in one line and let the user
decide — do not run it to find out.
**PLA only.**
