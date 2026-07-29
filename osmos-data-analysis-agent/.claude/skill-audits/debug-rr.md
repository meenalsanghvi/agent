# Coverage audit — `debug-rr` vs `RR_AGENT_INSTRUCTION`

**Verdict: FAITHFUL WITH DEFECTS — 8 defects (1 missing tool ❌, 7 degraded nuances ⚠️) across 69 audited elements.**

Source: `RR_AGENT_INSTRUCTION` (lines 831–1038, `weekly_analysis_agent/prompts/agent_instructions.py`), expanding `_COMMON_FIRST_STEP`, `_COMMON_CONSULTANT_BEHAVIOR`, `_COMMON_PROGRAM_TYPES`, `_COMMON_PRE_SUMMARY_CHECKPOINT`, `_COMMON_CROSS_AGENT`, `_COMMON_RULES_TEMPLATE`, `_build_store_findings_block`.
Skill: `.claude/skills/debug-rr/SKILL.md` + `references/common-rules.md`.

Status legend: ✅ full · ✅ dropped-justified · ⚠️ degraded · ❌ missing.

| # | Source element | Destination | Status |
|---|----------------|-------------|--------|
| 1 | Persona: "You are the Response Rate (RR) Debugging Agent — specialist in ad response rate changes." | Dropped | ✅ dropped-justified (persona line) |
| 2 | `_COMMON_FIRST_STEP` — STEP 0 one-time parallel setup (get_context/get_date_ranges/get_all_findings/get_discoveries), don't re-call | common-rules §STEP 0 | ✅ full |
| 3 | `_COMMON_FIRST_STEP` — date validation + current-year default rule | common-rules §STEP 0 Dates | ✅ full |
| 4 | `_COMMON_FIRST_STEP` — user_note check for entity IDs | common-rules §STEP 0 user_note | ✅ full |
| 5 | `_COMMON_FIRST_STEP` — confirm program type, pass as `program_type` | common-rules §STEP 0 Program type | ✅ full |
| 6 | "Also get marketplace_client_id, region, timezone from context" | SKILL.md §intro (l.19) | ✅ full |
| 7 | Data-retention gate: 15-day (category_request_volume, filter_presence), 7-day (category_quadrant), warning format | SKILL.md §Data-retention gate | ✅ full (correctly adds display_quadrant under 7-day) |
| 8 | `_COMMON_CONSULTANT_BEHAVIOR` — narrowed scope / listen for entities | common-rules §Consultant behavior 1–2 | ✅ full |
| 9 | `_COMMON_CONSULTANT_BEHAVIOR` — interactive checkpoint model + 4-part format + honour choice + rewind | common-rules §Checkpoint format | ✅ full |
| 10 | `_COMMON_CONSULTANT_BEHAVIOR` — mid-conversation date change (set_date_ranges, restart step 1, skip step 0) | common-rules §Consultant behavior | ✅ full |
| 11 | `_COMMON_CONSULTANT_BEHAVIOR` — discovery store / get_discoveries before re-query | common-rules §Discovery store | ✅ full |
| 12 | `_COMMON_CONSULTANT_BEHAVIOR` — remember filters, dynamic tool order, broad-request default flow, data_agent-only note | common-rules §Consultant behavior 4–6 | ✅ full |
| 13 | Key concept: RR = (Non-Zero Responses/Requests)×100; drop = fewer requests filled, impacts BU | SKILL.md §Key concepts | ✅ full |
| 14 | Key concept: page types have different RR (search typically higher) | SKILL.md §Key concepts | ✅ full |
| 15 | Budget terminology: daily/total/week budget; `daily_budget` = SUM over range, divide by N | SKILL.md §Key concepts | ✅ full |
| 16 | `_COMMON_PROGRAM_TYPES`: PLA=os_product_ads; Display=guaranteed/auction_display_ads | common-rules §STEP 0 column rules | ✅ full |
| 17 | Tool `check_requests` — overall request/response counts, confirms RR drop + volume change | SKILL.md STEP 1 + Reading | ✅ full |
| 18 | Tool `check_response_rate_by_page` — RR by page type; returns search_page_affected, non_search_pages_affected | SKILL.md STEP 1 + Reading | ✅ full |
| 19 | Tool `get_response_rate_by_dimension` — call w/o group_by → available_columns → ask; w/ group_by → breakdown; PLA vs Display dims; filters (store_id_filter→filter_store_id); campaign-scope via categories; no retention limit | SKILL.md STEP 2 + Program-type completeness + Semantic patterns | ✅ full (dim enumerations obtained via the preserved available_columns mechanism) |
| 20 | Tool `get_filter_presence_response_rates` — PLA, per-filter present/absent blocks + `rr_delta_present_minus_absent`; filter list; recent 14 days; use late | SKILL.md STEP 3-A/3-C + Reading (l.168) | ⚠️ degraded — named return field `rr_delta_present_minus_absent` and present/absent block fields (request_share_pct etc.) not surfaced (interpretation retained) |
| 21 | Tool `get_store_level_rr_buckets` — both PLA & Display (program_type); hourly store×day×hour buckets zero(<1%)/partial/full; summed totals not hour rows; adjusted_rr_excluding_ineligible, has_store_eligibility_issue; prerequisite | SKILL.md STEP 2 store_id | ⚠️ degraded — bucket definitions dropped and the Display path (program_type="display" / filter_store_id) not represented (skill shows it PLA-only) |
| 22 | Tool `check_display_page_type_rr` — DISPLAY ONLY; RR by page_type; interpretation: search_page_affected→keyword campaigns inactive, category_page_affected→category campaigns paused | SKILL.md STEP 4 | ⚠️ degraded — the page-type→campaign-type interpretation (l.1015) dropped |
| 23 | Tool `check_display_hourly_rr` — DISPLAY ONLY; low-activity hours (<10%); adjusted_rr_active_hours, has_hourly_pattern, ad_units_without_campaigns; prerequisite | SKILL.md STEP 4 | ✅ full |
| 24 | Tool `get_display_ad_unit_performance` — Display ad unit breakdown, display only | SKILL.md STEP 4 + Program-type completeness | ✅ full |
| 25 | Tool `get_display_quadrant_performance` — page_type+ad_unit quadrant, BU%/spend/I/R/uniq campaigns-merchants; ⚠️7-day; prefer RR tools; signals: low uniq on high-request slot→supply gap, low BU%→delivery/budget, compare periods for lost campaigns | SKILL.md STEP 4 + Program-type completeness | ⚠️ degraded — reading signals (l.1016) dropped; only the ⚠️7-day/prefer-alternative note kept |
| 26 | Tool `get_display_inventory_campaigns` — AD UNIT→CAMPAIGNS; who competes on slot; outcompeted / UNKNOWN-strategy / 0-budget signals | SKILL.md STEP 4 + Reading (l.161) | ✅ full |
| 27 | Tool `get_campaign_inventory_performance` — CAMPAIGN→AD UNITS; few slots→limited reach, high-impr-low-CTR→creative/placement, zero spend→not winning | SKILL.md Reading (l.163) | ⚠️ degraded — "high impressions but low CTR → creative/placement issue" interpretation dropped |
| 28 | Tool `get_category_request_volume` — request volume by L1/L2/L3; categories_with_request_increase | SKILL.md STEP 3-A | ✅ full (field paraphrased as "categories with request increases") |
| 29 | Tool `get_search_query_response_rates` — keyword-level RR for search; Pareto keywords; top_keywords_by_volume; systemic vs concentrated | SKILL.md STEP 3-A/3-C | ⚠️ degraded — named field `top_keywords_by_volume`, the "Pareto" nuance, and the "systemic (many) vs concentrated" interpretation (l.1004) dropped |
| 30 | Tool `get_search_query_rr_buckets` — keyword-level RR bucketed zero/partial/full; Pareto-filtered, min 50 requests | — | ❌ missing — tool absent from SKILL.md entirely |
| 31 | Tool `get_search_query_campaigns` — campaigns for queries + effective_status; campaigns_lost, paused_campaigns, all_campaign_ids, all_client_ids; use after search_query_RR | SKILL.md STEP 3-A/3-C + Reading (l.147) | ✅ full |
| 32 | Tool `get_campaign_targeted_keywords` — SEARCH ONLY; (text, bidding_value=manual bid), negative_keywords; ask "Is this a Search campaign?" first; feed text→keywords_filter | SKILL.md Reading (l.149) + STEP 3-A | ✅ full |
| 33 | Tool `get_campaign_targeted_networks` — networks a campaign targets; scope network drills; missing-from-stream signal | SKILL.md STEP 2 + Reading (l.153) | ✅ full |
| 34 | Tool `get_keyword_categories` — categories mapped to keyword(s); PLA only; "what categories is keyword X mapped to?" | SKILL.md Reading (l.172) | ✅ full (S3/ranked-by detail trimmed, non-load-bearing) |
| 35 | Tool `get_category_response_rates` — category-level RR non-search; sort_by option | SKILL.md STEP 2/3-A/3-B/3-C | ✅ full (sort_by/agency_id are param signature — justified) |
| 36 | Tool `get_category_quadrant_performance` — category BU%/spend/uniq campaigns-merchants; ⚠️7-day; prefer RR tools; BU<75% signal | SKILL.md Reading (l.165) + STEP 3 | ✅ full |
| 37 | Tool `get_campaigns_in_category` — campaigns in category (PLA), flags paused + low BU, single period, accepts client_ids/marketing_campaign_ids | SKILL.md STEP 3-A + Semantic patterns | ⚠️ degraded — the "single period" caveat and named fields paused_campaigns/low_bu_campaigns (l.1009) not surfaced |
| 38 | Tool `get_merchant_rr_breakdown` — comparison mode; ranks by contribution to IMPRESSIONS change; status, impression share, pre_period_top_contributors, new_merchants; amplification caveat | SKILL.md STEP 5 | ✅ full |
| 39 | Tool `get_true_bu_campaign_data` — campaigns_paused_count, budget_drop_net_lost, sellers_with_zero_spend_count; Scenario B | SKILL.md STEP 3-B + Reading (l.156) | ✅ full |
| 40 | Tool `get_merchant_wallet_balance` — wallet balance; cross-ref zero_balance | SKILL.md STEP 3-B + Reading (l.157) | ✅ full |
| 41 | Tool `get_campaign_status_changes` — audit; changed_by_type=EXTERNAL=user-initiated | SKILL.md STEP 3 + Reading (l.159) | ✅ full |
| 42 | Tool `get_product_selection_changes` — audit; SKU removals reduce eligibility | SKILL.md STEP 3 + Reading (l.160) | ✅ full |
| 43 | Tool `get_campaign_product_selection` — current active products; resolve group_id via lookup_campaign; extract categories | SKILL.md Semantic patterns | ✅ full |
| 44 | Tool `get_campaign_performance` — campaign-level; accepts marketing_campaign_ids/client_ids/seller_ids | SKILL.md Semantic patterns (l.40) | ✅ full |
| 45 | State tools list | common-rules (§STEP 0 + §Output & tool rules) | ✅ full |
| 46 | Semantic pattern: network/store/category analysis for categories targeted by [campaign IDs] (resolve categories, steps 1–3 before 4) | SKILL.md Semantic patterns | ✅ full |
| 47 | Semantic pattern: "what categories does campaign X target?" | SKILL.md Semantic patterns | ✅ full |
| 48 | Semantic pattern: "which campaigns active for keyword/category?" | SKILL.md Semantic patterns | ✅ full |
| 49 | Semantic pattern: "RR for campaign X" — resolve categories → get_category_response_rates all levels; never filter get_response_rate_by_dimension by campaign ID | SKILL.md Semantic patterns | ✅ full |
| 50 | Semantic pattern: "low BU / underspend for campaign X" — lookup_campaign → get_campaign_performance → product selection → category RR (+ quadrant if BU%) | SKILL.md Semantic patterns | ✅ full |
| 51 | SOP escape hatch: "Skip SOP if user asks something specific — call matching tool directly" | common-rules §Consultant behavior 1 | ✅ full (covered by "narrowed scope → skip broad checks") |
| 52 | STEP 1 — Triage: 4 parallel calls (check_requests ×2 + check_response_rate_by_page ×2) | SKILL.md STEP 1 | ✅ full |
| 53 | STEP 2 — Scenario A (requests up + responses didn't keep up) | SKILL.md STEP 2 | ✅ full |
| 54 | STEP 2 — Scenario B (budget dropped) | SKILL.md STEP 2 | ✅ full |
| 55 | STEP 2 — Scenario C (requests + budget stable, responses dropped) | SKILL.md STEP 2 | ✅ full |
| 56 | STEP 2 — dimension drill-down + follow-ups (network/store_id/category/device) | SKILL.md STEP 2 | ✅ full |
| 57 | STEP 3-A — requests increased (non-search + search paths) → STEP 5 | SKILL.md STEP 3-A | ✅ full |
| 58 | STEP 3-B — budget dropped → STEP 5 | SKILL.md STEP 3-B | ✅ full |
| 59 | STEP 3-C — responses dropped → STEP 5 | SKILL.md STEP 3-C | ✅ full |
| 60 | STEP 4-DISPLAY — full Display path (ad_unit→page_type→hourly→inventory→status) | SKILL.md STEP 4 | ✅ full |
| 61 | STEP 5-MERCHANTS — get_merchant_rr_breakdown comparison mode | SKILL.md STEP 5 | ✅ full |
| 62 | STEP 6-SUMMARY — `_COMMON_PRE_SUMMARY_CHECKPOINT` | common-rules §Pre-summary checkpoint | ✅ full |
| 63 | Interpretation: check_requests (avg_response_percentage, Scenario A) | SKILL.md Reading | ✅ full |
| 64 | Interpretation: check_response_rate_by_page (search→keyword, non-search→category drill) | SKILL.md Reading | ✅ full |
| 65 | Interpretation: get_response_rate_by_dimension (dimension_value keyed rows; one segment near-0 while others high → isolated) | SKILL.md STEP 2 follow-ups | ✅ full (isolation logic preserved in per-dimension follow-ups) |
| 66 | `_COMMON_CROSS_AGENT` — get_all_findings once, note overlaps | common-rules §Cross-agent | ✅ full |
| 67 | `_build_store_findings_block("rr", …)` — metric_type rr, severity by RR drop %, entity types keyword/category/page_type | SKILL.md STEP 6 + common-rules §Storing findings | ✅ full |
| 68 | Final Report table columns (Page Types / Keywords / Categories / Merchants full 11-col + change; Root Cause/Programs/Pages) | SKILL.md §Final Report | ✅ full |
| 69 | `_COMMON_RULES_TEMPLATE` — date format, period matching, get_context once, store_discovery, currency, store_agent_findings first, scope transparency, HANDOFF_TO_ROOT | common-rules §Output & tool rules | ✅ full |

## Observations (not defects)
- RR source does **not** interpolate `_COMMON_COMPETITION_CHECK`, and SKILL.md correctly contains no competition-check path. `references/common-rules.md` still carries the shared COMPETITION CHECK section — harmless, since it is a shared file and the RR SKILL.md never invokes it.
- The data-retention gate correctly consolidates `get_display_quadrant_performance` under the 7-day limit; the source lists only `get_category_quadrant_performance` in its gate paragraph but states the 7-day limit at the `get_display_quadrant_performance` tool line — the skill's consolidation is a faithful clarification.
