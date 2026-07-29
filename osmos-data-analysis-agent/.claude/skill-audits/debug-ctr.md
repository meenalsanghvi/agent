# Coverage audit — `debug-ctr` vs `CTR_AGENT_INSTRUCTION`

**Verdict: PASS with 1 minor defect** — the port faithfully preserves every SOP step, scenario threshold, the I/R stop/go gate, all three merchant lists, both branch paths, the competition path, and the full report table. One tool-interpretation nuance is degraded (SKU-level ranking/fields). **Defect count: 1 (1 ⚠️ degraded, 0 ❌ missing).**

Source: `weekly_analysis_agent/prompts/agent_instructions.py` lines 481–629. Elements audited: **51**.

| # | Source element | Destination | Status |
|---|----------------|-------------|--------|
| 1 | Persona line ("You are the CTR Debugging Agent …") | Dropped | ✅ dropped-justified (whitelist: persona) |
| 2 | `_COMMON_FIRST_STEP` — Step 0 parallel setup, date validation, user_note, program-type confirm | common-rules.md §STEP 0 | ✅ full |
| 3 | "Also get marketplace_client_id and timezone from context" | SKILL.md §intro | ✅ full |
| 4 | `_COMMON_CONSULTANT_BEHAVIOR` — scope-narrowing, discovery store, checkpoint model, rewind, date-change | common-rules.md §Consultant behavior | ✅ full |
| 5 | Key Concept — CTR = (Clicks/Impressions)×100 | SKILL.md §intro | ✅ full |
| 6 | Key Concept — ALWAYS decompose clicks vs impressions before conclusions | SKILL.md §Core principle | ✅ full |
| 7 | Key Concept — doubling-vs-halving illustration | SKILL.md §Core principle | ✅ full |
| 8 | `_COMMON_PROGRAM_TYPES` — PLA/Display channel filters | common-rules.md §STEP 0 | ✅ full |
| 9 | Tool `check_ctr_overall` — marketplace TOTAL, comparison mode, no per-entity contribution | SKILL.md §STEP 1 | ✅ full |
| 10 | Tool `get_page_level_performance` — page fields + I/R (ir=impr/resp), comparison-mode note | SKILL.md §STEP 2/3-A/3-B | ✅ full |
| 11 | Tool `get_display_ad_unit_performance` — Display only | SKILL.md §Program-type completeness | ✅ full |
| 12 | Tool `get_merchant_ctr_breakdown` — Pareto high_impact_merchants, contribution block, new_merchants_below_avg_ctr, churned_merchants_above_avg_ctr, "report both lists" | SKILL.md §STEP 4 | ✅ full |
| 13 | Tool `get_sku_level_ctr_performance` — "ranks SKUs by contribution to the impressions change with status + ctr change" | SKILL.md §3-B/STEP 4 | ⚠️ degraded — referenced as a tool but the ranking-by-contribution-to-impressions-change + status + ctr-change nuance is not stated |
| 14 | Tool `get_search_query_performance` — auto/manual split defs, sort_by="impressions" for CTR | SKILL.md §3-A/3-B | ✅ full |
| 15 | Tool `get_keyword_seller_breakdown` — new/existing/churned classification, CTR draggers, after search-query | SKILL.md §3-A/3-B | ✅ full |
| 16 | Tool `get_category_level_performance` — L1/L2/L3 progressive drill, group_by_merchant, contribution_to_impressions_change | SKILL.md §3-A/3-B | ✅ full |
| 17 | Tool `get_merchant_keyword_performance` — SEARCH merchant drill, keywords×campaign pre/post, NO rows=AUTO fallback | SKILL.md §STEP 4 drill | ✅ full (match_type/spend/cpm/roas dimensions summarized as "pre/post CTR" + contribution pattern, essence preserved) |
| 18 | Tool `get_merchant_category_performance` — NON-SEARCH merchant drill, categories×campaign pre/post | SKILL.md §STEP 4 drill | ✅ full |
| 19 | Tool `get_product_selection_changes` — additions/removals audit | SKILL.md §3-B | ✅ full |
| 20 | Tool `get_campaign_product_selection` — active products, group→campaign resolution via lookup_campaign | SKILL.md §Additional drill tools | ✅ full |
| 21 | Tool `get_campaign_status_changes` — status audit | SKILL.md §3-A/3-B/STEP 5 | ✅ full |
| 22 | Tool `get_campaign_performance` — campaign-level | SKILL.md §STEP 4.5 | ✅ full |
| 23 | Tool `lookup_merchant` — client_id ↔ merchant_id | SKILL.md §Additional drill tools | ✅ full |
| 24 | Tool `lookup_campaign` — MUST ask ID type first, errors w/o valid id_type, returns 4 IDs | SKILL.md §Additional drill tools | ✅ full |
| 25 | State tools list (get_context, get_date_ranges, update_analysis, store_agent_findings, get_all_findings, store_discovery, get_discoveries) | common-rules.md + SKILL.md §Additional drill tools | ✅ full |
| 26 | "Skip SOP if user asks something specific — call matching tool" | SKILL.md §Core principle | ✅ full |
| 27 | STEP 1 — Triage (check_ctr_overall comparison, decompose before classification) | SKILL.md §STEP 1 | ✅ full |
| 28 | STEP 2 — Scenario A/B/C definitions + thresholds (>5%, >2%, <2%) | SKILL.md §STEP 2 | ✅ full |
| 29 | STEP 2 — "Tell user which scenario before proceeding" | SKILL.md §STEP 2 | ✅ full |
| 30 | STEP 2 — IMPRESSION-DRIVEN GATE: I/R FIRST, DROPPED→RAISE TO CLIENT & stop, INCREASED/held→go forward | SKILL.md §STEP 2 | ✅ full |
| 31 | STEP 2 — options restricted to page-level / merchant-level; "Do NOT offer search-query here" | SKILL.md §STEP 2 | ✅ full |
| 32 | STEP 3-A — impression dilution: I/R gate per page (ir_change), mix effect / new inventory / systemic branches, checkpoint | SKILL.md §STEP 3-A | ✅ full |
| 33 | STEP 3-A — SEARCH branch (search-query + keyword-seller, report format) | SKILL.md §STEP 3-A | ✅ full |
| 34 | STEP 3-A — NON-SEARCH branch (category L1→L3 progressive, report) | SKILL.md §STEP 3-A | ✅ full |
| 35 | STEP 3-A — get_campaign_status_changes (new low-quality campaigns) | SKILL.md §STEP 3-A | ✅ full |
| 36 | STEP 3-B — engagement decline: page interpretation (search/category/product), checkpoint | SKILL.md §STEP 3-B | ✅ full |
| 37 | STEP 3-B — SEARCH branch + "clicks fell = points OUTWARD → competition possible; STEP 4.5 offers it" | SKILL.md §STEP 3-B | ✅ full |
| 38 | STEP 3-B — NON-SEARCH branch (category drill, group_by_merchant, report) | SKILL.md §STEP 3-B | ✅ full |
| 39 | STEP 3-B — SKU / product-selection / status-change checks | SKILL.md §STEP 3-B | ✅ full |
| 40 | STEP 3-C — volume decline checkpoint text + HANDOFF_TO_ROOT redirect | SKILL.md §STEP 3-C | ✅ full |
| 41 | STEP 4 — mandatory checkpoint, all 4 lists + baseline_avg_ctr_threshold, lead with Pareto | SKILL.md §STEP 4 | ✅ full |
| 42 | STEP 4 — "NEVER show only change %; include RAW baseline & current" | SKILL.md §STEP 4 | ✅ full |
| 43 | STEP 4 — merchant drill branches (SEARCH / NON-SEARCH / OVERALL), checkpoint if multiple | SKILL.md §STEP 4 | ✅ full |
| 44 | STEP 4.5 — competition conditional (user-request-only, secondary cause, one-merchant narrowing, distinct from seller dilution) | SKILL.md §STEP 4.5 | ✅ full |
| 45 | `_COMMON_COMPETITION_CHECK` — targeting fingerprint, keyword/category/merchant surfaces, bid-not-spend conclusion | common-rules.md §COMPETITION CHECK | ✅ full |
| 46 | STEP 5 — `_COMMON_PRE_SUMMARY_CHECKPOINT` (confirm before summarizing, offer next-step options) | common-rules.md §Pre-summary checkpoint | ✅ full |
| 47 | STEP 5 — Interpretation bullets (CTR→CPC, CTR+impression spike→RR/BU, check status before relevance) | SKILL.md §STEP 5 | ✅ full |
| 48 | `_COMMON_CROSS_AGENT` — get_all_findings once, note overlaps | common-rules.md §Cross-agent | ✅ full |
| 49 | `_build_store_findings_block("ctr", …)` — metric_type ctr, severity thresholds (>15/5-15/<5%), impacted_entities keyed client_id + type merchant/page_type | SKILL.md §STEP 5 + common-rules.md §Storing findings | ✅ full |
| 50 | Final Summary format — header, Scenario, Root Cause, Key Findings, Page/Keyword/Merchant tables (exact columns) | SKILL.md §Final Summary | ✅ full |
| 51 | `_COMMON_RULES_TEMPLATE` — date format, period matching, currency prefix, scope transparency, HANDOFF_TO_ROOT conditions | common-rules.md §Output & tool rules | ✅ full |

## Observations (not defects)
- The source is internally consistent (scenario numbers, step numbers, branch labels all line up); no source inconsistencies that the skill needed to fix.
- Tool input schemas / optional filter parameters (`client_ids`, `seller_ids`, `marketing_campaign_ids`) are correctly omitted — parameter signatures are whitelisted drops.
- `get_search_query_performance`'s rationale phrase "impression-weighted queries are the ones that move CTR" is dropped, but the actionable instruction (`sort_by="impressions"` for CTR work) is preserved — not a defect.
