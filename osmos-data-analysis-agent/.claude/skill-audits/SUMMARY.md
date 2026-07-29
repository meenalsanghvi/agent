# Skill coverage audit — consolidated summary

> **RESOLVED (all 18 defects patched).** Every ❌/⚠️ below has been fixed in the
> respective `SKILL.md`; the shared competition-check header was made mechanics-only
> in `.claude/skill-common-rules.md` and re-synced to all 10 skills. This file is
> kept as the record of what was found and fixed. Re-run the auditors
> (`skill-coverage-audit-prompt.md`) to confirm a clean pass.

Each `debug-*` skill audited against the `*_AGENT_INSTRUCTION` it was ported from
(see `skill-coverage-audit-prompt.md` for method). Per-skill tables in this
folder. `❌` = element missing; `⚠️` = present but degraded (nuance watered down);
justified drops (persona line, tool input schemas) are not counted.

## Scoreboard

| Skill | Elements | ❌ missing | ⚠️ degraded | Status |
|---|---|---|---|---|
| debug-roas | ~50 | 0 | 0 | ✅ fixed (1 gap patched: `new_merchants_above_avg_cpc`) |
| debug-budget-pacing | 57 | 0 | 0 | ✅ clean |
| debug-keyword-low-rr | 34 | 0 | 0 | ✅ clean |
| debug-irrelevancy | 36 | 0 | 0 | ✅ clean |
| debug-cpc | 59 | 0 | 1 | ⚠️ minor |
| debug-ctr | 51 | 0 | 1 | ⚠️ minor |
| debug-keyword-delivery | 44 | 0 | 2 | ⚠️ minor |
| debug-campaign | 45 | 0 | 3 | ⚠️ minor |
| debug-bu | 49 | 1 | 2 | ❌ has a missing element |
| debug-rr | 69 | 1 | 7 | ❌ worst — a whole tool missing |
| **Total open** | | **2** | **16** | 18 defects across 6 skills |

## Priority 1 — `❌` missing (behavior the skill cannot perform)

1. **debug-rr — `get_search_query_rr_buckets` tool entirely absent.** Source line 877
   defines it (keyword-level RR bucketed zero/partial/full, Pareto-filtered, min-50-
   requests floor). No trace in SKILL.md → the RR skill lost a whole diagnostic step.
2. **debug-bu — "Skip SOP if user asks something specific" escape hatch missing.**
   Source line 682. Sibling skills (roas/cpc/ctr) all carry it; common-rules
   "skip broad checks" is only a partial analog and does not authorize skipping the
   whole SOP.

## Priority 2 — `⚠️` degraded (dropped tool return-fields / interpretation nuance)

**debug-rr (7):**
- `get_store_level_rr_buckets` — bucket definitions dropped; Display path
  (`program_type="display"`, `filter_store_id`) not represented (shown PLA-only).
- `check_display_page_type_rr` — interpretation mapping dropped (search_page→keyword
  campaigns inactive; category_page→category campaigns paused).
- `get_display_quadrant_performance` — reading signals dropped (low uniq_campaigns on
  high-request slot → supply gap; low BU% → delivery/budget).
- `get_search_query_response_rates` — `top_keywords_by_volume`, "Pareto keywords",
  systemic-vs-concentrated interpretation dropped.
- `get_campaigns_in_category` — "single period" caveat + `paused_campaigns` /
  `low_bu_campaigns` fields not surfaced.
- `get_campaign_inventory_performance` — "high impressions + low CTR on slot →
  creative/placement" interpretation dropped.
- `get_filter_presence_response_rates` — `rr_delta_present_minus_absent` + per-filter
  present/absent block fields not surfaced.

**debug-campaign (3):**
- STEP 3a — 5th SOV interpretation bullet dropped (Smart Shopping AUTO low-SOV +
  manual high-SOV → algorithm constrained, check 3b); low-`top_search_impressions_share`
  bullet trimmed of its actionable "combine with keyword bid table."
- STEP 1.5 — the four id-type choices to offer the user
  (`marketing_campaign_id` / `marketing_campaign_group_id` / `campaign_id` /
  `campaign_group_id`) not enumerated.
- common-rules COMPETITION CHECK header "(run only on explicit user request)"
  contradicts the campaign SOP, where 3g is auto-invoked from 3a/3c/3f gated by
  STEP 2.5 — the shared header could suppress a check the flow requires.

**debug-bu (2):**
- STEP 6 store_agent_findings — the 4 BU-specific `root_cause` example strings
  ("Request Drop on Search Pages" / "Budget Expansion Outpaced Spend" /
  "Network×Category Ceiling" / "Funnel Break: RR Decline") not carried over.
- STEP 2 (2B network) — RR-ceiling stop-condition reduced to "report/stop",
  dropping the "unless partial" qualifier.

**debug-keyword-delivery (2):**
- STEP 2 — `get_merchant_keyword_performance` breakdown structure
  (keyword × campaign_name × match_type, ranked by spend) + its purpose compressed away.
- STEP 6b — `get_targeted_keyword_competition` dropped `clicks`/`campaign_name`/
  `effective_status`, the "top 3-5 capturing traffic" focus, the "CPC meaningless for
  a CPM-bid campaign" caveat, and the "report each rival WITH its contribution" directive.

**debug-cpc (1):**
- STEP 5 — `get_targeted_keyword_competition` dropped `campaign_creation_date` +
  per-rival CTR/ROI (loses the finer rival entry-timing signal; `new_in_post` remains).

**debug-ctr (1):**
- STEP 3-B/4 — `get_sku_level_ctr_performance` nuance dropped (ranks SKUs by
  contribution to impressions change, with `status` + `ctr change`).

## Cross-cutting observation

The single shared `common-rules.md` carries the COMPETITION CHECK with the ROAS
wrapper's "(PLA only — run only on explicit user request)" header. That constraint
is ROAS's, not universal: the **campaign** SOP auto-invokes it. A shared file can't
hold one skill's gating in its header — the gate belongs in each SKILL.md, and the
shared block should state the mechanics only.
