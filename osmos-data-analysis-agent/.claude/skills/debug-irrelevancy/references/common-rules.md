# Common rules for marketplace performance-debugging skills

Shared behavior for all SOP debugging skills (ROAS, CPC, CTR, BU, RR, …),
extracted from the `_COMMON_*` blocks in `weekly_analysis_agent/prompts/
agent_instructions.py`. Load this once at the start of an investigation.

> ## ⚠️ Tool binding — read before your first data call
>
> The tool names in this file and in every skill (`check_gmv_attribution`,
> `get_merchant_breakdown`, `get_context`, …) are the **legacy ADK agent's Python
> functions**. **They do not exist here. There is no `get_*` or `check_*` tool.**
>
> - **Every data call is `run_report`** against a KAM report. Resolve each legacy
>   name to its report, columns and required filters via
>   **`knowledge/tool-map.md`** before calling. Do not guess a tool name, and do
>   not call one because the SOP prose names it.
> - **State tools have no replacement** (`get_context`, `get_date_ranges`,
>   `get_all_findings`, `get_discoveries`, `get_today`, `update_context`,
>   `update_analysis`, `get_keyword_categories`). There is no state store — the
>   conversation carries the context. See STEP 0.
> - **"In comparison mode" means two `run_report` calls.** These reports are
>   single-period and emit no `_prev` / `_change` / `_perc` variants; fetch
>   current and baseline separately and combine them yourself. Check each
>   response's `period` field rather than assuming call order.
>
> The *procedure* below is unchanged — only how you fetch the data.

---

## STEP 0 — One-time setup (first turn only)

**There are no context tools to call.** The intake protocol has already established
agency_id, marketplace_client_id, region, currency, timezone, the affected program
and the date ranges **in this conversation** — read them from there. Prior findings
and discovered entities are your own earlier turns. Nothing to fetch, nothing to
persist.

If any of it is genuinely missing, ask the user rather than inventing it.

**Dates** — use the dates resolved during intake, then reconcile with the user:
- No dates established → ask the user, then proceed.
- The user's message specifies dates that DIFFER from the ones in play → the
  user's intent wins; restate the new window and proceed.
- Match / unspecified → proceed with the established dates.
- **A month/day without a year always means the current calendar year.** Never
  pull 2024/2025 from training data. Only use a prior year if the user typed it,
  or if the current-year reading would be in the future.

**User-supplied entities** — campaign or merchant IDs the user gave you in the
conversation are scope. Pass them as `filters` on the relevant report.

**Program type** — confirm before analysis, and treat the answer as a **lock**.

- Established in the conversation ("pla" / "display") → state it and proceed.
- Missing or unclear → **ask and wait**. Never default, and never assume "both"
  because the user did not narrow it.
- Once set, the other program is **out of scope**. Do not run it, do not fetch it
  "to be thorough", do not speculate about what it would have shown. If you think
  it matters, say so in one line and let the user reopen it.
- "Both" is a valid answer, but only when the **user** chooses it. Then run them
  as two separate passes and present them separately — never blended into one
  table, since the underlying fact tables and column sets differ.

Pass the program to every report call as its filter.

Program-type column rules:
- **PLA:** `channel = 'os_product_ads'`
- **Display:** `channel IN ('guaranteed_display_ads', 'auction_display_ads')`

---

## Consultant behavior

1. If the user narrowed scope (category, merchant, SKU, page type), skip broad
   checks — go straight to the relevant tool.
2. Listen for specific entities (merchant names, client IDs, SKUs, categories)
   and call the matching tool immediately.
3. **Interactive checkpoint model (SOP skills only)** — after each major SOP
   step: present the checkpoint, then **STOP. Do not call another tool until the
   user has replied.** Ending your turn is the checkpoint. Never present a
   checkpoint and continue investigating in the same turn.

---

## The user drives. You do not.

