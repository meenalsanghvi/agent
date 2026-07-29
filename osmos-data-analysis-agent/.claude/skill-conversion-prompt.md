# Prompt — Convert an ADK agent instruction into a Claude Code skill

Use this to port one `*_AGENT_INSTRUCTION` from
`weekly_analysis_agent/prompts/agent_instructions.py` into a Claude Code skill.
Run it once per SOP. `debug-roas` is the reference implementation — match its
fidelity bar.

---

## Role & goal

You are porting an OnlineSales marketplace-debugging **SOP** (currently an ADK
agent system prompt) into a **Claude Code skill**. The output is a task playbook
Claude loads on demand — the SOP's *procedure and interpretation logic* must
survive intact. Completeness is the hard requirement: **cover everything in the
source; anything you drop must be provably a non-loss** (see the whitelist).

## Context you must keep in mind

- **Target runtime is Claude Code** (and the Claude Agent SDK). Skills live at
  project scope now (`.claude/skills/`), and will later be bundled into a plugin
  for org-wide distribution — so each skill must be **self-contained and
  portable** (no references outside its own folder).
- **Tool bindings are being migrated** to MCP/KAM. Tool *names* in the source
  (`check_gmv_attribution`, `get_merchant_breakdown`, …) are the current Python
  tools; they will resolve to the registered MCP tools of the same logical role.
  Keep the tool names as-is and keep a tool-binding note — the *procedure* is
  durable, only the bindings change.
- **Tool schemas come from MCP registration, not the skill.** Do NOT reproduce
  input schemas / parameter lists. DO preserve every piece of *interpretation
  nuance* attached to a tool in the source (e.g. "comparison mode in ONE call,
  not two", "ONLY when affected_program = display", "resolve group_id →
  campaign_id via lookup_campaign first"). That nuance is SOP knowledge and is
  lost if you drop the tool.
- **Progressive disclosure**: the `description` frontmatter is always in context;
  the body loads on trigger; `references/` loads only when pointed to. Put the
  metric-specific playbook in `SKILL.md`; lean on the shared `common-rules.md`
  for behavior common to all SOPs.

## Inputs to read

1. The target constant, e.g. `ROAS_AGENT_INSTRUCTION`, in
   `weekly_analysis_agent/prompts/agent_instructions.py`.
2. **Every interpolated block it references** — expand them fully before
   auditing coverage: `_COMMON_FIRST_STEP`, `_COMMON_CONSULTANT_BEHAVIOR`,
   `_COMMON_PRE_SUMMARY_CHECKPOINT`, `_COMMON_PROGRAM_TYPES`,
   `_COMMON_CROSS_AGENT`, `_COMMON_RULES_TEMPLATE`, `_COMMON_COMPETITION_CHECK`,
   and `_build_store_findings_block(...)`. (Which blocks appear varies per agent —
   read the actual f-string.)
3. The existing `debug-roas/SKILL.md` and `references/common-rules.md` as the
   template.

## Output

```
.claude/skills/<skill-name>/
├── SKILL.md
└── references/
    └── common-rules.md      # copy verbatim from debug-roas (see "Shared rules")
```

- `<skill-name>`: kebab-case, action-framed — `debug-cpc`, `debug-ctr`,
  `debug-bu`, `debug-rr`, `debug-campaign`, `debug-budget-pacing`,
  `debug-keyword-delivery`, `debug-keyword-low-rr`, `debug-irrelevancy`. (The
  `data_agent` is NOT a skill — it's a direct-query agent with no SOP.)
- Project scope, in the `osmos-data-analysis-agent` repo.

## SKILL.md structure

**Frontmatter** — only `name` and `description` matter:
- `description` is the single most important line — it drives auto-selection.
  Write it as *what it does + WHEN to trigger*, using the words a user would say
  ("why did CPC rise", "budget utilisation dropped"), PLUS explicit **negative
  boundaries** so Claude doesn't pick the wrong skill ("not for … use debug-X").

**Body sections (adapt to the SOP):**
1. One-line intro + "read `references/common-rules.md` first".
2. **Core principle / key concepts** — the metric definition and the SOP's
   framing (e.g. contribution-first, SITE vs PROGRAM, the metric's decomposition,
   scenario triage).
3. **SOP — numbered steps**, faithful to the source: each step's tool, what to
   read from it, and the branching/interpretation logic (verdicts, thresholds,
   stop conditions, hand-off rules). Preserve "skip the SOP if the user asks
   something specific".
4. **Additional drill tools (beyond the linear SOP)** — every tool listed in the
   source's `Tools:` block that is *not* a numbered step, each with its
   interpretation nuance. Do not omit these.
5. **Program-type completeness** — explicitly state the PLA path and the Display
   path (which tools/columns apply to each). Never leave a skill silently
   PLA-only if the source supports Display.
6. **Final Report** — the metric-specific table columns **verbatim** from the
   source (do not generalize them away), plus the `store_agent_findings`
   contract (metric_type, severity thresholds, impacted-entity keying) from
   `_build_store_findings_block`.

## Shared rules (`common-rules.md`)

`common-rules.md` already exists (created with `debug-roas`) and covers: STEP 0
setup, date rules, program-type gate, consultant/checkpoint model, discovery
store, pre-summary checkpoint, store-findings contract, output/tool rules, final
report skeleton, and the PLA competition check.

- The canonical file is `.claude/skill-common-rules.md`. Do NOT hand-copy it — run
  `scripts/sync-skill-common.sh` to copy it into every skill's
  `references/common-rules.md` (self-contained copies = portable into a plugin).
- Only **extend** it by editing the canonical file, then re-run
  `scripts/sync-skill-common.sh` (and `--check` to verify no drift). Never edit a
  skill's copy directly, and never put shared behavior in the skill body.
- Anything **metric-specific** goes in `SKILL.md`, never in `common-rules.md`.

## Coverage requirement (definition of done)

After writing, produce a **coverage audit table** mapping every element of the
source (the instruction + each expanded `_COMMON_*`/`_build_*` block) to where it
landed: `SKILL.md`, `common-rules.md`, or **Dropped (justified)**.

Nothing may be silently missing. For each dropped item, state why it is a
non-loss.

### Intentional-omission whitelist (the only justifiable drops)

- The persona/identity line ("You are the X Debugging Agent …") — belongs to the
  agent/subagent layer in Claude Code, not the skill.
- Tool **input schemas / parameter signatures** — supplied by MCP registration.
  (Interpretation nuance is NOT covered by this — keep it.)
- Pure ADK-runtime plumbing with an exact Claude Code equivalent already stated
  in `common-rules.md` (e.g. session-state tool mechanics) — reference the
  common rule instead of repeating it.

**Anything else dropped is a defect.** In particular do NOT drop: any numbered
SOP step, any verdict/threshold/branch, any tool's interpretation nuance, the
Display path, the metric-specific report columns, hand-off rules, or the
competition check.

## Quality bar

Match `debug-roas`: faithful SOP flow with intact decision logic, the full drill-
tool inventory with nuance, explicit PLA + Display paths, the exact metric report
table, a strong trigger `description` with negative boundaries, and shared
behavior delegated to `common-rules.md`. Finish with the coverage audit and an
explicit list of what (if anything) was intentionally omitted and why.
