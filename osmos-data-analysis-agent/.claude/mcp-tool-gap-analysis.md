# MCP Tool Gap Analysis — SOP tools vs existing MCP tools

_Date: 2026-07-22. Scope: the tools the 10 skills reference (from
`weekly_analysis_agent/tools/__init__.py`) vs the MCP tools currently connected in
this environment._

## Headline

- **~63 analytical/query tools** are referenced by the skills.
- **The large majority (~50) have NO existing MCP equivalent** — they are custom
  BigQuery aggregations that produce SOP-shaped output (comparison deltas,
  contribution %, verdicts, Pareto lists). These need **new KAM report configs**
  OR the **existing ADK Python tools re-exposed as an MCP server** (see Two paths).
- **~8 metadata/lookup tools PARTIALLY map** to `osmos-campaign-management-mcp`
  (candidates to reuse — verify schema/granularity).
- **~12 state/session tools are NOT KAM at all** — they map to Claude Code's native
  conversation context / memory.
- **1 opportunity:** `get_keyword_floor_bids` (already in the campaign MCP) can fill
  the floor-check gap the CPC skill currently hands to the user.

## Connected MCP tools (inventory)

- **osmos-campaign-management-mcp:** `list_campaigns`, `get_sponsored_product_ads_campaign_details`,
  `get_sponsored_display_ads_campaign_details`, `get_adgroups`, `get_adgroup_product_list`,
  `get_adgroup_product_lists_bulk`, `get_sponsored_product_ads_adgroup_keyword_list`,
  `get_sponsored_display_ads_adgroup_keyword_list`, `get_keyword_lists_bulk`,
  `get_keyword_floor_bids`, `get_adgroup_suggestions(_bulk)`, `get_brand_conquesting_config`,
  `get_inventory_details`, `get_campaigns_by_wallet`, `get_wallet_transaction_logs`,
  `get_adgroup_audit_logs`
- **osmos-reporting-mcp / -pulse:** `run_report`, `get_sponsored_product_ads_reports`,
  `get_sponsored_display_ads_reports`, `get_offsite_ads_reports`, `get_instore_digital_ads_reports`
- **kamService (repo, not connected here):** `run_kam_report`, `get_kam_query`, `post_kam_config`

## Legend
`MATCH` = existing tool covers it · `PARTIAL` = candidate, verify schema/granularity ·
`NONE` = no equivalent → new KAM config or re-expose ADK tool

---

## Group 1 — Analytical / metric aggregations (core SOP engines) → NONE

These produce comparison-mode, contribution-%, verdict-bearing output. No existing
MCP tool returns this shape. **New KAM config OR re-expose ADK Python tool.**

| SOP tool | Skill(s) | Verdict |
|---|---|---|
| check_gmv_attribution | roas | NONE |
| get_daily_order_trends | roas | NONE |
| get_merchant_breakdown | roas | NONE |
| get_sku_level_performance | roas | NONE |
| get_target_roi | roas | NONE |
| get_merchant_cpc_breakdown | cpc, roas | NONE |
| get_campaign_subtype_cpc_breakdown | cpc | NONE |
| get_merchant_category_cpc_comparison | cpc | NONE |
| get_sku_level_cpc_performance | cpc | NONE |
| check_ctr_overall | ctr, bu | NONE |
| get_merchant_ctr_breakdown | ctr, bu | NONE |
| get_sku_level_ctr_performance | ctr | NONE |
| get_keyword_seller_breakdown | ctr, cpc | NONE |
| get_page_level_performance | cpc, ctr, bu | NONE |
| get_category_level_performance | roas, ctr | NONE |
| get_campaigns_in_category | roas, cpc, rr, kw | NONE |
| get_search_query_performance | roas, cpc, ctr, kw | NONE |
| get_search_query_match_performance | ctr, kw, campaign | NONE |
| get_merchant_keyword_performance | roas, cpc, ctr, kw | NONE |
| get_merchant_category_performance | roas, cpc, ctr, kw | NONE |
| get_targeted_keyword_competition | cpc, ctr, kw, campaign | NONE |
| check_targeted_keyword_performance_in_campaigns | kw-delivery, campaign | NONE |
| check_program_spend | bu | NONE |
| check_requests | bu, rr, campaign | NONE |
| get_merchant_bu_breakdown | bu | NONE |
| get_true_bu_campaign_data | bu, rr, kw-low-rr, campaign | NONE |
| get_category_quadrant_performance | bu, rr | NONE |
| get_display_quadrant_performance | bu, rr | NONE |
| get_display_ad_unit_performance | bu, rr, ctr | NONE |
| get_display_inventory_campaigns | bu, rr | NONE |
| get_campaign_inventory_performance | bu, rr | NONE |
| check_response_rate_by_page | bu, rr | NONE |
| get_search_query_response_rates | bu, rr | NONE |
| get_search_query_rr_buckets | rr | NONE |
| get_search_query_campaigns | bu, rr | NONE |
| get_category_response_rates | bu, rr, kw-low-rr, campaign | NONE |
| get_merchant_rr_breakdown | rr | NONE |
| get_response_rate_by_dimension | bu, rr, kw-low-rr | NONE |
| check_display_page_type_rr | bu, rr | NONE |
| check_display_hourly_rr | bu, rr | NONE |
| get_problem_metrics | root/all | NONE |

## Group 2 — Campaign / merchant metadata & lookups → PARTIAL (reuse candidates)

