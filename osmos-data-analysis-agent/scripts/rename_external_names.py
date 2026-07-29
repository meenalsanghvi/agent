"""Prefix every external column name, and spell out the report_group tags.

Two renames, done together because both touch every config and every columnMetadata
row, and each would otherwise need its own re-post + re-sync + verification pass.

WHY THE COLUMN PREFIX
    columnMetadata is a single global row per columnName, and a POST *replaces* that
    row's filterTags. A column is served to a report only when their tags intersect.
    So any team posting `spend` with only their own tag silently breaks every other
    team's report that uses it — no error, no log. This has now happened in both
    directions: we stripped 16 production columns, and something later stripped
    `report_group:intake` off `agency_id`, `region` and `currency`, which broke the
    agent's marketplace lookup entirely.

    45 of our 174 columns are currently shared. Prefixing all 174 makes collision
    structurally impossible rather than merely unlikely — a name only we use is a row
    only we write. We prefix all, not just today's 45, because an exclusive name
    becomes shared the moment another team adopts it and nothing would warn us.

    The org convention says reuse canonical names. That exists for consistency within
    a catalogue — and ours is a separate mount (INTERNAL_PERFORMANCE), so an agent
    here never sees a BEATS or PULSE column. Internal consistency is what matters,
    and a uniform prefix preserves it.

WHY THE TAG RENAME
    Every distinct report_group value mints an MCP tool named
    get_<plural(value)>_reports, where plural() naively appends "s". `bu` gave
    `get_bus_reports`, `rr` gave `get_rrs_reports`. The taxonomy is the agent's menu,
    so the values are spelled out and chosen to pluralise legibly.

Usage:  python3 scripts/rename_external_names.py [--dry-run|--apply]
Idempotent: already-prefixed columns and already-renamed tags are left alone.
"""

import argparse
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, ".."))
CONFIGS = os.path.join(REPO, "kam_report_configs")

PREFIX = "perf_"

# old report_group value -> new. Chosen so plural() reads as English.
TAGS = {
    "bu":                 "budget_utilisation",
    "rr":                 "response_rate",
    "ctr":                "click_through",
    "cpc":                "cost_per_click",
    "category":           "categories",
    "sku":                "skus",
    "keyword":            "keywords",
    "campaign":           "campaigns",
    "merchant_breakdown": "merchant_breakdowns",
    "search_query":       "search_queries",
    "page_performance":   "page_performances",
    "budget_pacing":      "budget_pacings",
    "irrelevancy":        "relevance",
    # unchanged, already legible: roas, intake
}


def plural(v):
    return v if v.endswith("s") else v + "s"


def rename_tag(tag):
    if not tag.startswith("report_group:"):
        return tag  # never touch another team's namespace
    val = tag.split(":", 1)[1]
    return "report_group:" + TAGS.get(val, val)


def rename_col(name):
    return name if name.startswith(PREFIX) else PREFIX + name


def process(cfg):
    """Returns (changed_columns, changed_tags)."""
    cols = tags = 0

    new_tags = [rename_tag(t) for t in (cfg.get("filterTags") or [])]
    if new_tags != cfg.get("filterTags"):
        cfg["filterTags"] = new_tags
        tags += 1

    for section in ("attributes", "metrics"):
        for c in (cfg.get(section) or {}).values():
            ext = c.get("externalColumnName")
            if ext:
                new = rename_col(ext)
                if new != ext:
                    c["externalColumnName"] = new
                    cols += 1
            ct = [rename_tag(t) for t in (c.get("filterTags") or [])]
            if ct != c.get("filterTags"):
                c["filterTags"] = ct
                tags += 1

    # externalRequiredFilters name EXTERNAL columns — they must move too, or the MCP
    # will demand a filter whose column no longer exists.
    req = cfg.get("externalRequiredFilters") or []
    new_req = [rename_col(r) for r in req]
    if new_req != req:
        cfg["externalRequiredFilters"] = new_req
        cols += 1

    return cols, tags


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if a.apply == a.dry_run:
        sys.exit("pick exactly one of --dry-run / --apply")

    paths = [p for p in sorted(glob.glob(os.path.join(CONFIGS, "*", "*.json")))
             if os.path.basename(os.path.dirname(p)) != "_retired"]

    tot_c = tot_t = touched = 0
    all_tags, all_cols = set(), set()
    for p in paths:
        cfg = json.load(open(p))
        c, t = process(cfg)
        for tag in cfg.get("filterTags") or []:
            all_tags.add(tag)
        for sec in ("attributes", "metrics"):
            for col in (cfg.get(sec) or {}).values():
                if col.get("externalColumnName"):
                    all_cols.add(col["externalColumnName"])
        if c or t:
            touched += 1
            tot_c += c
            tot_t += t
            if a.apply:
                json.dump(cfg, open(p, "w"), indent=2)
                open(p, "a").write("\n")

    print(f"{'APPLIED' if a.apply else 'DRY RUN'} — {len(paths)} active configs")
    print(f"  configs touched      : {touched}")
    print(f"  column renames       : {tot_c}")
    print(f"  tag-list rewrites    : {tot_t}")
    print(f"  distinct columns now : {len(all_cols)}")
    unprefixed = sorted(c for c in all_cols if not c.startswith(PREFIX))
    print(f"  still unprefixed     : {unprefixed or 'none'}")
    print("\n  report_group tags -> MCP tool name")
    for t in sorted(all_tags):
        if t.startswith("report_group:"):
            v = t.split(":", 1)[1]
            print(f"    {t:38s} get_{plural(v)}_reports")
    return 0


if __name__ == "__main__":
    sys.exit(main())
