# Coverage audit — `debug-irrelevancy` vs `IRRELEVANCY_AGENT_INSTRUCTION`

**Verdict: PASS — faithful port. 0 defects across 36 audited elements.**

Source: `weekly_analysis_agent/prompts/agent_instructions.py` lines 1472–1542
(`IRRELEVANCY_AGENT_INSTRUCTION`), interpolating `_COMMON_FIRST_STEP` (138),
`_COMMON_CONSULTANT_BEHAVIOR` (158), `_COMMON_RULES_TEMPLATE` (228).

Structural notes confirmed in source: the instruction has **no `Tools:` block, no
`State:` block, no `Key Concepts` block, and no Final Report table** — it is a
conclusion/root-cause-summary SOP. It does NOT interpolate a store-findings,
competition-check, program-types, cross-agent, or pre-summary block. **PLA +
SEARCH page only** confirmed (source line 1472, 1479, 1496). The skill correctly
reflects all of this and invents none of the absent blocks in its body.

| # | Source element | Destination | Status |
|---|----------------|-------------|--------|
| 1 | Persona line "You are the Irrelevancy Agent — specialist…" (1472) | Dropped | ✅ dropped-justified |
| 2 | Scope override "PLA, SEARCH page only" (1472/1479) | SKILL.md §Overrides + §Program-type completeness | ✅ full |
| 3 | `_COMMON_FIRST_STEP` — STEP 0 one-time setup, dates, user_note, program-type gate (1474) | common-rules.md §STEP 0 | ✅ full |
| 4 | "Also get marketplace_client_id, timezone from context" (1475) | SKILL.md intro (l.21) | ✅ full |
| 5 | `_COMMON_CONSULTANT_BEHAVIOR` — scope-narrowing, discovery store, checkpoint model, rewind (1477) | common-rules.md §Consultant behavior | ✅ full |
| 6 | SCOPE / goal framing — identify cache_type that served irrelevant SKU; genuine divergence vs algorithm issue (1479) | SKILL.md intro + description | ✅ full |
| 7 | STEP 1 — Campaign ID(s) **required** (1482) | SKILL.md §STEP 1 | ✅ full |
| 8 | STEP 1 — Keyword(s) optional; Step 2 discovers if absent (1483) | SKILL.md §STEP 1 | ✅ full |
| 9 | STEP 1 — Specific product/SKU optional but helpful (1484) | SKILL.md §STEP 1 | ✅ full |
| 10 | STEP 1.5 — MANDATORY ID-type confirmation (ask which of the 4 types) (1487-1488) | SKILL.md §STEP 1.5 | ✅ full |
| 11 | STEP 1.5 — do NOT guess / do NOT default (1489) | SKILL.md §STEP 1.5 | ✅ full |
| 12 | STEP 1.5 — `lookup_campaign(raw_ids, id_type)` for every ID of that type (1489) | SKILL.md §STEP 1.5 | ✅ full |
| 13 | STEP 1.5 — extract `marketing_campaign_id` (downstream tools require) (1490) | SKILL.md §STEP 1.5 | ✅ full |
| 14 | STEP 1.5 — note `seller_id`/`client_id`; client_id needed in Step 2 (1491) | SKILL.md §STEP 1.5 | ✅ full |
| 15 | STEP 1.5 — re-ask if any ID fails to resolve (type may be wrong) (1492) | SKILL.md §STEP 1.5 | ✅ full |
| 16 | STEP 2 — `get_campaign_targeted_keywords(marketplace_client_id, marketing_campaign_id, client_id)` per campaign (1495) | SKILL.md §STEP 2 | ✅ full |
| 17 | STEP 2 — SEARCH-campaigns ONLY; confirm with user if ambiguous (1496) | SKILL.md §STEP 2 | ✅ full |
| 18 | STEP 2 — `targeted_keywords` (is_negative=0), each `(text, bidding_value)`, null/0 = AUTO (1498) | SKILL.md §STEP 2 | ✅ full |
| 19 | STEP 2 — `negative_keywords` (is_negative=1) (1499) | SKILL.md §STEP 2 | ✅ full |
| 20 | STEP 2 why-first — verify user keyword targeted; if not targeted & not neg-leak → expected auto/broad → call out & STOP (no bug) (1502) | SKILL.md §STEP 2 | ✅ full |
| 21 | STEP 2 why-first — no keyword given → use targeted_keywords as STEP 3 candidate list (1503) | SKILL.md §STEP 2 | ✅ full |
| 22 | STEP 2 why-first — negative-list keyword that still served = separate bug, flag it (1504) | SKILL.md §STEP 2 | ✅ full |
| 23 | STEP 3 — `get_keyword_categories(marketplace_client_id, search_queries)` with user kw OR top targeted (1507-1509) | SKILL.md §STEP 3 | ✅ full |
| 24 | STEP 3 — returns categories L1-L8, source=auto/manual, count, advertisable_sku_count (1511) | SKILL.md §STEP 3 | ✅ full |
| 25 | STEP 3 — mapped categories = "relevant" reference set for STEP 5 (1512) | SKILL.md §STEP 3 | ✅ full |
| 26 | STEP 4 — `get_responded_skus(marketplace_client_id, timezone, start/end, search_queries, campaign_ids)` (1515-1516) | SKILL.md §STEP 4 | ✅ full |
| 27 | STEP 4 — pass `product_name_like` when user named a specific product (pinpoints SKU+cache_type) (1517) | SKILL.md §STEP 4 | ✅ full |
| 28 | STEP 4 — return per kw+cache_type+SKU: product name, brand, category, impressions, spend (1519) | SKILL.md §STEP 4 | ✅ full |
| 29 | STEP 4 — `cache_type` is the key signal (names the OS algorithm) (1520) | SKILL.md §STEP 4 | ✅ full |
| 30 | STEP 5 — OVERLAP → not irrelevant at OS mapping level; taxonomy; present overlap + cache_type (1527) | SKILL.md §STEP 5 | ✅ full |
| 31 | STEP 5 — NO OVERLAP → GENUINE MISMATCH; cache_type = responsible algorithm; full conclusion text (1528) | SKILL.md §STEP 5 | ✅ full |
| 32 | STEP 5 — `keywords_not_found` → no ground truth; S3 mapping conclusion (1529) | SKILL.md §STEP 5 | ✅ full |
| 33 | STEP 5 — NEGATIVE LEAK conclusion (negative-match bypass bug) (1530) | SKILL.md §STEP 5 | ✅ full |
| 34 | STEP 6 — per-advertiser summary, group findings by `cache_type` (1533) | SKILL.md §STEP 6 | ✅ full |
| 35 | POSSIBLE ROOT CAUSES — the 4 numbered causes (1536-1539) | SKILL.md §Possible root causes | ✅ full |
| 36 | `_COMMON_RULES_TEMPLATE` — date format, period matching, currency prefix, scope transparency, HANDOFF_TO_ROOT triggers (1541) | common-rules.md §Output & tool rules | ✅ full |

## Observations (not defects)

- **Source inconsistency correctly resolved.** `_COMMON_RULES_TEMPLATE` (interpolated
  at 1541) carries the boilerplate mandate "CRITICAL: You MUST call
  `store_agent_findings()` BEFORE writing any final summary" (source l.235), yet the
  irrelevancy SOP never sets up a findings/store step and has no Final Report table —
  it is purely conclusion-based. The skill resolves this cleanly in its Overrides note
  ("ends in conclusions + a root-cause summary … not the standard
  pre-summary/`store_agent_findings`/final-report flow"), so the shared boilerplate
  does not mislead a reader of this skill. This is the intended PLA+SEARCH,
  conclusion-only design, not a dropped element.
- The skill body does **not** invent a store-findings, competition-check,
  program-types (as its own section), cross-agent, or pre-summary block — matching the
  source, which interpolates none of them. (Those blocks exist in the shared
  `common-rules.md`, which is correct for a shared reference file consumed by other
  skills.)
