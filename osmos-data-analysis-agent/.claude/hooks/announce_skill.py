#!/usr/bin/env python3
"""PreToolUse hook: show which SKILL is running, and nothing else.

Claude Code already renders tool calls inline, but two things stay invisible or
collapsed: which `debug-*` SOP a request routed to, and work happening inside the
`sku-drilldown` sub-agent. Emitting `systemMessage` surfaces those regardless of
nesting depth.

Deliberately narrow: this announces **skills and sub-agents only**. Individual data
calls (`run_report`, MCP tools, Bash, file reads) are NOT announced — the trace should
read "which SOP is the agent following", not a log of every fetch. Claude Code already
shows the tool calls themselves for anyone who wants that detail.

Wire-up is in hooks/hooks.json, matched on the Skill and Task tools only, so the hook
never runs for anything else.
"""

import json
import sys

# Friendly names for the SOPs. Keys are skill directory names.
SKILLS = {
    "analyze":                "Marketplace investigation — intake",
    "debug-roas":             "ROAS / ROI",
    "debug-cpc":              "CPC",
    "debug-ctr":              "CTR",
    "debug-bu":               "Budget utilisation",
    "debug-rr":               "Response rate",
    "debug-campaign":         "Single-campaign deep-dive",
    "debug-budget-pacing":    "Budget pacing / overspend",
    "debug-keyword-delivery": "Keyword delivery in a campaign",
    "debug-keyword-low-rr":   "Low keyword response rate",
    "debug-irrelevancy":      "Irrelevant products served",
}

AGENTS = {
    "sku-drilldown": "SKU drill-down across the top problem merchants",
}


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # never get in the way of a tool call

    tool = payload.get("tool_name", "")
    args = payload.get("tool_input")
    if not isinstance(args, dict):
        args = {}

    if tool == "Skill":
        name = args.get("skill") or args.get("name") or "skill"
        # Plugin-scoped skills arrive as "plugin:skill" — show the bare name.
        bare = name.split(":")[-1]
        label = SKILLS.get(bare)
        message = f"🧭 Skill · {bare}" + (f" — {label}" if label else "")

    elif tool == "Task":
        name = args.get("subagent_type") or "sub-agent"
        label = AGENTS.get(name)
        message = f"🧭 Sub-agent · {name}" + (f" — {label}" if label else "")

    else:
        return 0  # not a skill or sub-agent — say nothing

    json.dump({"systemMessage": message, "suppressOutput": True}, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
