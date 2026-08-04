---
name: debug-budget-pacing
description: >-
  Diagnose campaign OVERSPEND caused by budget pacing for an OnlineSales
  marketplace. Use when the user asks why a campaign overspent, spent its budget
  too fast, front-loaded spend, burned budget early in the day, or paced badly on a
  specific date. PLA (Product Ads) ONLY — Display does not use budget pacing.
  Compares actual vs expected minute-level spend per pacing bucket and diagnoses
  the overspend cause. Not for underspend / low budget utilisation (use debug-bu)
  or ROI/CPC/CTR/RR questions (use those skills).
---

# Diagnosing budget-pacing overspend

> **Every data call below is `run_report(reportType=…, attributes=[…], metrics=[…], dateRanges=[…], filters=[…])`** against the report named at each step. Report groups are discoverable via the `get_<group>s_reports` tools. Resolve exact column names via `knowledge/tool-map.md` — never from memory.

You are diagnosing campaign **overspend** from budget pacing. **Read
`references/common-rules.md`** for the STEP 0 context setup, date handling, the
interactive checkpoint model, and the output/hand-off rules. Also pull
`marketplace_client_id`, `agency_id`, and `timezone` from context.

**Two overrides vs the shared rules:**
1. **PLA-only, always.** Do NOT ask about program type or PLA-vs-Display — treat
   `affected_program` as `"pla"` even if context says otherwise. **Skip the
   program-confirmation gate** in `common-rules.md` STEP 0. (Display does not use
   budget pacing.)
2. **This SOP ends in a diagnosis, not the standard summary.** There is no
   pre-summary checkpoint / final-report table
   for this skill — conclude with the diagnosis text from STEP 4. 

## Tool whitelist — these are the ONLY tools; never call another
- `CAMPAIGN_LOOKUP_REPORT` — resolve any campaign ID to the `marketing_campaign_id` the
  other tools need.
- `MERCHANT_LOOKUP_REPORT` — only if the user references a merchant and you need its IDs
  (rare; pacing is campaign-level).
- `BUDGET_DELIVERY_MODE_REPORT` — ACCELERATED vs STANDARD (mandatory first diagnostic).
- `BUDGET_PACING_BUCKETS_REPORT` — pacing time buckets for the marketplace + date.
- `CAMPAIGN_DAILY_BUDGET_AVG_REPORT` — the **configured** daily budget.
- `CAMPAIGN_DAILY_BUDGET_FLEXI_REPORT` — the **effective spendable** budget, capped by
  the merchant's wallet balance. Fetch both; see STEP 2b.
- `WALLET_BALANCE_REPORT` — merchant balance. Current snapshot only, no date column.
- `MINUTE_LEVEL_CPC_REPORT` — minute-level clicks + spend (CPC marketplaces).
- `MINUTE_LEVEL_CPM_REPORT` — minute-level impressions + spend (CPM marketplaces).
- `AUDIT_EVENTS_REPORT` (must pass `perf_action_type_id` = 17) — budget-change audit events on the date.

Do NOT call any tool not in this list (no merchant breakdowns, no RR/CTR tools).

## SOP

This is a **menu of steps the user walks through with you**, not a script to run.
Per `common-rules.md`: every branch below is a question, every step ends the turn,
and the scope the user set — program, category, campaign — is the only one you touch.

**A branch is several sub-steps, not one.** Each fetch that produces a choice is a
checkpoint: present what came back, then let the user narrow before drilling further.
Do not run a whole chain in one turn just because you already hold the inputs.

