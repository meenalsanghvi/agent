# CLAUDE.md — Osmos marketplace data-analysis agent

Claude Code agent that debugs marketplace ad-performance issues (ROAS, CPC, CTR,
Budget Utilisation, Response Rate, keyword delivery, campaigns, budget pacing) for
OnlineSales marketplaces. Data flows through **KAM** reports via an MCP server; the
reasoning lives in the `debug-*` **skills**.

**Start with `/analyze`** — e.g. `/analyze takealot — why did RR drop last week`. Not
required: asking in plain language routes straight to the matching `debug-*` skill.
Whichever SOP runs is announced in the transcript (`🧭 Skill · debug-rr — Response rate`),
including work inside the `sku-drilldown` sub-agent — see `.claude/hooks/`.

> **Tool binding.** The SOPs still name the legacy ADK functions
> (`check_gmv_attribution`, `get_context`, …). **Those tools do not exist.** Every data
> call is `run_report`; resolve each legacy name via **`knowledge/tool-map.md`**. There is
> no state store — the conversation carries the context. Full rules in each skill's
> `references/common-rules.md`.

## How this agent works

The agent's behaviour — intake protocol, context model, skill routing map, sub-agent
delegation, and the global rules — lives in
**`.claude/skills/analyze/references/intake-protocol.md`**. That file is the single source
of truth; read it before starting an investigation.

It lives there rather than here because a plugin's `CLAUDE.md` is **not** loaded as project
context. When someone invokes this agent as `/osmos-data-analysis:analyze` from another
repo, only skills, agents, and hooks come along. **Add new agent-wide rules to that
reference file, not to this one** — a rule added here applies only to people working inside
this repo. See `ORG_INSTALL.md`.

Structure:

```
you (main loop)
  ├─ /analyze  → intake (marketplace + program + dates + flagged issues)
  ├─ ONE debug-* skill auto-triggers  → the interactive SOP for that metric
  │     └─ may delegate → sku-drilldown sub-agent  (top-N problem merchants, PLA)
  ├─ ad-hoc "show me / compare / top-N"  → answer directly with the MCP data tools
  └─ data layer: MCP → KAM → BigQuery
```

- **Skills** (`.claude/skills/debug-*`) are the 10 metric SOPs; they auto-trigger by
  describe-match. **Do not re-implement a router.** Each reads `references/common-rules.md`
  first.
- **Sub-agent** (`.claude/agents/sku-drilldown.md`) is delegated *by a skill* for the
  parallel top-N-merchant SKU step. It is the only runtime sub-agent.
- The migration design (why skills, not sub-agents, for the SOPs) is in
  `.claude/skills-vs-subagents-plan.md`.
- Distribution and org rollout: `ORG_INSTALL.md`.

---
## Current wiring status (for whoever runs this)

**43 report configs posted to the KAM test env**, consolidated from 70 and verified —
see `kam_report_configs/AUTHORING_STATUS.md`. The reports are real; what is still landing
is the transport.

| Piece | State |
|---|---|
| `/osmosReportingMcp/internalPerformance` mount | deploying — until it is up, data calls fail |
| `INTERNAL_PERFORMANCE` in kamService's `VALID_VISIBILITY_VALUES` | in progress; configs are posted under `INTERNAL_USER` meanwhile |
| Hades scope on that mount | needed per caller |
| `osmos-performance-mcp/local_dev_server.py` | the older local shim (~11 tools) — see `LOCAL_DEMO.md` |

`.mcp.json` declares both servers; `.claude/settings.local.json` selects which is enabled.

**Blocked reports** (infra, not config): the audit-event family and the raw request-log
family — unregistered appKey and missing BQ grants. `knowledge/reports.md` lists them.

## Generated docs — do not hand-edit
`knowledge/reports.md` and `knowledge/tool-map.md` are produced by
`scripts/build_plugin_knowledge.py`, which writes to **both** this repo and the plugin.
Run it after any config change; `--check` fails on drift.
