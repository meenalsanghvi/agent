# Coverage audit — `debug-cpc` skill vs `CPC_AGENT_INSTRUCTION`

**Verdict: ✅ Faithful port — 1 minor degraded nuance, 0 missing elements** (59 elements audited).

Source: `weekly_analysis_agent/prompts/agent_instructions.py` lines 374–478 (`CPC_AGENT_INSTRUCTION`)
plus interpolated blocks `_COMMON_FIRST_STEP` (138), `_COMMON_CONSULTANT_BEHAVIOR` (158),
`_COMMON_PROGRAM_TYPES` (221), `_COMMON_PRE_SUMMARY_CHECKPOINT` (215), `_COMMON_CROSS_AGENT` (225),
`_COMMON_RULES_TEMPLATE` (228), `_build_store_findings_block` (269).
Skill: `.claude/skills/debug-cpc/SKILL.md` + `references/common-rules.md`.

Note: the CPC source **inlines** its competition logic in STEP 5 (it does NOT interpolate
`_COMMON_COMPETITION_CHECK`), so STEP 5 is audited against SKILL.md §STEP 5, not against the
common-rules COMPETITION CHECK section. That common section is shared context carried for other
skills and is harmless here.

| # | Source element | Destination | Status |
|---|----------------|-------------|--------|
| 1 | Persona: "You are the CPC Debugging Agent…" | Dropped | ✅ dropped-justified (persona/identity) |
| 2 | `_COMMON_FIRST_STEP` — STEP 0 parallel setup (get_context/get_date_ranges/get_all_findings/get_discoveries; no re-call) | common-rules §STEP 0 | ✅ full |
| 3 | `_COMMON_FIRST_STEP` — date validation (none→ask+set; differ→set; match→proceed; current-year rule) | common-rules §STEP 0 Dates | ✅ full |
| 4 | `_COMMON_FIRST_STEP` — user_note check for IDs/entities | common-rules §STEP 0 user_note | ✅ full |
| 5 | `_COMMON_FIRST_STEP` — confirm program type; never default; pass as `program_type` | common-rules §STEP 0 Program type | ✅ full |
| 6 | `_COMMON_CONSULTANT_BEHAVIOR` 1–2 — narrowed scope / listen for entities | common-rules §Consultant 1–2 | ✅ full |
| 7 | Consultant — mid-conversation date change (set_date_ranges, restart STEP 1, don't re-run STEP 0) | common-rules §Consultant | ✅ full |
| 8 | Consultant — discovery store (store_discovery; check get_discoveries first) | common-rules §Consultant | ✅ full |
| 9 | Consultant 3 — interactive checkpoint model, four parts (a–d) + template | common-rules §Checkpoint format | ✅ full |
| 10 | Consultant — honour the choice / rewind / STEP-0 exception | common-rules §Checkpoint | ✅ full |
| 11 | Consultant 4–6 — remember filters / any tool order / broad→default flow; SOP-only note | common-rules §Consultant 4–6 | ✅ full |
| 12 | `_COMMON_PROGRAM_TYPES` — PLA vs Display channel filters | common-rules §STEP 0 column rules | ✅ full |
| 13 | Key Concepts — CPC = Spend ÷ Clicks; attribute by contribution | SKILL.md §intro + Decomposition | ✅ full |
| 14 | Key Concepts (contribution-first) — comparison mode; spend- & clicks-contribution; clicks caveat | SKILL.md §Core principle | ✅ full |
| 15 | Key Concepts — SITE vs PROGRAM distinct; attributed_cvr vs site_cvr | SKILL.md §Core principle | ✅ full |
| 16 | Tool `get_page_level_performance` — page CPC, comparison, cpc_change + contribution | SKILL.md §STEP 1 | ✅ full |
| 17 | Tool `get_merchant_cpc_breakdown` — named fields pre_period_top_contributors, new_merchants, new_merchants_above_avg_cpc, churned_merchants_below_avg_cpc, baseline_avg_cpc_threshold | SKILL.md §STEP 3 | ✅ full |
| 18 | Tool `get_campaign_subtype_cpc_breakdown` — PLA buckets; "INSTEAD of jumping to SKU" | SKILL.md §STEP 2 | ✅ full |
| 19 | Tool `get_merchant_category_cpc_comparison` — verdicts cpc_benign / competition_reduced / merchant_cpc_concern; PLA only | SKILL.md §STEP 4 | ✅ full |
| 20 | Tool `get_sku_level_cpc_performance` — PLA-only SKU drill; prefer subtype/category first | SKILL.md §STEP 6 | ✅ full |
| 21 | Tool `get_product_selection_changes` — audit log; client_ids/campaign_ids + timezone | SKILL.md §Additional drill tools | ✅ full |
| 22 | Tool `get_campaign_performance` — comparison one-call (not two); daily=True; client_ids | SKILL.md §STEP 5a | ✅ full |
| 23 | Tool `get_campaigns_in_category` — named fields new_entrants_in_period, subtype_summary; two-hop usage | SKILL.md §STEP 5 (a2 NON-SEARCH, broad) | ✅ full (bid-model field `campaign_group_bidding_strategy_type` not named — bid-model preserved via lookup_campaign; observation only) |
| 24 | Tool `get_targeted_keyword_competition` — TARGETED vs served-on view; new_in_post; exclude_marketing_campaign_ids; bid model | SKILL.md §STEP 1.5, §STEP 5b | ⚠️ degraded — named return field `campaign_creation_date` (rival-entry-timing signal) + the per-rival CTR/ROI metrics dropped from the tool description |
| 25 | Tool `get_campaign_targeted_keywords` — (text, bidding_value); manual-vs-auto gate; count 0→search-query route; don't hand-derive from product names | SKILL.md §STEP 5b + common-rules §Competition | ✅ full |
| 26 | Tool `get_search_query_performance` — typed queries; breakdown_by="campaign" (new_competitors); AUTO scope then marketplace-wide | SKILL.md §STEP 1.5, §STEP 5b | ✅ full |
| 27 | Tool `get_merchant_keyword_performance` — keywords × campaign; SEARCH drill + manual-vs-auto gate (NO rows→AUTO) | SKILL.md §STEP 5 a2 SEARCH | ✅ full |
| 28 | Tool `get_merchant_category_performance` — categories × campaign; NON-SEARCH drill | SKILL.md §STEP 5 a2 NON-SEARCH | ✅ full |
| 29 | State tools (get_context, get_date_ranges, update_analysis, store_agent_findings, get_all_findings, store_discovery, get_discoveries) | common-rules (+ SKILL update_analysis) | ✅ full |
| 30 | "Skip SOP if user asks something specific" escape hatch | SKILL.md §Core principle | ✅ full |
| 31 | STEP 1 triage — comparison; decomposition; identify pages by contribution; spend_share_baseline/current_pct vs contribution_to_spend_change_pct | SKILL.md §STEP 1 | ✅ full |
| 32 | STEP 1 FLOOR-PRICE checkpoint — SEARCH→Keyword Floors / other→Category Floors; metric-agnostic CPC/CPM; no tool, ask user, never imply | SKILL.md §STEP 1 | ✅ full |
| 33 | STEP 1 — multiple pages → checkpoint ask which first | SKILL.md §STEP 1 | ✅ full |
| 34 | STEP 1 next-step steering — free branch; SEARCH→1.5 primary (not bare "competition"); NON-SEARCH→3, STEP 2 optional; run what user picks, no substitution | SKILL.md §STEP 1 | ✅ full |
| 35 | STEP 1.5 — marketplace-wide search-query drill; sort_by spend / rank by current spend; never sort by cpc_change alone; lead raw+cpc_change+contribution+AUTO-manual; ≈10–20 rows; churned high-CPC flagged separately | SKILL.md §STEP 1.5 | ✅ full |
| 36 | STEP 1.5 — competition on queries (breakdown_by campaign new_competitors; targeted_keyword_competition new_in_post; drop/rise interpretation) | SKILL.md §STEP 1.5 | ✅ full |
| 37 | STEP 1.5 — drop to merchants (STEP 3) only to attribute / on user request | SKILL.md §STEP 1.5 | ✅ full |
| 38 | STEP 2 — subtype buckets, optional narrowing not prerequisite | SKILL.md §STEP 2 | ✅ full |
| 39 | STEP 3 — merchant breakdown drivers + named fields; take os_client_ids forward | SKILL.md §STEP 3 | ✅ full |
| 40 | STEP 3 — MERCHANT-SCOPED GATE (STEP 4/5/6 + merchant tools require os_client_id) | SKILL.md §STEP 3 | ✅ full |
| 41 | STEP 4 — category vs category-average, three verdicts | SKILL.md §STEP 4 | ✅ full |
| 42 | STEP 5 GATE — single-merchant only; default flow stops at merchant/category (1–4); checkpoint if multiple | SKILL.md §STEP 5 | ✅ full |
| 43 | STEP 5a — get_campaign_performance driving campaign by contribution; daily rows | SKILL.md §STEP 5a | ✅ full |
| 44 | STEP 5a2 — branch on affected page (SEARCH / NON-SEARCH two-hop / OVERALL); carry marketing_campaign_id forward; product_type ≠ category taxonomy | SKILL.md §STEP 5 a2 | ✅ full |
| 45 | STEP 5b — FETCH keywords first; forbidden Smart-Shopping hallucination; EXACT/PHRASE/BROAD = proof of manual | SKILL.md §STEP 5b | ✅ full |
| 46 | STEP 5b count>0 MANUAL — targeted_keyword_competition; compare on bid model (bidding_strategy via lookup_campaign) CPC/CPM | SKILL.md §STEP 5b | ✅ full |
| 47 | STEP 5b count=0 AUTO — mandatory 3-step data-driven flow (queries→competition→corroboration); core deduction | SKILL.md §STEP 5b | ✅ full |
| 48 | STEP 5b — broad/category bid pressure via get_campaigns_in_category | SKILL.md §STEP 5b | ✅ full |
| 49 | STEP 5 conclusion — bid-competition vs own bid change; cite contested query/category + rival on OUR bid model | SKILL.md §STEP 5 | ✅ full |
| 50 | STEP 6 — SKU optional PLA; spend/clicks interpretation; CTR handoff | SKILL.md §STEP 6 (CTR skill handoff) | ✅ full |
| 51 | STEP 7 — `_COMMON_PRE_SUMMARY_CHECKPOINT` (confirm before store/summary) | common-rules §Pre-summary + SKILL.md §STEP 7 | ✅ full |
| 52 | `_COMMON_CROSS_AGENT` — get_all_findings once; note overlaps | common-rules §Cross-agent | ✅ full |
| 53 | `_build_store_findings_block("cpc",…)` — metric_type cpc; severity CPC-increase >15/5–15/<5%; client_id + type merchant | common-rules §Storing findings + SKILL.md §STEP 7 | ✅ full |
| 54 | Final Report header (Summary/Severity/Period/Root Cause/Programs/Key Findings) | SKILL.md §Final Report | ✅ full |
| 55 | Final Report — Page-types table columns (7) | SKILL.md §Final Report | ✅ full |
| 56 | Final Report — Merchants table columns (16, high_impact_merchants Pareto first) | SKILL.md §Final Report | ✅ full |
| 57 | Final Report — Subtype buckets table columns | SKILL.md §Final Report | ✅ full |
| 58 | Final Report — Categories table columns (verdict) | SKILL.md §Final Report | ✅ full |
| 59 | `_COMMON_RULES_TEMPLATE` — date format, period matching, currency, dynamic tools, store_agent_findings-before-summary, scope transparency, HANDOFF_TO_ROOT conditions | common-rules §Output & tool rules | ✅ full |

## Observations (not defects)
- Source correctly adapted: STEP 6 "consider CTR agent" → "handing off to the CTR skill" (agent→skill terminology). Faithful.
- `lookup_campaign` and `get_keyword_seller_breakdown` are referenced but not in the source `Tools:` block — a source omission the skill mirrors (lookup_campaign referenced in STEP 5b; get_keyword_seller_breakdown only in the shared common-rules competition section, unused by CPC's inlined STEP 5). Not a skill defect.
- `get_campaigns_in_category`'s named bid-model field `campaign_group_bidding_strategy_type` is not surfaced in SKILL.md, but the bid-model comparison itself is preserved (read `bidding_strategy` from `lookup_campaign`). Functionally equivalent — logged as observation, not counted as a defect.