### STEP 1 — Ask only for missing inputs
- Which campaign(s) (any campaign ID type).
- The date of the pacing problem (`YYYY-MM-DD`).
- Whether the marketplace uses **CPC or CPM** bidding (decides the minute-level
  tool — this is NOT about PLA vs Display; it's always PLA).

### STEP 1.5 — Resolve campaign IDs
`CAMPAIGN_LOOKUP_REPORT`, filtering **`perf_marketing_campaign_id`** with the IDs the
user gave — that is the ID shown in the UI. Do **not** filter `perf_campaign_id`: on this
report that column holds the INTERNAL id, so the UI id returns zero rows with no error.
Extract the `perf_marketing_campaign_id`s (what downstream reports require). If an ID
fails to resolve, name it and ask for a correction before proceeding.

**Never call this report unfiltered.** It ignores `limit` and returns the marketplace's
entire campaign list (~186k rows / 27 MB), which will kill the MCP connection.

### STEP 1.75 — Budget delivery mode (MANDATORY FIRST DIAGNOSTIC)
`BUDGET_DELIVERY_MODE_REPORT` for ALL resolved campaigns.
- **ACCELERATED** → front-loaded/burst spend is EXPECTED, not a pacing defect.
  Conclude: "Campaign [ID] is on ACCELERATED delivery — designed to spend the
  daily budget as fast as possible. Early/burst spending is expected, not a pacing
  defect. To pace it across the day, switch to STANDARD delivery." **STOP here for
  ACCELERATED campaigns — do NOT proceed to Steps 2–4 for them.**
- **STANDARD** → proceed.
- **Mixed** → call out the ACCELERATED ones, proceed with only the STANDARD
  campaigns.

### STEP 1.9 — Confirm bidding strategy (MANDATORY, BLOCKING)
You MUST know CPC vs CPM before STEP 2 — it decides which minute-level tool you
call. No default, no auto-detection.
- User already said CPC/CPM → use it.
- Otherwise ASK EXACTLY: "Does this marketplace use CPC (cost-per-click) or CPM
  (cost-per-mille / impression) bidding? I need this to pull the right minute-level
  spend data." Then **STOP and wait** — do NOT call any STEP 2 tool.
- **NEVER guess. NEVER call both minute-level tools hoping one works. NEVER call
  either before the user confirms.**

### STEP 2 — Fetch data (parallel; STANDARD campaigns only; confirmed strategy)
a) `BUDGET_PACING_BUCKETS_REPORT` — pacing time buckets for the marketplace + date.
b) **Both** budget reports — they answer different questions:
   - `CAMPAIGN_DAILY_BUDGET_AVG_REPORT` — the **configured** daily budget. It is derived as
     an average over the range you pass, so query a **single date** for a single-date
     question; a week-long range returns the week's average.
   - `CAMPAIGN_DAILY_BUDGET_FLEXI_REPORT` — the **effective spendable** budget, capped by
     the merchant's wallet. When the day's spend exceeded the remaining balance it returns
     that spend, because that is all that was fundable.

   **If flexi ≈ actual spend while avg is much higher, the campaign was wallet-capped on
   that date, not pacing-capped** — that is the answer, not a report defect. Flexi is the
   only report that reveals a *historical* wallet cap, so treat the match as the finding.

   `WALLET_BALANCE_REPORT` **cannot confirm it**: the report has no date column and returns
   a current snapshot, so a healthy balance today says nothing about the date in question —
   the wallet may have been drained then and topped up since. Report the wallet cap on
   flexi's evidence, state that the as-of-date balance is not available from these reports,
   and do not treat a healthy current balance as contradicting it.

   Use **avg** for the STEP 3 pacing comparison and report the wallet cap separately.
c) ONE minute-level tool (never both): CPC → `MINUTE_LEVEL_CPC_REPORT` (clicks +
   spend by campaign, page_type, hour, minute); CPM → `MINUTE_LEVEL_CPM_REPORT`
   (impressions + spend by campaign_group, hour, minute).

### STEP 3 — Compare actual vs expected spend per bucket
For each bucket: `expected_spend = daily_budget × (bucket_pct ÷ 100)`. Sum actual
minute-level spend within each bucket's time window. For CPC data, split by
`page_type` into SEARCH and NON-SEARCH (everything not SEARCH). Identify buckets
where `actual_spend > expected_spend` (overspend).

### STEP 4 — Diagnose the overspend (apply rules IN ORDER)
1. **Budget update** — `AUDIT_EVENTS_REPORT` (must pass `perf_action_type_id` = 17). If a budget change occurred
   AND overspend happened within a **40-minute window AFTER** the change timestamp
   → "Budget update is the reason: daily budget changed from [old] to [new] at
   [time], overspend occurred in the 40 minutes following." If a change occurred
   but overspend is NOT within the 40 min → "Budget was changed but overspend is
   not correlated with the update timing. Raise internally to the backend team."
2. **Sudden click traffic** (CPC only, NON-SEARCH only) — overspend on NON-SEARCH
   pages concentrated in a **consecutive 10-minute window where every minute has
   spend (no gaps)** → "Sudden click-traffic burst on non-search pages caused the
   overspend. [N] clicks in [minute range] generated [spend] exceeding the bucket
   allocation."
3. **Search-page pacing limitation** — overspend on SEARCH pages → "Budget pacing
   is not applicable to SEARCH pages. The pacing algorithm only pauses campaigns on
   non-search pages. Overspend on search is expected — the campaign pauses serving
   only on non-search pages when the budget is reached."

If none match → present the raw actual-vs-expected comparison and flag for manual
investigation.

## Available drills by program — a menu, not a checklist

**This is not a coverage list.** Run only the program the user chose, and only the
drills they pick. Nothing here is owed to them by default. If a drill from the other
program would genuinely change the diagnosis, say so in one line and let the user
decide — do not run it to find out.
**PLA only.** Display ads do not use budget pacing — there is no Display path.