This agent is used to work tickets, where the person asking already knows which
slice they care about. Running the "complete" investigation wastes their time and
buries the answer they wanted.

**a) Decision nodes are questions, not routing.** Wherever this SOP branches —
a scenario (A / B / C), a program, a dimension, a drill-down — **do not pick.**
Present the evidence, list the branches, say which you would choose and why, then
**ask and wait**. Use `AskUserQuestion` so the choice is explicit and selectable.

Correct:
> Requests rose 18% while responses stayed flat, so scenario A fits best.
> Where do you want to go?
> 1. **A — category request surge** (recommended: the jump is concentrated in 3 L1s)
> 2. **B — budget drop** — rule it out first; cheap to check
> 3. **C — supply-side response drop**

Wrong: *"Scenario A applies, so moving to STEP 3-A…"* then running it.

**b) Scope is locked once the user sets it.** If they said PLA, **Display is out
of scope** for the rest of the session — do not run it, do not fetch it "for
completeness", do not mention what it might have shown. Same for a named
category, page type, campaign or merchant. If you believe the other program is
relevant, say so in one line and let them decide.

**c) Never widen a request on your own.** A question about one page type is not
an invitation to break down every page type. Answer what was asked; offer the
wider cut as an option.

**d) One step per turn.** Even when the next step is obvious and you already hold
its inputs, stop and offer it. The user may know something the data does not —
which is the whole reason they are here.

**Exception:** parallel calls *inside* one SOP step (the triage fan-out) are one
step, not several. Fetch them together, present once.

**Mid-conversation date change** — if the user asks for different dates later,
restate the new window and restart from STEP 1.

**Entities you have already fetched** — when a report returns entities with clear
relationships (categories targeted by a campaign, merchants in a breakdown, SKUs
under a merchant), they are in this conversation. Re-read your earlier turns
rather than re-fetching. There is no discovery store to write to.

### Checkpoint format (every checkpoint has all four parts)
- **a) Where we stand** — 1–2 sentences on what's confirmed so far.
- **b) Findings** — a markdown table of the actual rows + real metric values the
  step produced. Show the concrete numbers, not a prose characterisation. Back
  every qualitative claim ("CPC is in line", "others are bidding too") with the
  table rows it came from. If a step returned no rows, say so.
- **c) What this means** — 2–3 interpretation bullets pointing at the likely
  cause / next signal.
- **d) Options** — numbered investigation paths, each runnable **right now**
  (its tool is loaded at this stage AND you already hold every input it needs),
  each with a one-line rationale. Mark the one you'd recommend and say why.
  If you lack an input, the correct option is the step that PRODUCES it, not the
  downstream drill. Never offer an option you can't execute.

  Options are a **question**, not a preview of what you are about to do. Present
  them with `AskUserQuestion` and end the turn. Always include a way out —
  "something else / stop here" — because the user may want a cut the SOP does not
  list.

```
CHECKPOINT [N] — [Step Name]

Where we stand: [confirmed facts]

[Findings — markdown table of actual rows + numbers]

What this means:
• [pointer 1]
• [pointer 2]

How would you like to proceed?
1. [Option A] — [why, given the findings]
2. [Option B] — [why]
3. [Wrap up / other direction]
```

After emitting a checkpoint, STOP and wait for the user's choice — do not call
any tool until they respond. **Honour the choice:** call the exact tool the
chosen option named; never silently substitute a different step. If the chosen
option turns out not to be runnable, say so and explain what's needed.
**Rewind:** if the user says "go back" / "try option 2", re-present the previous
checkpoint from data already fetched (no need to re-run tools), then proceed.
Do NOT checkpoint for the STEP 0 parallel setup calls.

4. Remember the user's filters all session; never re-ask for provided info.
5. Use tools in whatever order fits the question.
6. For broad requests ("BU dropped"), follow the skill's default flow.

---

## Pre-summary checkpoint

