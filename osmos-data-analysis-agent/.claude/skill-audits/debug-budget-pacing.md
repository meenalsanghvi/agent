# Coverage audit — `debug-budget-pacing` vs `BUDGET_PACING_AGENT_INSTRUCTION`

**Verdict: PASS — faithful port, 0 defects.** 57 source elements enumerated; all
preserved in SKILL.md or common-rules.md, or dropped under the whitelist. The
skill is correctly and legitimately PLA-only (source line 1043 + 1059), does not
invent a store-findings block, competition check, program-types block,
cross-agent block, or pre-summary checkpoint for this flow, and correctly states
there is no Display path.

Source: `weekly_analysis_agent/prompts/agent_instructions.py` lines 1041–1122.
Interpolates: `_COMMON_FIRST_STEP` (138), `_COMMON_CONSULTANT_BEHAVIOR` (158),
`_COMMON_RULES_TEMPLATE` (228).

| # | Source element | Destination | Status |
|---|----------------|-------------|--------|
| 1 | Persona: "You are the Budget Pacing Debugging Agent — specialist in diagnosing campaign overspend…" | Dropped | ✅ dropped-justified (persona whitelist) |
| 2 | PLA-only statement — "for PLA ONLY. Display ads do not use budget pacing" | SKILL.md (desc + override #1 + Program-type completeness) | ✅ full |
| 3 | Tool whitelist framing — "THESE ARE THE ONLY TOOLS… Do NOT call any other tool name, ever" | SKILL.md §Tool whitelist | ✅ full |
| 4 | State tools list (update_context … get_discoveries) | SKILL.md §Tool whitelist | ✅ full |
| 5 | `lookup_campaign` nuance — resolve any ID type → marketing_campaign_id | SKILL.md §Tool whitelist | ✅ full |
| 6 | `lookup_merchant` nuance — only if merchant referenced; rare, campaign-level | SKILL.md §Tool whitelist | ✅ full |
| 7 | `get_budget_delivery_mode` — ACCELERATED vs STANDARD (MANDATORY first diagnostic) | SKILL.md §Tool whitelist | ✅ full |
| 8 | `get_budget_pacing_buckets` — pacing buckets for marketplace + date | SKILL.md §Tool whitelist | ✅ full |
| 9 | `get_campaign_daily_budget` — effective daily budget on date | SKILL.md §Tool whitelist | ✅ full |
| 10 | `get_minute_level_cpc_data` — clicks + spend (CPC) | SKILL.md §Tool whitelist | ✅ full |
| 11 | `get_minute_level_cpm_data` — impressions + spend (CPM) | SKILL.md §Tool whitelist | ✅ full |
| 12 | `check_budget_changes_on_date` — budget-change audit events on date | SKILL.md §Tool whitelist | ✅ full |
| 13 | FIRST_STEP: STEP 0 parallel setup (get_context/date_ranges/all_findings/discoveries) | common-rules.md §STEP 0 | ✅ full |
| 14 | FIRST_STEP: date validation (no dates / differ / match) + set_date_ranges | common-rules.md §STEP 0 Dates | ✅ full |
| 15 | FIRST_STEP: current-year date rule | common-rules.md §STEP 0 Dates | ✅ full |
| 16 | FIRST_STEP: user_note check for IDs/entities | common-rules.md §STEP 0 user_note | ✅ full |
| 17 | FIRST_STEP: program-type confirm gate | common-rules.md §STEP 0 (correctly overridden by skill override #1) | ✅ full |
| 18 | FIRST_STEP: "Pass affected_program to all tools as program_type" | common-rules.md §STEP 0 | ✅ full |
| 19 | Extra: also get marketplace_client_id, agency_id, timezone from context | SKILL.md intro (line 18) | ✅ full |
| 20 | PROGRAM TYPE OVERRIDE — PLA-only always; never ask; skip program confirmation | SKILL.md override #1 | ✅ full |
| 21 | CONSULTANT: narrowed scope → skip broad; listen for entities (behaviors 1,2) | common-rules.md §Consultant behavior | ✅ full |
| 22 | CONSULTANT: interactive checkpoint model (parts a–d + template) | common-rules.md §Consultant behavior | ✅ full |
| 23 | CONSULTANT: honour choice / never silently substitute | common-rules.md §Consultant behavior | ✅ full |
| 24 | CONSULTANT: mid-conversation date change → set_date_ranges, restart STEP 1 | common-rules.md §Consultant behavior | ✅ full |
| 25 | CONSULTANT: discovery store + check get_discoveries before re-query | common-rules.md §Consultant behavior | ✅ full |
| 26 | CONSULTANT: rewind behavior | common-rules.md §Consultant behavior | ✅ full |
| 27 | CONSULTANT: checkpoint exception for STEP 0 setup calls | common-rules.md §Consultant behavior | ✅ full |
| 28 | CONSULTANT: remember filters (4); tool order (5); broad-request flow (6) | common-rules.md §Consultant behavior | ✅ full |
| 29 | CONSULTANT: interactive behavior = SOP agents only (data_agent excluded) | common-rules.md ("SOP skills only") | ✅ full |
| 30 | STEP 1 — ask only for missing inputs: campaign(s), date, CPC/CPM | SKILL.md §STEP 1 | ✅ full |
| 31 | STEP 1.5 — resolve IDs via lookup_campaign(raw_ids), extract mkt_campaign_id, name failures | SKILL.md §STEP 1.5 | ✅ full |
| 32 | STEP 1.75 — ACCELERATED branch conclusion + STOP (no Steps 2–4) | SKILL.md §STEP 1.75 | ✅ full |
| 33 | STEP 1.75 — STANDARD branch → proceed | SKILL.md §STEP 1.75 | ✅ full |
| 34 | STEP 1.75 — Mixed branch → call out ACCELERATED, proceed with STANDARD | SKILL.md §STEP 1.75 | ✅ full |
| 35 | STEP 1.9 — user already said CPC/CPM → use it | SKILL.md §STEP 1.9 | ✅ full |
| 36 | STEP 1.9 — else ASK EXACTLY [verbatim prompt] then STOP | SKILL.md §STEP 1.9 | ✅ full |
| 37 | STEP 1.9 — NEVER guess / NEVER call both / NEVER call before confirm | SKILL.md §STEP 1.9 | ✅ full |
| 38 | STEP 2 — parallel, STANDARD only, confirmed strategy | SKILL.md §STEP 2 | ✅ full |
| 39 | STEP 2a — get_budget_pacing_buckets | SKILL.md §STEP 2 | ✅ full |
| 40 | STEP 2b — get_campaign_daily_budget | SKILL.md §STEP 2 | ✅ full |
| 41 | STEP 2c — ONE minute tool; field breakdown (CPC: campaign/page_type/hour/min; CPM: campaign_group/hour/min) | SKILL.md §STEP 2 | ✅ full |
| 42 | STEP 3 — expected_spend = daily_budget × bucket_pct/100; sum actual per bucket | SKILL.md §STEP 3 | ✅ full |
| 43 | STEP 3 — CPC data split by page_type into SEARCH / NON-SEARCH | SKILL.md §STEP 3 | ✅ full |
| 44 | STEP 3 — identify buckets where actual > expected (overspend) | SKILL.md §STEP 3 | ✅ full |
| 45 | STEP 4 Rule 1 — budget update; 40-min window; both branches (correlated / not correlated → raise to backend) | SKILL.md §STEP 4 | ✅ full |
| 46 | STEP 4 Rule 2 — sudden click traffic; CPC-only, NON-SEARCH-only; consecutive 10-min window, no gaps | SKILL.md §STEP 4 | ✅ full |
| 47 | STEP 4 Rule 3 — search-page pacing limitation (pacing only pauses non-search) | SKILL.md §STEP 4 | ✅ full |
| 48 | STEP 4 — none-match fallback: raw comparison + flag manual investigation | SKILL.md §STEP 4 | ✅ full |
| 49 | RULES: date format YYYY-MM-DD, no trailing chars | common-rules.md §Output & tool rules | ✅ full |
| 50 | RULES: period matching (check `period` field) | common-rules.md §Output & tool rules | ✅ full |
| 51 | RULES: call get_context/all_findings once (STEP 0) | common-rules.md §STEP 0 | ✅ full |
| 52 | RULES: store_discovery after entity-returning calls | common-rules.md §Consultant behavior | ✅ full |
| 53 | RULES: currency prefix on all monetary values | common-rules.md §Output & tool rules | ✅ full |
| 54 | RULES: choose tools dynamically | common-rules.md §Consultant behavior (#5) | ✅ full |
| 55 | RULES: CRITICAL store_agent_findings() before final summary | common-rules.md §Storing findings (preserved verbatim) | ✅ full — see Observation 1 |
| 56 | RULES: scope transparency (say so if unanswerable; list available tools) | common-rules.md §Output & tool rules | ✅ full |
| 57 | RULES: HANDOFF_TO_ROOT conditions (5 triggers; never ask for agency_id) | common-rules.md §Output & tool rules | ✅ full |

## Defects
None.

## Observations (not defects)

1. **store_agent_findings override.** `_COMMON_RULES_TEMPLATE` (interpolated) carries
   the "CRITICAL: MUST call store_agent_findings() before any final summary" rule,
   and it is preserved verbatim in common-rules.md. SKILL.md override #2 relaxes it
   to optional ("You may still store_agent_findings if useful, but it is not
   required"). This is legitimate and aligned with the source: this SOP does NOT
   interpolate `_build_store_findings_block` and has no final-report step — it ends
   at the STEP 4 diagnosis text. The relaxation therefore does not degrade a source
   behavior the pacing agent actually performs. Recorded as an observation, not a
   defect.

2. **Shared reference file scope.** common-rules.md is the shared file across all
   debug-* skills and contains blocks this instruction does not interpolate
   (pre-summary checkpoint, store-findings, competition check, program-types union,
   cross-agent, final-report skeleton). SKILL.md correctly does NOT invoke any of
   these for the pacing flow: it scopes its common-rules read to "STEP 0 context
   setup, date handling, the interactive checkpoint model, and output/hand-off
   rules," and override #2 explicitly disclaims the pre-summary/store/final-report.
   No invention.

3. **PLA-only confirmed at source.** Source line 1043 ("for PLA (Product Ads) ONLY.
   Display ads do not use budget pacing") and line 1059 PROGRAM TYPE OVERRIDE
   establish this is PLA-only by design; the skill's PLA-only stance and "no
   Display path" statement are correct, not a silently-dropped Display path.
