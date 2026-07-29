# Using the agent from any repo (org rollout)

The agent is packaged as a **Claude Code plugin**, so anyone in the org can invoke it from
whatever repo they happen to be working in — no `cd` into this repo, no copying `.claude/`
around.

```
/osmos-data-analysis:analyze Flipkart — ROAS dropped for PLA, 2026-07-19..2026-07-21 vs prior week
```

Everything comes along: the 10 `debug-*` SOP skills, the `sku-drilldown` sub-agent, the
MCP data tools, and the tool-call announcement hook.

## What ships

| Component | Path | Becomes |
|---|---|---|
| Entry-point skill | `.claude/skills/analyze/` | `/osmos-data-analysis:analyze` |
| Metric SOP skills | `.claude/skills/debug-*/` | `/osmos-data-analysis:debug-roas`, … (10) |
| Sub-agent | `.claude/agents/sku-drilldown.md` | `@osmos-data-analysis:sku-drilldown` |
| Tool-call visibility hook | `.claude/hooks/hooks.json` | `PreToolUse` on every call |
| Data layer | `.mcp.json` | MCP tools |

Manifest: `.claude-plugin/plugin.json`. Catalog: `.claude-plugin/marketplace.json`
(marketplace name `osmos-agents`). The manifest points at the existing `.claude/`
directories rather than copying them, so there is exactly one copy of every skill and
local development in this repo and plugin distribution stay in sync.

Bare `/analyze` also works when no other installed plugin claims that name; the namespaced
form always works.

## Install (per user)

```shell
/plugin marketplace add https://<your-git-host>/<org>/osmos-data-analysis-agent
/plugin install osmos-data-analysis@osmos-agents
/reload-plugins
```

## Install (whole org, no per-user steps)

