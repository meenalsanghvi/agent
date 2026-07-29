# Coverage audit — `debug-keyword-low-rr` vs `KEYWORD_LOW_RR_AGENT_INSTRUCTION`

**Verdict: FAITHFUL — 0 defects.** Every SOP step, threshold, branch, stop-condition, tool nuance, and rule from the source (lines 1379–1471) is present in `SKILL.md` or `references/common-rules.md`. Interpolated blocks (`_COMMON_FIRST_STEP`, `_COMMON_CONSULTANT_BEHAVIOR`, `_COMMON_RULES_TEMPLATE`) map to the shared reference. Source is PLA-only by design (no Display path exists to port); the skill correctly does not invent store-findings / competition / cross-agent / pre-summary / program-types blocks (none are interpolated by this instruction).

**Elements audited: 34.**

| # | Source element | Destination | Status |
|---|----------------|-------------|--------|
| 1 | Persona: "You are the Keyword Low RR Agent — specialist…" | Dropped | ✅ dropped-justified (persona) |
| 2 | "PLA only" qualifier | SKILL.md (scope + Program-type completeness) | ✅ full |
| 3 | `_COMMON_FIRST_STEP` — STEP 0 one-time parallel setup + date validation + user_note + program-type confirm | common-rules.md §STEP 0 | ✅ full |
| 4 | "Also get marketplace_client_id, timezone, agency_id from context" | SKILL.md (intro, "Also pull…") | ✅ full |
| 5 | `_COMMON_CONSULTANT_BEHAVIOR` — narrowing, entity-listen, checkpoint model, date-change, discovery store | common-rules.md §Consultant behavior | ✅ full |
| 6 | SCOPE: single kw or list; optional campaign context; NO baseline (diagnoses current period) | SKILL.md §Scope & overrides | ✅ full |
| 7 | NOTE RR vs win-rate: competition/outbid does NOT lower RR; RR = responses÷requests; no competition check in this SOP | SKILL.md §RR vs win-rate | ✅ full |
| 8 | NOTE: `get_campaigns_in_category` in STEP 5 used ONLY to confirm supply, not bid competition | SKILL.md §RR vs win-rate (last sentence) | ✅ full |
| 9 | STEP 1 — keyword(s) required | SKILL.md STEP 1 | ✅ full |
| 10 | STEP 1 — optional campaign IDs: ASK id-type, `lookup_campaign(raw_ids, id_type)`, keep `marketing_campaign_id`s | SKILL.md STEP 1 | ✅ full |
| 11 | STEP 2 — `check_keyword_request_volume(marketplace_client_id, timezone, search_queries, end_date)` (MUST be first) | SKILL.md STEP 2 | ✅ full |
| 12 | STEP 2 — threshold rule: category mapping created only after >100 requests in trailing 7 days | SKILL.md STEP 2 | ✅ full |
| 13 | STEP 2 — below_threshold conclusion + STOP for those keywords, continue for passers | SKILL.md STEP 2 | ✅ full |
| 14 | STEP 2 — above_threshold → STEP 3 | SKILL.md STEP 2 | ✅ full |
| 15 | STEP 3 — `get_keyword_categories`; returns L1–L8, `source`(auto/manual), `count`, `advertisable_sku_count` | SKILL.md STEP 3 | ✅ full |
| 16 | STEP 3 — note mapped categories per keyword, reused throughout | SKILL.md STEP 3 | ✅ full |
| 17 | STEP 3 — `keywords_not_found` (passed threshold, no S3 mapping) conclusion + STOP | SKILL.md STEP 3 | ✅ full |
| 18 | STEP 4 — (only if campaign IDs) `get_campaign_product_selection` per campaign; compare product L1/L2/L3 vs kw categories | SKILL.md STEP 4 | ✅ full |
| 19 | STEP 4 — no overlap → category-mismatch conclusion + STOP | SKILL.md STEP 4 | ✅ full |
| 20 | STEP 4 — overlap → STEP 5; skip STEP 4 if no campaign IDs | SKILL.md STEP 4 | ✅ full |
| 21 | STEP 5 — `get_campaigns_in_category(agency_id, start/end, category_level l1/l2/l3, category_l*_filter, top_n=50)`; pick top categories by count + advertisable_sku_count | SKILL.md STEP 5 | ✅ full |
| 22 | STEP 5 — `paused_campaigns`: flag paused that should run | SKILL.md STEP 5 | ✅ full |
| 23 | STEP 5 — `low_bu_campaigns` (spend < 50% budget) = POTENTIAL ROOT CAUSE; highlight | SKILL.md STEP 5 | ✅ full |
| 24 | STEP 5 — no active campaign in category → no-supply conclusion + STOP | SKILL.md STEP 5 | ✅ full |
| 25 | STEP 6 — top 2–3 campaigns, `get_campaign_product_selection`, inspect L1/L2/L3 match | SKILL.md STEP 6 | ✅ full |
| 26 | STEP 6 — RELEVANCY NOTE: cannot run relevancy algos; suggest verifying caches (title/taxonomy/inventory), raise internally | SKILL.md STEP 6 | ✅ full |
| 27 | STEP 7 — only call when STEPs 5–6 didn't conclude | SKILL.md STEP 7 | ✅ full |
| 28 | STEP 7 — `get_response_rate_by_dimension(marketplace_client_id, start/end, program_type="pla", group_by_columns="f_kw,network,store_id,page_type,category_l1")` | SKILL.md STEP 7 | ✅ full |
| 29 | STEP 7 — CRITICAL DATE RULE: MUST use 7-day trailing window (end_date−6 → end_date), not full range | SKILL.md STEP 7 | ✅ full |
| 30 | STEP 7 — interpret (concentrated f_kw but low RR across combos = filters too restrictive; find RR=0 combos) + conclusion style | SKILL.md STEP 7 | ✅ full |
| 31 | STEP 8 — only if STEP 5 flagged low-BU performers; `get_true_bu_campaign_data`; budget-exhaustion conclusion | SKILL.md STEP 8 | ✅ full |
| 32 | STEP 9 — per-advertiser not serving → `HANDOFF_TO_ROOT` delegate to keyword_delivery_agent | SKILL.md STEP 9 | ✅ full (renamed to "keyword-delivery skill") |
| 33 | POSSIBLE ROOT CAUSES 1–8 (summarise in final findings) | SKILL.md §Possible root causes | ✅ full |
| 34 | `_COMMON_RULES_TEMPLATE` — date format, period matching, currency prefix, scope transparency, HANDOFF_TO_ROOT triggers, store_agent_findings | common-rules.md §Output & tool rules / §Storing findings | ✅ full |

## Observations (not defects)
- **`store_agent_findings` tension, correctly navigated.** The source interpolates `_COMMON_RULES_TEMPLATE`, which carries the generic "MUST call `store_agent_findings()` before any summary" line. But this SOP's body never invokes it and ends only in per-keyword conclusions + a root-cause list. SKILL.md explicitly states the SOP "ends in conclusions + a root-cause summary, not the standard pre-summary/`store_agent_findings`/final-report flow" — a sound reading of how the SOP is actually designed. The generic rule remains available in `common-rules.md`. Not a defect.
- **No invented blocks.** SKILL.md does not add a competition check, program-types branch, cross-agent, pre-summary, or store-findings step — matching the fact that this instruction interpolates none of them. The competition/pre-summary/store-findings text present in `common-rules.md` is the shared reference (used by other skills), not content invented for this skill.
- **Adaptation, not degradation:** agent-name references (`keyword_delivery_agent`) rendered as "keyword-delivery skill"; tool parameter signatures abbreviated (`category_l*_filter`) — both justified per the whitelist (agent→skill renaming; MCP-derived input schemas).
