# Coverage audit — `debug-campaign` vs `CAMPAIGN_DIAGNOSTIC_AGENT_INSTRUCTION`

**Verdict:** Faithful port — both SEARCH and Smart Shopping branches, all six complaint branches (3a–3g), the SOV check, the AUTO competition check, and PLA-only scope survived. **3 defects (all ⚠️ degraded, 0 ❌ missing).**

Source: `weekly_analysis_agent/prompts/agent_instructions.py` lines 1545–1687.
Blocks interpolated: `_COMMON_FIRST_STEP`, `_COMMON_CONSULTANT_BEHAVIOR`, `_COMMON_COMPETITION_CHECK`, `_COMMON_RULES_TEMPLATE`.
Correctly NOT interpolated (and correctly absent from SKILL.md's flow): store-findings, program-types, cross-agent, pre-summary. SKILL.md line 24 explicitly overrides: "This SOP ends in a diagnosis or a handoff (STEP 4), not the standard summary." PLA-only confirmed in source (lines 1545, 1677).

Element count: **45**

| # | Source element | Destination | Status |
|---|----------------|-------------|--------|
| 1 | Persona: "You are the Campaign Diagnostic Agent — single-campaign deep-dive specialist. PLA only." | Dropped (identity) + intro | ✅ dropped-justified |
| 2 | ENTRY POINTS list (low impr / high CPC / not spending / kw not spending / underperforming / paused) | SKILL.md desc + intro | ✅ full |
| 3 | `_COMMON_FIRST_STEP` (STEP 0 parallel setup, dates, user_note, program type) | common-rules §STEP 0 | ✅ full |
| 4 | "Also get agency_id, marketplace_client_id, currency, timezone from context" | SKILL.md intro (l.19–20) | ✅ full |
| 5 | `_COMMON_CONSULTANT_BEHAVIOR` (checkpoint model, discovery store, rewind) | common-rules §Consultant | ✅ full |
| 6 | STEP 1 — gather inputs (campaign ID(s), complaint type, time window) | SKILL.md §STEP 1 | ✅ full |
| 7 | STEP 1.5 — MANDATORY id-type confirmation, ASK, don't guess | SKILL.md §1.5 | ✅ full |
| 8 | STEP 1.5 — the four id-type options offered in the question (marketing_campaign_id / marketing_campaign_group_id / campaign_id / campaign_group_id) | SKILL.md §1.5 | ⚠️ degraded |
| 9 | STEP 1.5 — `lookup_campaign(raw_ids, id_type)` call | SKILL.md §1.5 | ✅ full |
| 10 | STEP 1.5 — resolved record fields (marketing_campaign_id, client_id, campaign_subtype, bidding_strategy, campaign_status, campaign_name) | SKILL.md §1.5 | ✅ full |
| 11 | STEP 1.6 — read subtype FROM lookup, do NOT ask (data authoritative) | SKILL.md §1.6 | ✅ full |
| 12 | STEP 1.6 — OS_ADS_SEARCH semantics (manual only, BROAD/EXACT/PHRASE, no AUTO) | SKILL.md §1.6 | ✅ full |
| 13 | STEP 1.6 — SMART_SHOPPING semantics (AUTO default, can add manual, AUTO-only OR AUTO+manual) | SKILL.md §1.6 | ✅ full |
| 14 | STEP 1.6 — implication: kw analysis applies to BOTH, don't skip for Smart Shopping | SKILL.md §1.6 | ✅ full |
| 15 | STEP 1.6 — brief acknowledgement guidance (don't pose as a question) | SKILL.md §1.6 | ✅ full |
| 16 | STEP 2 — `get_campaign_performance` snapshot (spend vs budget, impr/clicks/CTR/CPC, ROI/orders, daily rollup) | SKILL.md §STEP 2 | ✅ full |
| 17 | STEP 2 — "use these baseline metrics to inform the Step 3 branch" | SKILL.md §STEP 2 (implicit) | ✅ dropped-justified |
| 18 | STEP 2 — OPTIONAL merchant zoom-out: `get_merchant_keyword_performance` (auto/manual gate) + `get_merchant_category_performance` | SKILL.md §STEP 2 | ✅ full |
| 19 | STEP 2 — network targeting scope note (no default, never parallel, empty normal, retain list) | SKILL.md §STEP 2 | ✅ full |
| 20 | STEP 2.5 — 4 basic checks (product selection, wallet, true BU, status) w/ interpretations | SKILL.md §2.5 | ✅ full |
| 21 | STEP 2.5 — "if ANY fails, that IS the answer — report and stop" | SKILL.md §2.5 | ✅ full |
| 22 | 3a — `check_targeted_keyword_performance_in_campaigns` (args; client_ids REQUIRED) | SKILL.md §3a | ✅ full |
| 23 | 3a — client_ids rationale ("marketing_campaign_id is per-client, not global") | SKILL.md §3a | ✅ dropped-justified |
| 24 | 3a — aggregate AUTO-vs-MANUAL summary table (match_type/spend/impr/clicks/CPC/CTR) | SKILL.md §3a | ✅ full |
| 25 | 3a — 3 interpret cases (AUTO+MANUAL / MANUAL-only / AUTO-only) | SKILL.md §3a | ✅ full |
| 26 | 3a — conclusion format template | SKILL.md §3a | ✅ full |
| 27 | 3a SOV — `get_search_query_match_performance` REQUIRED for any low-impr complaint | SKILL.md §3a | ✅ full |
| 28 | 3a SOV — `sov` definition | SKILL.md §3a | ✅ full |
| 29 | 3a SOV — `top_search_impressions_share` definition | SKILL.md §3a | ✅ full |
| 30 | 3a SOV — 5 interpretation bullets | SKILL.md §3a | ⚠️ degraded |
| 31 | 3a SOV — report at two levels (top-5 queries + AUTO-vs-MANUAL rollup) | SKILL.md §3a | ✅ full |
| 32 | 3b — product/catalog (`get_campaign_product_selection`, `get_product_selection_changes`, `get_campaign_status_changes`) | SKILL.md §3b | ✅ full |
| 33 | 3c — "specific keyword not spending → use 3f" | SKILL.md §3c | ✅ full |
| 34 | 3c — true BU / status changes / keyword-serving-zero + escalation to keyword_delivery (HANDOFF_TO_ROOT) | SKILL.md §3c | ✅ full |
| 35 | 3c — AUTO competition check: BOTH surfaces (kw+category two-hop L3), category RR, bid comparison, AUTO caveat, verdict | SKILL.md §3c | ✅ full |
| 36 | 3f — run STEP 2.5 basics first | SKILL.md §3f | ✅ full |
| 37 | 3f — `check_requests` whole-marketplace LAST 7 DAYS (fixed window, not baseline) | SKILL.md §3f | ✅ full |
| 38 | 3f — RR ≈ 100% → COMPETITION CHECK on keyword, raise bid | SKILL.md §3f | ✅ full |
| 39 | 3f — RR low → (a) mapped vs product category, (b) keyword-in-product-name, (c) raise to engineering | SKILL.md §3f | ✅ full |
| 40 | 3d — underperforming: ROI/ROAS / CPC / CTR / BU branches + handoffs | SKILL.md §3d | ✅ full |
| 41 | 3e — paused: status changes + product-selection changes + escalate as system issue | SKILL.md §3e | ✅ full |
| 42 | 3g — competition-check surface naming per caller (3a/3c/3f) + STEP 2.5 gate | SKILL.md §3g | ✅ full |
| 43 | `_COMMON_COMPETITION_CHECK` block (symptom-by-targeting-type, 3-surface finest→coarsest, bid-not-spend conclusion, contribution) | common-rules §COMPETITION CHECK | ⚠️ degraded |
| 44 | STEP 4 — 2 handoff conditions (marketplace-wide → metric skill; keyword+campaign → keyword-delivery) | SKILL.md §STEP 4 | ✅ full |
| 45 | `_COMMON_RULES_TEMPLATE` (dates, period matching, currency, scope transparency, HANDOFF_TO_ROOT) | common-rules §Output rules | ✅ full |

## Observations (not defects)
- SKILL.md correctly refuses to invent a store-findings / pre-summary / cross-agent step for the campaign flow (the source doesn't interpolate them); the override on l.24 makes this explicit.
- Minor rationale drops that are justified: element 17 (Step-2→Step-3 linking sentence) and 23 (per-client client_ids rationale) are connective tissue, not procedure.
- common-rules.md is a shared file; its program-types and pre-summary/store-findings sections exist for the other skills and are not wrongly pulled into the campaign SOP.

## Defects
See the ⚠️ rows (8, 30, 43) — detailed in the returned bullet list.
