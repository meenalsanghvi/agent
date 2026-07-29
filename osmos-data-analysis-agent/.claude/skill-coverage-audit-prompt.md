# Prompt — Coverage audit of a Claude Code skill vs its source ADK instruction

Use this to verify that one `debug-*` skill faithfully preserved **every** step,
verdict, threshold, branch, tool nuance, program path, report column, and rule
from the `*_AGENT_INSTRUCTION` it was ported from. This is the inverse check of
`skill-conversion-prompt.md`: that prompt *creates* the skill; this one *audits*
it. `debug-roas` is the reference (already audited and patched).

## The rule you are enforcing

The conversion contract says the source instruction is redistributed into exactly
three destinations — nothing may be silently missing:

1. **`SKILL.md`** — everything metric-specific: numbered SOP steps, verdicts /
   thresholds / branches / stop-conditions, EACH tool's interpretation nuance
   (including named return fields like `new_merchants_above_avg_cpc`), the PLA
   **and** Display paths, the exact metric report-table columns, hand-off rules.
2. **`references/common-rules.md`** — the shared `_COMMON_*` / `_build_*` behavior.
3. **Dropped — ONLY these are justifiable (the whitelist):**
   - the persona/identity line ("You are the X Debugging Agent …");
   - tool **input schemas / parameter signatures** (come from MCP registration);
   - pure ADK-runtime plumbing that has an exact equivalent already stated in
     `common-rules.md`.

**Anything else missing is a DEFECT.** In particular a dropped SOP step, verdict,
threshold, branch, tool-interpretation nuance, the Display path, a report column,
a hand-off rule, or the competition check is a defect — not a justified drop.

## Inputs to read (all of them, fully)

1. The source constant `<INSTRUCTION_NAME>` (lines `<RANGE>`) in
   `weekly_analysis_agent/prompts/agent_instructions.py`.
2. **Every block it interpolates** — expand each fully before auditing. This
   skill uses: `<BLOCKS>`. Their definitions live at the top of the same file
   (`_COMMON_FIRST_STEP` 138, `_COMMON_CONSULTANT_BEHAVIOR` 158,
   `_COMMON_PRE_SUMMARY_CHECKPOINT` 215, `_COMMON_PROGRAM_TYPES` 221,
   `_COMMON_CROSS_AGENT` 225, `_COMMON_RULES_TEMPLATE` 228,
   `_COMMON_COMPETITION_CHECK` 247, `_build_store_findings_block` 269).
3. The skill: `.claude/skills/<SKILL>/SKILL.md` and
   `.claude/skills/<SKILL>/references/common-rules.md`.

## Method

Enumerate the source as discrete, checkable elements in this order:
persona · each interpolated block (sub-point by sub-point) · Key-Concepts/framing ·
**every tool in the `Tools:` block WITH its nuance** · every numbered SOP step and
its branches/verdicts/thresholds · competition check (if present) · store-findings
contract args · the Final Report table columns · output/hand-off rules.

For each element decide: **SKILL.md** / **common-rules.md** / **Dropped
(justified)** / **DEFECT (missing or degraded)**. A nuance that is present but
watered-down (e.g. a named return field or a "ONE call not two" instruction that
got generalized away) is a DEFECT, tagged `degraded`.

Watch specifically for: named return fields dropped from a tool description;
a verdict/branch or its stop-condition missing; Display path missing or a skill
left silently PLA-only when the source supports Display; report-table columns
dropped or renamed; the "skip SOP if user asks something specific" escape hatch;
hand-off (`HANDOFF_TO_ROOT`) conditions; thresholds (severity %, request minimums).
Also note (as an observation, not a defect) any source **inconsistency the skill
correctly fixed** (e.g. mismatched step numbers).

## Output

Write the full audit table to `.claude/skill-audits/<SKILL>.md` with columns:
`# | Source element | Destination | Status (✅ full / ✅ dropped-justified / ⚠️ degraded / ❌ missing)`.
Head it with a one-line verdict and the defect count.

Then **return** (as your final message, not just in the file): the one-line
verdict, the total element count, and a bullet list of every ⚠️/❌ defect —
each as `SKILL.md §<section> — <source element> — <what's missing/degraded>`.
If there are zero defects, say so explicitly. Do NOT modify the skill or any
source file — this is read-only analysis.
