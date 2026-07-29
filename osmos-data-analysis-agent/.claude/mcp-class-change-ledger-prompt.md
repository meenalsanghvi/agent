# Prompt — KAM class-change ledger (triage every SOP tool)

## Goal
Triage **every** data-fetching tool of the data-analysis agent into one of three
buckets, so we know up front which tools ship as **config-only** (no kamService
change) and which need **kamService class changes** — and group the class changes
into a small number of **cohesive PRs** we can hand the kamService owner.

The output is a single ledger: `kam_report_configs/CLASS_CHANGE_LEDGER.md`.

## Why (context)
- A **KAM report config** is JSON posted to KAM's Mongo — *data*, deployed anytime,
  no code review. A **KAM class** (`kamService/src/utils/schema/*Class.js` +
  `schemaRegistry.js`) is *code* — needs a PR + deploy.
- A tool is **config-only** iff *every* metric / attribute / filter / grouping its
  source query needs is already exposed by an existing, registered class.
- If a needed table has **no class**, or an existing class is **missing a metric /
  attribute / filter** the query needs, the tool needs a **class change** (a PR).
- Validated already, config-only: `check_ctr_overall` (`MonetizeMerchantFacts`).
- Known gap (the pivotal one): `ClientVendorChannelPerformanceFacts` (cvcpf) has no
  channel/vendor filter attribute for the PLA/Display split, no converted-spend
  metric (its `spend` = `SUM(cost)`), and no overall per-click-timestamp program
  metrics. Any tool whose query reads cvcpf **with a channel filter and/or
  per-click-timestamp attribution and/or converted spend** needs that enhancement.

## Inputs
- Source-of-truth per tool: `query_inventory/**/*.sql`. Each file has a header block
  documenting: `tables:`, `injected_fragments:` (e.g. `channel_condition`),
  `python_derived_metrics:`, and params. **Read the header — that is the contract.**
- Existing classes: every `*Class.js` basename in
  `/Users/manav.kumawat/Desktop/kamService/src/utils/schema/` maps to a table by
  snake_casing the name (e.g. `OsProductAdsPageNamePerformanceFactsClass` →
  `os_product_ads_page_name_performance_facts`). A table **has a class** iff a
  matching `*Class.js` (or `*AttributesClass.js`/`*MetricsClass.js`) exists.
- Files named `*__<suffix>.sql` (e.g. `..__resolve_sellers`, `..__product_names`)
  and `_fragment_*` / `lookup_*` / `fetch_marketplace_info*` are **sub-queries /
  resolvers / id-lookups**, not standalone tools — note them as "helper" and fold
  into their parent tool's row; don't give them their own PR verdict.

## Per-tool triage record (produce for every real tool)
| Field | Meaning |
|---|---|
| `tool` | function name (from the header `source:` / filename) |
| `skill` | owning skill dir (roas/cpc/ctr/bu/rr/budget_pacing/keyword_delivery/irrelevancy/shared) |
| `tables` | tables the query reads |
| `needs` | the *specific* metrics/attributes/filters/grouping the query requires (esp. channel/program filters, per-click-timestamp attribution, converted spend, raw-request or minute-level or S3 sources) |
| `class_map` | each table → its class name, or **NO CLASS** |
| `verdict` | `config-only` \| `needs-class` \| `verify` |
| `pr_bucket` | if `needs-class`: `PR1-cvcpf` (cvcpf channel-split / converted-spend / per-click-timestamp) \| `PR2-newclass` (table has no class, or a brand-new metric on another class) — else `—` |
| `gap` | if `needs-class`: the class + exactly what's missing (one line) |
| `note` | anything to verify, or a config-only deviation option (e.g. "faithful=cvcpf; config-only alt = MMF merchant-grain, validate vs legacy") |

### Verdict rules
- **config-only** — all needed metrics/attrs/filters plainly exist on existing
  classes (standard clicks/impressions/spend/ctr/cpc/ir from base; grouping by an
  attribute the dimension class exposes; single fact table). Say so.
- **needs-class** — a table has NO class, OR a documented gap applies (cvcpf split /
  converted spend / per-click-timestamp), OR the query needs a metric/attribute that
  the class clearly lacks. Assign the PR bucket + one-line gap.
- **verify** — you can't tell from the header alone whether the class exposes a
  needed metric (it's plausible but unconfirmed). Mark `verify` and say which class
  file + which metric/attr to confirm. **Do not guess config-only when unsure** —
  `verify` is the honest bucket; false "config-only" costs us a failed fetch later.

## Rules
- Be honest about uncertainty — prefer `verify` over an optimistic `config-only`.
- Where a tool's *faithful* source needs a class change but a **config-only
  substitute** exists (e.g. MMF merchant-grain instead of cvcpf), record BOTH: the
  faithful verdict in `verdict`/`pr_bucket`, and the substitute in `note`.
- Do not read every class file line-by-line — use the header + the class-name→table
  map; only open a class file when a single confirm decides verdict vs `verify`.

## Deliverable — `kam_report_configs/CLASS_CHANGE_LEDGER.md`
1. **Summary counts**: # tools, # config-only, # needs-class (split PR1 vs PR2),
   # verify.
2. **PR1 — cvcpf enhancement**: the tools it unblocks + the exact class additions
   (channel/vendor filter attribute, converted-spend metric, per-click-timestamp
   program metrics), each as a checklist item.
3. **PR2 — new classes**: per new table needed, the tools it unblocks.
4. **Config-only queue** (ordered, ready to author now): tool → suggested reportType
   → classes reused.
5. **Verify queue**: each with the one class-file check that resolves it.
6. **Full per-tool table** (all fields above), grouped by skill.
Keep it scannable — tables over prose. This ledger drives both the config-authoring
order and the two kamService PRs.
