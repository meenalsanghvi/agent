# Skills vs sub-agents — migration plan (ADK → Claude SDK)

Derived from a full read of `weekly_analysis_agent` (Google ADK). Decides, per piece,
whether it becomes a **skill** (main-context playbook, auto-triggered, shares the live
conversation) or a **sub-agent** (isolated context, delegated via the Task tool,
returns a result).

## 1. What the ADK agent actually is

```
root_agent (weekly_analysis_agent)         ← intake + context + routing
  tools: state_tools + get_problem_metrics
  sub_agents (11):
    data_agent            ← ad-hoc data, ~45 tools, NO SOP
    roas / cpc / ctr / bu / rr             ┐
    keyword_delivery / keyword_low_rr      │ 10 SOP specialists:
    irrelevancy / campaign_diagnostic      │ SOP instruction + staged toolset
    budget_pacing                          ┘
```

Three ADK mechanisms hold it together:
- **Session state** (`update_context`, `state["agency_id"|"timezone"|"affected_program"|
  "user_note"|"current_start_date"|"agent_findings"…]`) — because **ADK sub-agents
  cannot see the conversation history**, the root must copy every fact (and even
  user-supplied entities via `user_note`) into shared state before routing.
- **Staged toolset** (`AnalysisToolset`: `always → after_attribution → after_merchant`)
  — progressive tool disclosure to keep token cost down; a stage unlocks once a tool
  from the previous stage was called.
- **Routing** — the root LLM picks a sub-agent by its `description`; sub-agents bounce
  back with `HANDOFF_TO_ROOT: …`.

## 2. The mapping principle (why most sub-agents → skills)

**ADK sub-agents here exist for instruction isolation, tool scoping, and routing —
all three of which Claude Code solves *without* sub-agents:**

| ADK construct | Why it existed in ADK | Claude SDK equivalent |
|---|---|---|
| Sub-agent per metric | isolate the SOP instruction + tools; enable routing | **Skill** (auto-triggered by `description`, runs in main context) |
| Session state + `user_note` relay | sub-agents can't see the conversation | **Not needed** — a skill sees the whole live conversation |
| `AnalysisToolset` staging | cut tokens via progressive tool disclosure | **Not needed** — skills *are* progressive disclosure; MCP tool decls are cheap |
| Root-agent router | pick the specialist | **Automatic skill triggering** — no router artifact |
| `HANDOFF_TO_ROOT` | bounce control back | skills hand off to each other/main loop in-context |

**Conclusion:** a Claude sub-agent should be used for the *opposite* reason ADK used
them — only when you genuinely WANT isolation/parallelism, never because you're forced
into it. So the 10 interactive SOPs are **skills** (already built), and sub-agents are
reserved for a few bounded, parallel, or isolatable sub-tasks.

## 3. Component-by-component plan

| ADK piece | Claude SDK | Notes |
|---|---|---|
| **10 SOP agents** (roas, cpc, ctr, bu, rr, keyword_delivery, keyword_low_rr, irrelevancy, campaign_diagnostic, budget_pacing) | **10 skills** ✅ already built (`debug-*`) | Interactive, shared-context, self-routing. Correct as-is. |
| **root intake/context** (fuzzy-match marketplace → agency/region/currency/timezone; confirm PLA/Display; resolve current+baseline dates; fetch flagged problem metrics) | **CLAUDE.md "intake protocol"** + a few always-available MCP tools (`fetch_marketplace_info`, `get_problem_metrics`, `compute_week_range`) + optional thin **`start-analysis` skill** | Runs at the top of essentially every session → belongs in CLAUDE.md, not a triggered-only skill. Program-type + date rules are prose the main agent follows. |
| **routing** | **automatic skill triggering** | Skill `description`s already written as triggers. No artifact. |
| **session state** | **the live conversation** (+ optional `scratchpad/context.md` for very long sessions) | Drop `update_context`/`user_note`/state plumbing — the main agent just remembers in-context. |
| **staged toolset** | **drop** | Skills load on demand; the skill body tells the agent which tool to call at each step. |
| **data_agent** (ad-hoc data, no SOP) | **main-agent baseline** over the MCP catalogue tools (`run_report`/`get_*_reports`) | "Show me / compare / top-N" needs no skill or sub-agent — it's default behavior. Optional tiny `data-lookup` skill only for output conventions. |

## 4. Where sub-agents ARE warranted (build these)

Only bounded / parallel / isolatable work — never the interactive SOP itself.

| Sub-agent | Used by | Why a sub-agent (not a skill) | I/O contract |
|---|---|---|---|
| **`sku-drilldown`** | debug-roas (step 5), debug-cpc (step 4), debug-ctr (step 5) | The SOPs say "SKU drill-down for **top 5 problem merchants**". Fan out one isolated worker **per merchant**, in parallel; each pulls SKU rows + ranks offenders. Keeps the (large, noisy) SKU pulls out of the main context and is faster. | in: `{client_ids[], program, dates}` · out: ranked SKU offenders per merchant (compact) |
| **`contribution-scan`** (optional) | debug-roas / cpc / ctr / bu / rr (the "contribution-first / Pareto high-impact merchants" step) | When the merchant/category list is large, fan out contribution math and return only the Pareto set. Inline is fine for small lists — promote to a sub-agent only when the list is big. | in: `{entities[], metric, current, baseline}` · out: Pareto-ranked contributors |
| **`report-validator`** (authoring-side) | the KAM-config authoring workflow (not the runtime agent) | Mirrors kamService's `kam-tester` subagent: post config to test, run with known params, eyeball rows, COMPARE vs baseline. Bounded, non-interactive, returns a verdict. | in: `{config, agency, dates, baseline?}` · out: `{pass|fail, rows, diffs}` |

## 5. Do NOT port (ADK-limitation artifacts)
- The **root agent** as a separate entity (routing is automatic).
- **Session-state tools** and the **`user_note` relay** (no isolated context to feed).
- The **`AnalysisToolset` staging** machinery.
- `HANDOFF_TO_ROOT` protocol.

## 6. Net architecture

```
Claude Code (main loop)
  ├─ CLAUDE.md intake protocol  ── fetch_marketplace_info · get_problem_metrics · dates · program-type
  ├─ auto-triggers ONE debug-* skill  (the 10 SOPs — interactive, in-context)
  │     └─ may delegate → sku-drilldown  (parallel, top-N merchants)   ← sub-agent
  │     └─ may delegate → contribution-scan (large lists)              ← sub-agent (optional)
  ├─ ad-hoc "show me X"  → main agent + MCP catalogue tools (was data_agent)
  └─ data layer: osmos-reporting-mcp (INTERNAL_PERFORMANCE mount) + KAM
authoring-side (separate): report-validator sub-agent
```

## 7. Build / keep / drop
- **Keep:** the 10 `debug-*` skills (they are the correct shape).
- **Build:** CLAUDE.md intake protocol (+ optional `start-analysis` skill); `sku-drilldown`
  sub-agent; `report-validator` sub-agent (authoring). `contribution-scan` only if needed.
- **Drop / don't build:** root-agent router, session-state plumbing, `user_note` relay,
  staged-toolset machinery, a bespoke `data_agent` (it's baseline behavior).

## 8. Open decisions
- **Intake as CLAUDE.md vs skill** — recommend CLAUDE.md (runs every session); a skill is
  only better if you want it explicitly invocable.
- **`contribution-scan`** — build now or inline until lists prove large? (Recommend inline
  first; promote when a real marketplace has hundreds of merchants.)
- **`report-validator`** — only relevant if config authoring stays in this repo vs moving
  to the sanctioned kamService kam-writer/kam-tester stack.
