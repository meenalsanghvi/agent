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

> **Every data call below is `run_report(reportType=…, attributes=[…], metrics=[…], dateRanges=[…], filters=[…])`** against the report named at each step. Report groups are discoverable via the `get_<group>s_reports` tools. Resolve exact column names via `knowledge/tool-map.md` — never from memory.

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
`campaign_id` / `campaign_group_id`) before `CAMPAIGN_LOOKUP_REPORT`; don't guess/default.
Then `CAMPAIGN_LOOKUP_REPORT`; extract the
`marketing_campaign_id`s **and** note `seller_id` / `client_id` (needed in STEP 2).
If an ID fails, re-ask (type may be wrong).

### STEP 2 — Campaign's TARGETED keywords (MUST run before STEP 3)
`CAMPAIGN_KEYWORDS_REPORT` (must pass `perf_is_negative` = 0 for targeted, = 1 for negative) per campaign. **SEARCH campaigns only** — confirm with the user if
ambiguous. Returns `targeted_keywords` (is_negative=0; each `(text,
bidding_value)`, `bidding_value` = merchant's manual bid, null/0 = AUTO) and
`negative_keywords` (is_negative=1). Why first:
- If the user gave a keyword, verify it's in `targeted_keywords`. If it's NOT
  targeted AND not a negative-match leak → the "irrelevancy" is expected
  auto/broad-match behavior → **call it out and STOP (no bug).**
- If no keyword given → use `targeted_keywords` as the STEP 3 candidate list.
- If the irrelevant keyword appears in `negative_keywords` but still served →
  separate bug, flag it (see STEP 5).

### STEP 3 — Establish the served-category baseline
> ⚠️ The keyword's **mapped** categories are unavailable — `get_keyword_categories` was an
> ADK-only tool reading S3 files with no KAM equivalent, and no KAM report gives a PLA
> keyword→category mapping. There is therefore **no ground truth** for what a keyword
> *should* match. Say so plainly in the report; do not substitute another report for it.

Instead, judge relevance from the served set's own coherence. From STEP 4's data build:
- **D** = the distribution of `perf_category` across served SKUs, weighted by impressions.
- The **dominant** category — the one holding the large majority of impressions.

### STEP 4 — Actually-responded SKUs
`RESPONDED_SKUS_REPORT` — `RESPONDED_SKUS_REPORT`. **Always filter on `perf_keyword`**:
kamService does not enforce the report's required filter, so an unscoped fetch runs
and never returns. Pass the investigated keyword(s) (or STEP 2's targeted keywords).

To narrow to one campaign, filter `perf_internal_campaign_id` — **not**
`perf_campaign_id`. This report keys on the INTERNAL campaign id; the id STEP 1.5
returns is the MARKETING id, and filtering with it yields **0 rows and no error**.
Get the internal id from `CAMPAIGN_LOOKUP_REPORT` (`perf_internal_campaign_id` there), and
note the two are not 1:1 — one internal id can map to several marketing ids.

To narrow to one product, filter `perf_product_name`, `perf_brand` or
`perf_category` (exact `IN` match — there is no LIKE).

Returns per keyword + `cache_type` + SKU: product name, brand, category,
impressions, **clicks** and spend. **`cache_type` is the key signal** — it names the
algorithm that decided to serve this SKU for this keyword.

### STEP 5 — Diagnose from coherence, not from a mapping
Rank the served SKUs by impressions and judge each against the dominant category **and**
against the keyword string itself:

- **Coherent set** — one category holds the large majority of impressions, and the
  keyword appears in most `product_name`s → **no irrelevancy evident.** Report the
  distribution and say the complaint is not reproducible in the served data. Note that
  without the mapping this cannot be a formal verdict.
- **Outliers present** — a small number of SKUs sit outside the dominant category or
  bear no relation to the keyword by name → those are the candidates. For each, name the
  `cache_type` that served it: "Keyword '[kw]' served [N]% of impressions in [dominant
  category], but SKU [sku_id] '[product]' (category [Z]) was served by '[cache_type]'."
  Rank outliers by spend so the cost of the irrelevancy is explicit.
- **No dominant category** — impressions spread across many unrelated categories →
  broad/loose matching. Group by `cache_type` and name the algorithm carrying the most
  unrelated impressions.
- **Deliberate conquesting** — an outlier served via a targeting cache (e.g.
  `INTERNAL_TARGETED_KEYWORD_CACHE`) means an advertiser explicitly targeted this
  keyword. That is a **policy** question, not an algorithm defect — say so, with the
  spend it cost.
- **Negative leak** (the keyword is in `negative_keywords` but served) → "'[kw]' is in
  the campaign's negative list but still served — escalate as a negative-match bypass
  bug."

Always state which `cache_type`s served the outliers — that is the entry point for the
relevancy team — and state that the mapping check was skipped.

### STEP 6 — Per-advertiser summary
When multiple campaigns / keywords / SKUs are in play, **group findings by
`cache_type`** so the user sees which single algorithm is the biggest offender.

## Possible root causes (summarise in final findings)
1. Keyword NOT in `targeted_keywords` but served via broad/auto-match → expected,
   not a bug.
2. Keyword IS in `negative_keywords` but still served → negative-match bypass bug.
3. An advertiser explicitly targeted the keyword (targeting `cache_type`) → policy
   question, not an algorithm defect.
4. Served SKU sits outside the keyword's dominant served category → algorithm-side
   issue; `cache_type` names the responsible algorithm. Note this is a coherence
   judgement, not a mapping comparison — the mapping is unavailable.

## Available drills by program — a menu, not a checklist

**This is not a coverage list.** Run only the program the user chose, and only the
drills they pick. Nothing here is owed to them by default. If a drill from the other
program would genuinely change the diagnosis, say so in one line and let the user
decide — do not run it to find out.
**PLA, SEARCH page only.**