Before summarizing, present what's been found and ask:
"I've completed the analysis. Would you like me to summarize the findings, or
investigate further?" Offer concrete next-step options drawn from tools you have
NOT yet run (or could re-run at a finer grain) — deeper merchant/SKU/category/
campaign/page/keyword drills, campaign-status or product-selection checks, custom
SQL — each with a one-line rationale. Always include a "Write final summary" and
an "Other direction" option. Only after the user confirms → call
`store_agent_findings()`, then write the Final Report. Never auto-summarize.

---

## Storing findings (MANDATORY before the summary)

You MUST call `store_agent_findings()` **before** writing any final summary text —
other skills/agents read this state to cross-reference. Call it with:
- `metric_type` (e.g. "roas", "cpc", …)
- `root_cause` (e.g. "Marketplace Level Decline" / "Merchant Level — top 3
  merchants lost orders")
- `affected_programs`: "pla" / "display" / "both"
- `severity`: high (>15% of the metric), medium (5–15%), low (<5%)
- `key_findings`: list with actual numbers
- `impacted_entities`: list of `{ "name", "impact", ... }` (e.g. `client_id` +
  `"type": "merchant"`)
- `recommendations`: actionable list

Only after it completes → write the Final Report.

**Cross-agent:** if an earlier investigation in this conversation already covered
part of this ground, note the overlap and do not repeat completed analysis.

---

## Output & tool rules

- **Dates** passed to tools MUST be exactly `YYYY-MM-DD`, no trailing characters
  (`2026-03-31`, never `2026-03-31,`). Double-check before every call.
- **Period matching:** when you call a tool for current vs baseline, check the
  `period` field in each response — never assume call order equals period order.
- **Currency:** always prefix monetary values with the marketplace currency from
  context ("INR 1,234", "USD 5,678"). Never show a raw number.
- **Scope transparency:** if you can't answer with available tools, say so —
  state what you CAN provide and which tools exist. Never silently skip or invent
  data. (e.g. "I don't have keyword-level CPC; I can show merchant-level
  (`get_merchant_cpc_breakdown`) or page-level (`get_page_level_performance`).")
- **Hand back** with `HANDOFF_TO_ROOT: [reason]` when: the user asks about a
  different marketplace; needs a different metric; analysis is complete and they
  want other areas; context is missing (no agency_id / dates); or the request
  can't be met with your tools. Never ask the user for agency_id — hand back.

---

## Final report format

Generic skeleton — **each skill defines its own metric-specific entity table
columns** (e.g. the ROAS skill's 16-column merchant table). Use this for the
overall structure; take the columns from the skill.

```
[metric] Analysis Summary | Severity: HIGH/MEDIUM/LOW | Period: [dates]
Root Cause: [description] | Programs: PLA/Display/Both
Key Findings: [numbered, actual numbers]
Tables (ACTUAL values, never "N/A"):
- Merchants: highest spenders FIRST (lead with the Pareto vital-few list).
  name | Client ID | Status | Baseline Spend | Current Spend | Baseline GMV |
  Current GMV | Baseline ROI | Current ROI | GMV Δ% | Baseline Share% |
  Current Share% | Contribution to GMV Δ% | Cumulative Spend Share% |
  Attributed CVR vs Site CVR | Site GMV Δ%  (RAW baseline & current, not only Δ%)
Recommendations: [actions]
Cross-References: [other agents' findings]
```

---

## COMPETITION CHECK (PLA only)

> **When to run this is defined by each skill, not here.** Some skills gate it
> behind an explicit user request (e.g. ROAS, CTR run it only when the user asks);
> others auto-invoke it from their own branches (e.g. the campaign diagnostic runs
> it from branches 3a/3c/3f, gated by its STEP 2.5). Follow the calling skill's
> gate — this section only defines the mechanics once the check is triggered.

A rival entered or raised bids on a surface our campaign competes on. Run it only
when the metric move points OUTWARD — after internal causes are ruled out
(campaign not paused, products present, wallet/budget OK, no catalog/
product-selection change).

**First, the symptom depends on OUR campaign's targeting type** — confirm with
`get_campaign_targeted_keywords` (count > 0 = MANUAL bids set, and each keyword's
`bidding_value` is our bid; count = 0 = AUTO / Smart-auto; Smart Shopping can have
both — never infer from subtype, and never claim "no manual keywords" without the
fetch; any EXACT/PHRASE/BROAD row proves manual targeting):
- **AUTO / Smart-auto** (no bid set): system raises our effective bid → symptom is
  RISING CPC/CPM (spend up; clicks flat/down).
- **MANUAL** (fixed bid): we don't auto-raise → symptom is FALLING
  impressions/SOV/position (and downstream CTR); CPC stays roughly flat; the fix
  is "raise the bid".

Rising CPC = the AUTO fingerprint; falling impressions/position = the MANUAL
fingerprint. Competition is a root cause that propagates (higher bids → worse
position → fewer impressions/clicks → lower CTR → lower fill → shifted spend →
higher cost-per-conversion). Trace it to whichever metric you own.

**Then check the surfaces the campaign competes on (finest → coarsest), always in
COMPARISON mode** so a rival entering/raising in post surfaces as `new_in_post` /
`new_competitors` / `new_entrants_in_period`:

1. **Keyword / search query** — a rival targeted a query we won cheaply, at a
   higher bid.
   - a. `get_search_query_performance(sort_by="spend", + baseline)` scoped to the
     campaign or the problem keyword(s) → the spend-driving queries pre/post;
     flag those that lost spend/impressions or whose CPC rose.
   - b. `get_targeted_keyword_competition(search_queries=[those],
     exclude_marketing_campaign_ids=[ours], + baseline)` → rivals targeting them
     and their bids pre/post; a `new_in_post` rival, or one whose cpc/cpm rose, on
     a contested query = the bid pressure.
   - c. `get_search_query_performance(search_queries=[those],
     breakdown_by="campaign", + baseline)` marketplace-wide → served-on
     competition + `keyword_match_type` (AUTO vs EXACT/PHRASE/BROAD) +
     `new_competitors`.
2. **Category** — resolve to FULL L1 > L2 > L3 (`category_level="l3"`); never stop
   at L1. TWO HOPS:
   (a) `get_campaigns_in_category(marketing_campaign_ids=[ours],
   category_level="l3", + baseline)` to read OUR campaign's category_l1/l2/l3 and
   pick the L3 categories where our spend fell;
   (b) re-call with those `category_l1/l2/l3_filter` values and NO campaign filter
   → the RIVAL campaigns in the same category pre vs post, with per-rival cpc/cpm,
   `new_entrants_in_period`, and `subtype_summary`.
   **The conclusion is a BID comparison, not a spend comparison.** Banned
   non-conclusions: "we're not among the top spenders", "the category is
   saturated", "our spend is negligible". Build a PRE vs POST table: row 1 = OUR
   campaign (from hop a, always present even at tiny spend); following rows = top
   rivals / new_entrants (from hop b). State the verdict in bid numbers on OUR bid
   model. Only rivals bidding ABOVE us in post prove we're outbid; if rivals are
   at/below our cpc/cpm, we are NOT outbid — say so and look at RR/eligibility.
3. **Merchant / seller** — a new seller entered the queries broadly
   (`get_keyword_seller_breakdown` new sellers; merchant breakdowns
   `new_merchants`).

Compare rivals on OUR campaign's bid model (read `bidding_strategy` from
`lookup_campaign`): CPC for CPC/AUTO_CPC, CPM for CPM/AUTO_CPM. Conclude only after
naming the contested query/category, the specific rival, and — for a new entrant —
the timing vs when our metric moved. Always present every competition data point
WITH its contribution (share per period + contribution to the spend/clicks
change), never raw numbers alone.
