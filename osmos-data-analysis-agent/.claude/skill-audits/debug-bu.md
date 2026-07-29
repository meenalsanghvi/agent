# Coverage audit — `debug-bu` vs `BU_AGENT_INSTRUCTION`

**Verdict:** Substantially faithful — 3 defects (1 missing, 2 degraded); every SOP step, branch, threshold, stop-condition, Display path, and the Final-Report columns are preserved.
**Elements audited:** 48 · **Defects:** 3 (❌ 1 / ⚠️ 2)

Source: `weekly_analysis_agent/prompts/agent_instructions.py` lines 630–828 (`BU_AGENT_INSTRUCTION`) plus interpolated blocks `_COMMON_FIRST_STEP`, `_COMMON_CONSULTANT_BEHAVIOR`, `_COMMON_PROGRAM_TYPES`, `_COMMON_PRE_SUMMARY_CHECKPOINT`, `_COMMON_CROSS_AGENT`, `_COMMON_RULES_TEMPLATE`, `_build_store_findings_block`.
(Note: BU does NOT interpolate `_COMMON_COMPETITION_CHECK`; its presence in `common-rules.md` is shared-file overhead, not a BU requirement — correctly not surfaced in the BU SKILL.)

| # | Source element | Destination | Status |
|---|----------------|-------------|--------|
| 1 | Persona — "You are the Budget Utilisation (BU) Debugging Agent." | Dropped | ✅ dropped-justified |
| 2 | `_COMMON_FIRST_STEP` — STEP 0 parallel setup (get_context/get_date_ranges/get_all_findings/get_discoveries), no re-call | common-rules §STEP 0 | ✅ full |
| 3 | Date validation / current-year default | common-rules §STEP 0 (Dates) | ✅ full |
| 4 | user_note check | common-rules §STEP 0 (user_note) | ✅ full |
| 5 | Program-type confirm before analysis; pass as program_type | common-rules §STEP 0 (Program type) | ✅ full |
| 6 | "Also get marketplace_client_id, region, timezone from context" | SKILL.md intro | ✅ full |
| 7 | Data-retention gate: get_category_request_volume / get_filter_presence_response_rates → 15-day | SKILL.md §Data-retention gate | ✅ full |
| 8 | Data-retention gate: get_category_quadrant_performance → 7-day (+ get_display_quadrant consolidated) | SKILL.md §Data-retention gate | ✅ full |
| 9 | Retention warning format string | SKILL.md §Data-retention gate | ✅ full |
| 10 | `_COMMON_CONSULTANT_BEHAVIOR` — narrowed scope / entity listening / checkpoint model / date-change / discovery store / rewind | common-rules §Consultant behavior | ✅ full |
| 11 | Checkpoint 4-part format (where/findings-table/means/options) | common-rules §Checkpoint format | ✅ full |
| 12 | Key concept: BU = Spend÷Budget×100, funnel, stop at first broken layer | SKILL.md §Key concepts | ✅ full |
| 13 | Key concept: Budget drop ≠ BU drop (program shrinkage) | SKILL.md §Key concepts | ✅ full |
| 14 | Key concept: always assess ABSOLUTE BU% (0.01%→0.02% still critical) | SKILL.md §Key concepts | ✅ full |
| 15 | Budget terminology: daily / total / week budget; daily_budget = SUM over range; report which | SKILL.md §Budget terminology | ✅ full |
| 16 | `_COMMON_PROGRAM_TYPES` — PLA/Display channel filters | common-rules §STEP 0 (column rules) | ✅ full |
| 17 | Comparison mode: single-period tools; get_merchant_bu_breakdown EXCEPTION (contribution, status, spend share, pre_period_top_contributors, new_merchants) | SKILL.md §Comparison mode | ✅ full |
| 18 | Semantic pattern: "analysis for categories targeted by [campaigns]" (lookup→product_selection→extract→get_response_rate_by_dimension w/ filters, ordered) | SKILL.md §Semantic patterns | ✅ full |
| 19 | Semantic pattern: "what categories does campaign X target?" | SKILL.md §Semantic patterns | ✅ full |
| 20 | Semantic pattern: "scope analysis to campaign X's products" | SKILL.md §Semantic patterns (subsumed by #18) | ✅ full |
| 21 | Semantic pattern: "which campaigns active for keyword/category?" → get_search_query_campaigns / get_campaigns_in_category | SKILL.md §Semantic patterns | ✅ full |
| 22 | Semantic pattern: "RR / check RR for campaign X" (resolve categories → get_category_response_rates all levels) | SKILL.md §Semantic patterns (merged) | ✅ full |
| 23 | Semantic pattern: "low BU / underspend for campaign X" (+ get_campaign_performance, + quadrant if counts/BU%) | SKILL.md §Semantic patterns (merged) | ✅ full |
| 24 | "Never filter get_response_rate_by_dimension by campaign ID — returns 0" | SKILL.md §Semantic patterns | ✅ full |
| 25 | SOP escape hatch: "Skip SOP if user asks something specific — call matching tool directly" | — | ❌ missing |
| 26 | STEP 1 triage: parallel check_requests + get_true_bu_campaign_data + check_program_spend; baseline → 6 calls | SKILL.md §STEP 1 | ✅ full |
| 27 | STEP 1: present group-by dimensions (page_type/store_id/network/category_l1–l5/device); STOP & wait | SKILL.md §STEP 1 | ✅ full |
| 28 | STEP 1: get_response_rate_by_dimension w/ chosen group_by_column (no limit; scope filters only if asked) | SKILL.md §STEP 1 | ✅ full |
| 29 | 2A BU% thresholds: <5% critical / 5–30% low / >60% healthy; bu_change_pp branches (≈0&>30% stop, ≈0&<5% proceed, <−2pp drop) | SKILL.md §STEP 2 (2A) | ✅ full |
| 30 | 2B pattern classes: CONCENTRATED / UNIFORM DROP→2C / SPARSE→2C | SKILL.md §STEP 2 (2B) | ✅ full |
| 31 | 2B network drill: get_campaign_targeted_networks gate; RR ceiling via group_by_column="category_l1"+network_filter; ≥95%→ceiling; no combos→2C | SKILL.md §STEP 2 (2B network) | ⚠️ degraded |
| 32 | 2B store_id drill: get_store_level_rr_buckets; has_store_eligibility_issue=True → report & stop | SKILL.md §STEP 2 (2B store_id) | ✅ full |
| 33 | 2B device drill: no eligible SKUs / no targeting; confirm via get_campaign_performance | SKILL.md §STEP 2 (2B device) | ✅ full |
| 34 | 2B category drill: get_category_response_rates (+ quadrant ⚠️7-day if BU%/spend) | SKILL.md §STEP 2 (2B category) | ✅ full |
| 35 | 2B any-other-dimension: interpret near-0 RR, report, ask before 2C | SKILL.md §STEP 2 (2B) | ✅ full |
| 36 | 2C signal classifier: requests→3-REQUESTS / budget→3-BUDGET / RR→3-RR / mixed / both-stable→3-RR | SKILL.md §STEP 2 (2C) | ✅ full |
| 37 | STEP 3-REQUESTS full sequence (pages → checkpoint → get_category_response_rates/quadrant / Display skip → merchant_bu_breakdown → wallet → status_changes → STEP 6) | SKILL.md §STEP 3-REQUESTS | ✅ full |
| 38 | STEP 3-BUDGET sequence (campaigns_with_budget_increase; wallet+status; check_response_rate_by_page search/non-search/Display branches; low RR→HANDOFF; ceiling stop; merchant_bu_breakdown) | SKILL.md §STEP 3-BUDGET | ✅ full |
| 39 | STEP 3-RR PLA drill (search→sqrr→sq_campaigns→status; non-search→category_rr→campaigns_in_category; filters→get_filter_presence_response_rates w/ 8-filter list, 14-day) | SKILL.md §STEP 3-RR | ✅ full |
| 40 | STEP 3-RR Display drill (page_type_rr→ad_unit RR→quadrant if counts→inventory_campaigns competition→status EXTERNAL pauses→hourly_rr) | SKILL.md §STEP 3-RR | ✅ full |
| 41 | STEP 4-IR: get_page_level_performance, I/R=impr÷responses; stable→5-CTR; dropped→PLA/Display drills→merchant_bu_breakdown | SKILL.md §STEP 4-IR | ✅ full |
| 42 | STEP 5-CTR: check_ctr_overall+page CTR; dropped→ctr_breakdown→status→merchant_bu_breakdown; stable→HANDOFF to CPC | SKILL.md §STEP 5-CTR | ✅ full |
| 43 | STEP 6A: merchant_bu_breakdown 3 segments (spend drops / low-BU budget holders / budget-up flat-spend) | SKILL.md §STEP 6 (6A) | ✅ full |
| 44 | STEP 6B severity: bu%<5%→≥MEDIUM; >15pp→HIGH; 5–15pp→MEDIUM; <5pp→LOW | SKILL.md §STEP 6 (6B) | ✅ full |
| 45 | `_COMMON_PRE_SUMMARY_CHECKPOINT` (6C) | common-rules §Pre-summary checkpoint | ✅ full |
| 46 | Final Report layout + Merchants 11-column table (name…Cumulative Spend Share%), highest spenders first | SKILL.md §Final Report | ✅ full |
| 47 | `_COMMON_CROSS_AGENT` | common-rules §Storing findings (Cross-agent) | ✅ full |
| 48 | `_build_store_findings_block("bu", …, "BU drop", …)`: metric_type/severity/entity types carried; BU-specific root_cause examples | SKILL.md §STEP 6 (6C) + common-rules §Storing findings | ⚠️ degraded |
| 49 | `_COMMON_RULES_TEMPLATE` (dates/period/currency/scope-transparency/HANDOFF_TO_ROOT conditions) | common-rules §Output & tool rules | ✅ full |

## Defects

- **SKILL.md §SOP — default investigation flow — "Skip SOP if user asks something specific" escape hatch — ❌ missing.** The source states this immediately under the SOP header (line 682). It is absent from the BU SKILL. Sibling skills debug-roas, debug-cpc, debug-ctr all carry the line ("If the user asks something specific, skip the SOP and call the matching tool"), so this is a genuine omission, not a justified generalization. (common-rules Consultant behavior #1 "skip broad checks" is only a partial analog — it narrows checks, it does not authorize skipping the whole SOP.)
- **SKILL.md §STEP 6 (6C) — store_agent_findings `root_cause` examples — ⚠️ degraded.** The source `_build_store_findings_block` seeds BU-specific root_cause examples ("Request Drop on Search Pages" / "Budget Expansion Outpaced Spend" / "Network×Category Ceiling" / "Funnel Break: RR Decline"). None appear in the SKILL; only the generic ROAS-flavored examples in common-rules survive, so the BU author loses the metric-specific guidance for the root_cause value.
- **SKILL.md §STEP 2 (2B, network) — RR-ceiling stop-condition "Report and stop unless partial" — ⚠️ degraded.** Source: "RR ≥ 95% … → CEILING … Report and stop unless partial." The skill reduces this to "report/stop", dropping the "unless partial" qualifier that tells the agent to continue when the ceiling is only partial.