Push this to your team's shared `settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "osmos-agents": {
      "source": {
        "source": "github",
        "repo": "<org>/osmos-data-analysis-agent"
      }
    }
  },
  "enabledPlugins": {
    "osmos-data-analysis@osmos-agents": true
  },
  "permissions": {
    "allow": [
      "mcp__plugin_osmos-data-analysis_osmos-performance-local"
    ]
  }
}
```

The `permissions.allow` entry pre-approves the plugin's MCP data tools. Without it every
user gets a permission prompt on the first data call of every investigation. The tools are
read-only report fetches, so allowlisting them org-wide is safe. Note the scoped name
form — a plugin's MCP server is exposed as
`mcp__plugin_<plugin-name>_<server-name>__<tool>`, and a rule written against the bare
server name never matches.

### Skills must declare `allowed-tools: Read`

Every skill here carries `allowed-tools: Read` in its frontmatter. This is **required**,
not cosmetic: the skills read sibling reference files (`references/intake-protocol.md`,
`references/common-rules.md`), and once installed the plugin lives outside the user's
working directory, so those reads are denied without the grant. Verified by testing — the
skill silently loses its SOP and improvises.

`allowed-tools: Read(${CLAUDE_SKILL_DIR}/**)` does **not** work as a tighter form.
`${CLAUDE_SKILL_DIR}` is only substituted in `Bash` rules, so the path-scoped rule never
matches and the read is still denied. Use the bare `Read`. **Any new skill added to this
plugin needs the same line.**

## Two things to know before rolling out

**1. The MCP server path is laptop-local — this is the actual blocker.** `.mcp.json`
currently points at
`/Users/manav.kumawat/Documents/agent/osmos-performance-mcp/local_dev_server.py`, the demo
shim from `LOCAL_DEMO.md`. That path does not exist on anyone else's machine, so the
plugin installs fine but every data tool fails. Before org rollout, `.mcp.json` must point
at the **hosted** `osmos-performance` MCP (see "Current wiring status" in `CLAUDE.md` and
`kam_report_configs/AUTHORING_STATUS.md`). Until then this packaging is testable locally
but not shippable.

**2. `CLAUDE.md` does not travel with a plugin.** Per the Claude Code docs, a plugin's
`CLAUDE.md` is not loaded as project context — plugins contribute context through skills,
agents, and hooks only. The intake protocol therefore now lives in
`.claude/skills/analyze/references/intake-protocol.md`, which is the single source of
truth; `CLAUDE.md` points at it. **Any new agent-wide rule must go in that reference file,
not in `CLAUDE.md`**, or it will silently apply for people working inside this repo and
not for anyone invoking the plugin from elsewhere.

## Tracking token usage across the org

Claude Code's OpenTelemetry export attributes tokens to the plugin, skill, sub-agent, and
MCP server that spent them, so this agent's usage separates cleanly from everyone's general
Claude Code use. No custom instrumentation is needed — but telemetry is **off by default**
and an admin has to enable it.

### Enable it (admin, managed settings)

`/Library/Application Support/ClaudeCode/managed-settings.json` on macOS, pushed via MDM:

```json
{
  "env": {
    "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
    "OTEL_METRICS_EXPORTER": "otlp",
    "OTEL_LOGS_EXPORTER": "otlp",
    "OTEL_EXPORTER_OTLP_PROTOCOL": "grpc",
    "OTEL_EXPORTER_OTLP_ENDPOINT": "http://<your-collector>:4317",
    "OTEL_EXPORTER_OTLP_HEADERS": "Authorization=Bearer <token>"
  }
}
```

Managed settings can't be overridden by users, so coverage is guaranteed once it lands.

### The attributes that matter here

`claude_code.token.usage` (unit: tokens) and `claude_code.cost.usage` (USD) both carry:

| Attribute | Use for this agent |
|---|---|
| `plugin.name` | `osmos-data-analysis` — **the top-level filter for all agent usage** |
| `skill.name` | which SOP: `analyze`, `debug-roas`, `debug-rr`, … |
| `agent.name` | `sku-drilldown` fan-out cost |
| `mcp_server.name` / `mcp_tool.name` | which KAM tools drive spend |
| `query_source` | `main` vs `subagent` vs `auxiliary` |
| `type` | `input` / `output` / `cacheRead` / `cacheCreation` |
| `model`, `effort` | model mix and effort level |
| `user.email`, `session.id`, `organization.id` | who and which session |

### Example queries

Total tokens spent by the agent, by type:

```promql
sum by (type) (claude_code_token_usage_total{plugin_name="osmos-data-analysis"})
```

Which SOP is expensive — cost per skill:

```promql
sum by (skill_name) (claude_code_cost_usage_total{plugin_name="osmos-data-analysis"})
```

Adoption — distinct users per week:

```promql
count by (user_email) (claude_code_session_count_total{plugin_name="osmos-data-analysis"})
```

Cache effectiveness (the `debug-*` skills are long, so `cacheRead` should dominate `input`):

```promql
sum by (type) (claude_code_token_usage_total{plugin_name="osmos-data-analysis", type=~"cacheRead|cacheCreation|input"})
```

Metric names above are the Prometheus-normalized form (dots → underscores, `_total`
suffix); if you export straight to an OTLP backend, use the dotted names as documented.

### Verify attribution before trusting the dashboard

`plugin.name` / `skill.name` tag the requests made **while that skill or plugin is active**.
A skill's content stays in context across turns, so a long investigation should stay
attributed, but confirm the boundary behaviour yourself rather than assuming it: run one
`/osmos-data-analysis:analyze` session with `OTEL_METRICS_EXPORTER=console` and
`OTEL_METRIC_EXPORT_INTERVAL=10000`, then check that the follow-up turns after intake still
carry `plugin.name`. Anything attributed to the bare session instead of the plugin is
usage you'd undercount.

### If you can't stand up a collector

Two weaker fallbacks:

- **Anthropic Console → Usage**, or the organization usage report API, gives per-user and
  per-day Claude Code totals. No plugin/skill breakdown — you'd see that a KAM user spent
  tokens, not that this agent spent them.
- **`/cost` and `/usage`** report the current session only, per user. Fine for spot-checking
  what one investigation costs, useless for org-wide tracking.

## Versioning

`version` is deliberately unset in `plugin.json`, so the plugin is versioned by git commit
SHA and users pick up changes on every push. If you switch to explicit semver, you must
bump it on every change or `/plugin update` reports "already at the latest version".

## Local development and pre-push testing

Validate the manifests after any edit:

```shell
claude plugin validate .
```

Then **sideload** the plugin — this loads it for one session without touching your global
config, and running from an unrelated directory is what proves it works away from this
repo:

```shell
cd /tmp/somewhere-else
claude --plugin-dir /Users/<you>/Documents/agent/osmos-data-analysis-agent
```

Checks worth running before pushing:

| Check | How |
|---|---|
| All 11 skills load | ask "list every skill from a plugin" — expect the 10 `debug-*`; `analyze` is hidden from the model by `disable-model-invocation` and won't appear |
| `/analyze` is user-invocable | type `/osmos-data-analysis:analyze` with no args — it should ask which marketplace |
| Reference files are readable | run a real ask and confirm it reads `intake-protocol.md` instead of improvising |
| Sub-agent registered | it appears as `osmos-data-analysis:sku-drilldown` |
| MCP server attached | `/mcp` shows `plugin:osmos-data-analysis:osmos-performance-local` |
| Hook fires | `claude --debug hooks --debug-file h.log …` then grep `h.log` for `announce_tool_call` |

Two headless-mode gotchas when scripting these checks with `-p`: the hook's `systemMessage`
is not rendered (it's a TUI affordance — confirm it in the debug log instead), and
`--strict-mcp-config` suppresses the plugin's own MCP server, so omit it when you want to
exercise the data tools.

To test the full install path instead of sideloading, add this directory as a local
marketplace:

```shell
/plugin marketplace add /Users/<you>/Documents/agent/osmos-data-analysis-agent
/plugin install osmos-data-analysis@osmos-agents
```

Note that `.claude/settings.json` no longer registers the announcement hook — the plugin
does. Registering it in both places would announce every tool call twice for anyone with
the plugin installed who is also working inside this repo.
