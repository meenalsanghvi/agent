# Coverage audit — `debug-keyword-delivery` vs `KEYWORD_DELIVERY_AGENT_INSTRUCTION`

**Verdict: PASS with 2 minor degradations** — every SOP step, verdict, threshold, branch, stop-condition, the PLA-only scope, and all three competition views are preserved; the only losses are dropped tool return-field / breakdown nuances in STEP 2 zoom-out and STEP 6b. No SOP step, branch, verdict, or the Display path is missing (source is PLA-only by design). No blocks invented.

**Defects: 2 (⚠️ degraded), 0 (❌ missing). Elements audited: 44.**

Source range: `weekly_analysis_agent/prompts/agent_instructions.py` lines 1261–1378.
Interpolated blocks expanded: `_COMMON_FIRST_STEP` (138), `_COMMON_CONSULTANT_BEHAVIOR` (158), `_COMMON_RULES_TEMPLATE` (228).
This instruction does NOT interpolate a pre-summary, store-findings (`_build_store_findings_block`), program-types, cross-agent, or competition-check block — confirmed the skill does not invent them (SKILL.md explicitly overrides the summary flow).

| # | Source element | Destination | Status |
|---|----------------|-------------|--------|
| 1 | Persona: "You are the Keyword Delivery Agent — specialist…" | Dropped | ✅ dropped-justified (persona/identity line) |
| 2 | Scope: covers BOTH "not serving / regressed" AND "low delivery / outbid" | SKILL.md intro + description | ✅ full |
| 3 | PLA only | SKILL.md (Overrides + Program-type completeness) | ✅ full |
| 4 | "Also get marketplace_client_id, timezone from context" | SKILL.md §intro | ✅ full |
| 5 | STEP 0 parallel setup (get_context/get_date_ranges/get_all_findings/get_discoveries) | common-rules.md §STEP 0 | ✅ full |
| 6 | Context fields yielded (agency_id, region, currency, timezone, problem_summary, affected_program, user_note, dates, prior findings, discoveries) | common-rules.md §STEP 0 | ✅ full |
| 7 | Don't proceed without context; don't re-call setup tools | common-rules.md §STEP 0 | ✅ full |
| 8 | Date validation (no dates → ask+set; user diff → set; match → proceed) | common-rules.md §STEP 0 Dates | ✅ full |
| 9 | Current-year date rule | common-rules.md §STEP 0 Dates | ✅ full |
| 10 | user_note check for IDs/entities | common-rules.md §STEP 0 | ✅ full |
| 11 | Program-type confirm + pass as program_type | common-rules.md §STEP 0 | ✅ full |
| 12 | Consultant: narrowed scope → skip broad | common-rules.md §Consultant #1 | ✅ full |
| 13 | Consultant: listen for entities, call matching tool | common-rules.md §Consultant #2 | ✅ full |
| 14 | Date-change mid-conversation (set_date_ranges, restart Step 1, no re-Step 0) | common-rules.md §Consultant | ✅ full |
| 15 | Discovery store (store_discovery / get_discoveries) | common-rules.md §Consultant | ✅ full |
| 16 | Interactive checkpoint model (parts a–d, findings table mandate) | common-rules.md §Checkpoint format | ✅ full |
| 17 | Honour the choice (call exact tool named) | common-rules.md §Checkpoint | ✅ full |
| 18 | Rewind behavior | common-rules.md §Checkpoint | ✅ full |
| 19 | Exception: no checkpoint for Step-0 setup | common-rules.md §Checkpoint | ✅ full |
| 20 | Remember filters / tools any order / broad → default flow | common-rules.md §Consultant #4–6 | ✅ full |
| 21 | Rules: date format YYYY-MM-DD no trailing chars | common-rules.md §Output rules | ✅ full |
| 22 | Rules: period matching (check `period` field) | common-rules.md §Output rules | ✅ full |
| 23 | Rules: currency prefix on monetary values | common-rules.md §Output rules | ✅ full |
| 24 | Rules: choose tools dynamically | common-rules.md §Consultant #5 | ✅ full |
| 25 | Rules: MUST call store_agent_findings() before final summary | common-rules.md §Storing findings | ✅ full (SKILL.md override to optional — see observation) |
| 26 | Rules: scope transparency | common-rules.md §Output rules | ✅ full |
| 27 | Rules: HANDOFF_TO_ROOT conditions (5) + never ask user for agency_id | common-rules.md §Output rules | ✅ full |
| 28 | STEP 1 — gather which keyword(s) + which campaign(s) | SKILL.md §STEP 1 | ✅ full |
| 29 | STEP 1.5 — mandatory id-type ask, no guess/default, lookup_campaign(raw_ids,id_type), extract marketing_campaign_id, fail→re-ask | SKILL.md §STEP 1.5 | ✅ full |
| 30 | STEP 2 — campaign-scoped (not marketplace-wide) validation rationale | SKILL.md §STEP 2 | ✅ full |
| 31 | check_targeted_keyword_performance_in_campaigns TWICE parallel (curr+baseline); pass BOTH client_ids AND marketing_campaign_ids; errors without client_ids (per-client); source os_ads_keyword_performance_report distinct from search-query; returns spend/impressions/CTR/CPM/attributed sales/ROI | SKILL.md §STEP 2 | ✅ full |
| 32 | Optional zoom-out: get_merchant_keyword_performance (keyword × campaign_name × match_type, ranked by spend; where kw sits among top performers / whether other campaigns serve it; auto-vs-manual gate) + get_merchant_category_performance | SKILL.md §STEP 2 | ⚠️ degraded |
| 33 | STEP 2 interpret — 4 cases (zero→Step3; regression→Step3; low CTR→Step4; performing fine→INVALID REQUEST/STOP) | SKILL.md §STEP 2 Interpret | ✅ full |
| 34 | STEP 3 — check_keyword_request_volume(keywords, current end_date); >100 in trailing 7 days; below→conclusion(N)/expected; above→Step4 | SKILL.md §STEP 3 | ✅ full |
| 35 | STEP 4 — get_keyword_categories (S3) + get_campaign_product_selection (l1/l2/l3), both in PARALLEL | SKILL.md §STEP 4 | ✅ full |
| 36 | STEP 5 — K/P/missing_categories defs + 4 branches (∅→mismatch/ticket/STOP; keywords_not_found→ticket/STOP; partial→inform/PROCEED; full→PROCEED) | SKILL.md §STEP 5 | ✅ full |
| 37 | STEP 6 header — competition analysis, run all views | SKILL.md §STEP 6 | ✅ full (fixed "TWO…run BOTH" vs 6a/6b/6c inconsistency → "run ALL THREE") |
| 38 | 6a — get_search_query_match_performance signature; sov def; top_search_impressions_share def (within-campaign, not competitive); 4 interpretation cues | SKILL.md §6a | ✅ full |
| 39 | 6b — get_targeted_keyword_competition in comparison mode; return fields (spend/impressions/**clicks**/CPC/CPM, changes, status/**effective_status**, contribution, **campaign_name**, campaign_creation_date, new_in_post); sort impressions DESC / **top 3-5**; compare on bid model (CPC meaningless for CPM); prioritise new_in_post + new_entrants_in_period + risen cpc/cpm; **report each rival WITH contribution**; timing cross-ref | SKILL.md §6b | ⚠️ degraded |
| 40 | 6c — REQUIRED, do NOT skip; rationale (AUTO rivals 6b misses); get_search_query_performance(breakdown_by="campaign", marketplace-wide, +baseline); keyword_match_type + new_competitors; compare on OUR bid model | SKILL.md §6c | ✅ full |
| 41 | CONCLUSION format (combine 6a+6b+6c) | SKILL.md §STEP 6 Conclusion | ✅ full |
| 42 | No-competitor fallback: get_campaign_status_changes + suggest product-stock check in overlapping categories | SKILL.md §STEP 6 | ✅ full |
| 43 | PLA-only completeness — source has no Display path | SKILL.md §Program-type completeness | ✅ full (correct; no Display path exists to drop) |
| 44 | No invented pre-summary / store-findings / final-report / competition-check / program-types / cross-agent block | SKILL.md §Overrides | ✅ full (explicitly overridden, not invented) |

## Observations (not defects)
- **Source inconsistency fixed:** STEP 6's lead ("TWO complementary views, run BOTH") contradicts its 6a/6b/6c sub-steps; the skill correctly renders it as "run ALL THREE views."
- **store_agent_findings override:** `_COMMON_RULES_TEMPLATE` carries the "MUST call store_agent_findings before any final summary" mandate; the rule is faithfully preserved in common-rules.md, and SKILL.md's Overrides section relaxes it to optional because this SOP legitimately ends in diagnosis/ticket conclusions with no final-report step — a defensible metric-specific reconciliation, not a silent drop.
