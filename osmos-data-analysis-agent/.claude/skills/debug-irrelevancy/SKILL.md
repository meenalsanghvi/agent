---
name: debug-irrelevancy
description: >-
  Investigate why IRRELEVANT products are being served for search keyword(s) on an
  OnlineSales marketplace. Use when the user reports irrelevant products / wrong
  SKUs showing for a keyword in a campaign, or "product Z was shown for keyword X
  but shouldn't have been". PLA, SEARCH page only. Identifies which OnlineSales
  relevancy algorithm (cache_type) served the irrelevant SKU and whether it's a
  genuine category mismatch, expected auto/broad-match, a negative-match leak, or
  an unmapped keyword. Not for a keyword not serving / low delivery (use
  debug-keyword-delivery) or low RR (use debug-keyword-low-rr).
---

# Investigating keyword irrelevancy

You are investigating **why irrelevant products serve for a search keyword**. The
goal is to identify which OnlineSales relevancy algorithm (`cache_type`) served the
irrelevant SKU and confirm whether it's a genuine category divergence or an
algorithm-side issue. **Read `references/common-rules.md`** for STEP 0 context
setup, the checkpoint model, and output rules. Also pull `marketplace_client_id`
and `timezone`.

**Overrides:** PLA, **SEARCH page only**. This SOP ends in **conclusions + a
root-cause summary** (grouped by `cache_type`), not the standard
pre-summary / final-report flow.

## SOP

This is a **menu of steps the user walks through with you**, not a script to run.
Per `common-rules.md`: every branch below is a question, every step ends the turn,
and the scope the user set — program, category, campaign — is the only one you touch.

**A branch is several sub-steps, not one.** Each fetch that produces a choice is a
checkpoint: present what came back, then let the user narrow before drilling further.
Do not run a whole chain in one turn just because you already hold the inputs.

### STEP 1 — Inputs
- Campaign ID(s) where irrelevancy was observed (**required**).
- Keyword(s) complained about (optional — STEP 2 discovers them if absent).
- Specific product name / SKU flagged as irrelevant (optional but helpful).

### STEP 1.5 — Resolve campaign IDs (MANDATORY id-type confirmation)
ASK the id-type (`marketing_campaign_id` / `marketing_campaign_group_id` /
`campaign_id` / `campaign_group_id`) before `lookup_campaign`; don't guess/default.
Then `lookup_campaign(raw_ids=[...], id_type="<confirmed>")`; extract the
`marketing_campaign_id`s **and** note `seller_id` / `client_id` (needed in STEP 2).
If an ID fails, re-ask (type may be wrong).

### STEP 2 — Campaign's TARGETED keywords (MUST run before STEP 3)
`get_campaign_targeted_keywords(marketplace_client_id, marketing_campaign_id,
client_id)` per campaign. **SEARCH campaigns only** — confirm with the user if
ambiguous. Returns `targeted_keywords` (is_negative=0; each `(text,
bidding_value)`, `bidding_value` = merchant's manual bid, null/0 = AUTO) and
`negative_keywords` (is_negative=1). Why first:
- If the user gave a keyword, verify it's in `targeted_keywords`. If it's NOT
  targeted AND not a negative-match leak → the "irrelevancy" is expected
  auto/broad-match behavior → **call it out and STOP (no bug).**
- If no keyword given → use `targeted_keywords` as the STEP 3 candidate list.
- If the irrelevant keyword appears in `negative_keywords` but still served →
  separate bug, flag it (see STEP 5).

### STEP 3 — Keyword → category mappings
> ⚠️ **This step cannot be run.** No report backs the keyword→category mapping — `get_keyword_categories` was an ADK-only tool reading S3 files, and has no KAM equivalent. Tell the user the mapping is unavailable, then continue with the remaining steps — do not substitute another report for it.
`get_keyword_categories` **(UNAVAILABLE — see note above)** with the
user's keyword(s), or the top `targeted_keywords` from STEP 2. Returns categories
(L1–L8, `source`=auto/manual, `count`, `advertisable_sku_count`) — the **"relevant"
reference set** for STEP 5.

### STEP 4 — Actually-responded SKUs
`get_responded_skus` — `RESPONDED_SKUS_REPORT`. **Always filter on `perf_keyword`**:
kamService does not enforce the report's required filter, so an unscoped fetch runs
and never returns. Pass the investigated keyword(s) (or STEP 2's targeted keywords).

To narrow to one campaign, filter `perf_internal_campaign_id` — **not**
`perf_campaign_id`. This report keys on the INTERNAL campaign id; the id STEP 1.5
returns is the MARKETING id, and filtering with it yields **0 rows and no error**.
Get the internal id from `CAMPAIGN_LOOKUP_REPORT` (`perf_campaign_id` there), and
note the two are not 1:1 — one internal id can map to several marketing ids.

To narrow to one product, filter `perf_product_name`, `perf_brand` or
`perf_category` (exact `IN` match — there is no LIKE).

Returns per keyword + `cache_type` + SKU: product name, brand, category,
impressions, **clicks** and spend. **`cache_type` is the key signal** — it names the
algorithm that decided to serve this SKU for this keyword.

### STEP 5 — Compare and diagnose
For each (keyword, responded SKU) row, compare the SKU's category (STEP 4) against
the keyword's mapped categories (STEP 3):
- **Overlap** → NOT irrelevant at the OS mapping level; the user's perception may
  come from broader taxonomy differences. Present the overlap + `cache_type`.
- **No overlap → GENUINE MISMATCH.** Identify the `cache_type` that served it (the
  responsible algorithm): "Keyword '[kw]' is mapped to [X,Y] but SKU [sku_id]
  '[product]' (category [Z]) was served by algorithm '[cache_type]'. '[cache_type]'
  is responsible for this irrelevancy. Recommend raising internally to the
  relevancy/algorithm team with the cache_type as the entry point."
- **keywords_not_found** (no mapping in STEP 3) → no ground truth: "'[kw]' has no
  category mapping in the S3 files, so relevancy cannot be evaluated. Recommend
  adding a manual mapping and re-evaluating."
- **Negative leak** (irrelevant keyword is in `negative_keywords` but served) →
  "'[kw]' is in the campaign's negative list but still served — escalate as a
  negative-match bypass bug."

### STEP 6 — Per-advertiser summary
When multiple campaigns / keywords / SKUs are in play, **group findings by
`cache_type`** so the user sees which single algorithm is the biggest offender.

## Possible root causes (summarise in final findings)
1. Keyword NOT in `targeted_keywords` but served via broad/auto-match → expected,
   not a bug.
2. Keyword IS in `negative_keywords` but still served → negative-match bypass bug.
3. Keyword has no S3 category mapping → no ground truth; add a manual mapping.
4. Category mismatch between the keyword mapping and the responded SKU →
   algorithm-side issue; `cache_type` names the responsible algorithm.

## Available drills by program — a menu, not a checklist

**This is not a coverage list.** Run only the program the user chose, and only the
drills they pick. Nothing here is owed to them by default. If a drill from the other
program would genuinely change the diagnosis, say so in one line and let the user
decide — do not run it to find out.
**PLA, SEARCH page only.**