Verify each candidate's granularity — the campaign MCP is often **ad-group** level
while the SOP tools are **campaign/merchant** level, and ID-type coverage differs.

| SOP tool | Candidate existing MCP tool | Verdict |
|---|---|---|
| lookup_campaign | `list_campaigns` + `get_sponsored_product_ads_campaign_details` | PARTIAL — must resolve all 4 ID types (marketing/campaign × id/group) |
| lookup_merchant | `get_campaigns_by_wallet` (weak) | PARTIAL / NONE — no clean client↔seller↔merchant resolver |
| get_campaign_product_selection | `get_adgroup_product_list` | PARTIAL — ad-group granularity; needs roll-up to campaign |
| get_campaign_targeted_keywords | `get_sponsored_product_ads_adgroup_keyword_list` | PARTIAL — SOP needs bidding_value + negative_keywords + match_type |
| get_campaign_targeted_networks | — | NONE |
| get_campaign_status_changes | `get_adgroup_audit_logs` | PARTIAL — ad-group audit; SOP wants campaign status events + changed_by_type=EXTERNAL |
| get_product_selection_changes | `get_adgroup_audit_logs` | PARTIAL — same audit source, product add/remove events |
| get_merchant_wallet_balance | `get_campaigns_by_wallet` / `get_wallet_transaction_logs` | PARTIAL — balance vs transactions |
| get_campaign_performance | `get_sponsored_product_ads_reports` / `run_report` | PARTIAL — reporting backend; needs comparison-mode shaping |

## Group 3 — Raw-log / audit / S3 / pacing specialty → NONE

Hit raw request tables, S3 keyword-category files, minute-level, or pacing config —
no reporting equivalent. **New KAM config OR re-expose ADK tool.**

| SOP tool | Skill(s) | Verdict |
|---|---|---|
| get_category_request_volume | bu, rr | NONE (raw request table, 15-day) |
| get_filter_presence_response_rates | bu, rr | NONE (raw request log, 14-day) |
| get_store_level_rr_buckets | bu, rr | NONE (hourly store buckets) |
| get_keyword_categories | kw-delivery, kw-low-rr, irrelevancy | NONE (S3 keyword-category files) |
| get_responded_skus | irrelevancy | NONE (per keyword×cache_type×SKU) |
| check_keyword_request_volume | kw-delivery, kw-low-rr | NONE (>100/7-day threshold) |
| get_minute_level_cpc_data | budget-pacing | NONE |
| get_minute_level_cpm_data | budget-pacing | NONE |
| get_budget_pacing_buckets | budget-pacing | NONE |
| get_campaign_daily_budget | budget-pacing | NONE |
| check_budget_changes_on_date | budget-pacing | NONE |
| get_budget_delivery_mode | budget-pacing | NONE |
| get_table_info / execute_sql | deep-dive | NONE (raw BQ access) |

## Group 4 — State / session tools → NATIVE to Claude Code (not KAM, not MCP)

The ADK session-state layer. In Claude Code these map to native conversation
context / memory, not data tools — do NOT build KAM configs for these.

`get_context`, `update_context`, `get_date_ranges`, `set_date_ranges`, `get_today`,
`compute_week_range`, `update_analysis`, `store_agent_findings`, `get_all_findings`,
`store_discovery`, `get_discoveries`, `fetch_marketplace_info`.

- `fetch_marketplace_info` (fuzzy marketplace → agency_id/region/timezone) is the one
  that still needs a real data lookup → small MCP tool or KAM config.
- `store_agent_findings` / `get_all_findings` (cross-skill findings) → a lightweight
  memory/MCP shim if we want cross-skill hand-off; otherwise skill-managed in-context.

## Group 5 — Opportunities (existing MCP tools that could IMPROVE the SOPs)

| Existing MCP tool | Use |
|---|---|
| `get_keyword_floor_bids` | **Fills the CPC floor-check gap** — the CPC skill currently asks the user to check floors (no tool). This could fetch them directly. |
| `get_sponsored_display_ads_campaign_details` / `_adgroup_keyword_list` | Back some Display metadata drills. |
| `get_inventory_details` | Potential input for Display inventory/slot analysis. |

---

## Two paths to wire (recommendation)

For every Group 1 / Group 3 `NONE`:

1. **Re-expose the existing ADK Python tools as one MCP server (fastest).** They
   already produce the exact SOP-shaped output the skills expect (comparison mode,
   contribution %, verdicts) and the Python derived-math layer is already written.
   Closes the gap immediately; naming aligns 1:1 with the skills' tool references.
2. **Author new KAM report configs (governed, longer-term).** Data flows through
   KAM (`run_report` / `run_kam_report`); KAM returns raw aggregates and the Python
   math layer computes the derived metrics. Centralized, cached, reusable by other
   consumers — but ~50 configs to author.

**Suggested plan:** start with path 1 (re-expose ADK tools) to get the skills
runnable in Claude Code end-to-end, reuse the Group 2 `osmos-campaign-management`
tools where schema matches, adopt `get_keyword_floor_bids` for the floor gap, and
migrate the heaviest/most-reused queries to KAM configs (path 2) over time.

## Naming reconciliation (either path)
MCP tools are namespaced (e.g. `mcp__osmos__get_merchant_breakdown`). The skills
reference bare logical names. Align the MCP tool names to the skills' names (or
update the skills' references) so Claude maps them unambiguously — this is why the
skills carry the "tool-binding note" in `common-rules.md`.
