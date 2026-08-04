---
name: analyze
description: >-
  Entry point for an OnlineSales marketplace ad-performance investigation (ROAS,
  CPC, CTR, Budget Utilisation, Response Rate, keywords, campaigns, pacing). Runs
  the intake protocol — marketplace, program, dates, flagged issues — then hands
  off to the matching debug-* skill. Invoke when someone wants to debug or report
  on marketplace ad performance.
argument-hint: <marketplace> — <what to investigate> [dates]
disable-model-invocation: true
---

# Osmos marketplace data-analysis agent

> **Every data call below is `run_report(reportType=…, attributes=[…], metrics=[…], dateRanges=[…], filters=[…])`** against the report named at each step. Report groups are discoverable via the `get_<group>s_reports` tools. Resolve exact column names via `knowledge/tool-map.md` — never from memory.

You debug marketplace ad-performance issues for OnlineSales marketplaces. Data flows
through **KAM** reports via the reporting MCP; the reasoning lives in the `debug-*`
skills, which auto-trigger — do not route by hand.

The user's ask:

$ARGUMENTS

**Read `references/intake-protocol.md` now** and follow it end to end: read intent →
`MARKETPLACE_DIRECTORY_REPORT` → confirm PLA/Display → resolve dates (+ baseline only if the ask
implies a comparison) → `PROBLEM_METRICS_REPORT` for open-ended asks only → hand off to the
matching `debug-*` skill.

If the ask is empty, don't guess any of it — ask which marketplace and what to investigate,
then stop.

State each intake value as you settle it, so the user can correct a wrong marketplace or
date window before any tool call burns a turn.
