"""Validate merged KAM report configs.

Three checks per merged config:
  1. JSON is well formed and carries every field the KAM config validator requires.
  2. Every table alias referenced by an attribute/metric selector is actually bound by
     the query template -- this is the failure mode when a column is inherited from a
     member that used a different alias.
  3. Coverage: every retired report's (attributes, metrics) key set is a subset of its
     successor's, so no caller loses a column.

Usage:  python3 validate_merged.py
"""

import json
import os
import re
import sys

from merge_lib import ROOT, load

REQUIRED_TOP = [
    "reportType", "externalReportType", "visibility", "filterTags",
    "description", "source", "sourceInfo", "attributes", "metrics", "query",
]

# merged config -> configs it retires
COVERAGE = {}

# Pre-existing gaps inherited from the retired configs. Listed here so the check stays
# on for every other report; fixing these is tracked separately in MERGE_ANALYSIS.md.
ALLOW_UNSCOPED = {
    # os_ads_db_campaign_targeting_mapping has no agency column and neither retired
    # config (BY_ID, VIA_CTD) scoped by tenant -- they rely entirely on the caller's
    # campaign_id filter. Merging preserved that behaviour rather than changing it.
    "shared/INTERNAL_PERF_CAMPAIGN_NETWORKS.json",
}


# merged config -> {"attributes": [...], "metrics": [...]} deliberately not carried
# forward. Declared in the specs with a justification; surfaced in the report so an
# intentional drop can never quietly look like full coverage.
DROPPED = {}


def _load_coverage():
    """Read the merge specs so coverage is derived from the same source of truth."""
    for wave in ("merge_wave1", "merge_wave2", "merge_wave3"):
        try:
            mod = __import__(wave)
        except ImportError:
            continue
        for spec in mod.SPECS:
            COVERAGE[spec["path"]] = [
                p for p in spec["absorbs"] if p != spec["path"]
            ]
            drops = {"attributes": set(spec.get("drop_attributes") or ()),
                     "metrics": set(spec.get("drop_metrics") or ())}
            if drops["attributes"] or drops["metrics"]:
                DROPPED[spec["path"]] = drops


def bound_aliases(template):
    """Aliases the FROM/JOIN clauses of a template bind."""
    aliases = set(re.findall(r"(?:AS\s+)?([A-Za-z_][A-Za-z0-9_]*)\s+ON\b", template))
    aliases |= set(re.findall(r"`[^`]+`\s+(?:AS\s+)?([A-Za-z_][A-Za-z0-9_]*)\b", template))
    aliases |= set(re.findall(r"\)\s*(?:AS\s+)?([A-Za-z_][A-Za-z0-9_]*)\b", template))
    return {a for a in aliases if a.upper() not in {
        "ON", "AS", "JOIN", "INNER", "LEFT", "RIGHT", "FULL", "OUTER", "WHERE",
        "GROUP", "BY", "SELECT", "FROM", "AND", "OR", "SAFE_CAST", "CAST", "IN",
    }}


def referenced_aliases(selector):
    """Aliases a selector reads from, ignoring SQL function calls."""
    hits = set()
    for m in re.finditer(r"\b([A-Za-z_][A-Za-z0-9_]*)\.", selector):
        hits.add(m.group(1))
    # `prj-onlinesales-prod-01.reporting.table` inside a correlated subquery
    return {h for h in hits if not h.startswith("prj") and h != "reporting"}


def check(rel, retired):
    cfg = load(rel)
    errs = []

    for field in REQUIRED_TOP:
        if not cfg.get(field):
            errs.append(f"missing required field: {field}")

    template = cfg["query"]["REPORTING"]
    if "__AGENCY_ID__" not in template and rel not in ALLOW_UNSCOPED:
        errs.append("template does not scope by __AGENCY_ID__")
    if not cfg["metrics"]:
        errs.append("no metrics (KAM fetch requires >= 1)")

    bound = bound_aliases(template)
    # subquery-local aliases: anything bound inside a nested SELECT is also fine
    for kind in ("attributes", "metrics"):
        for key, colr in cfg[kind].items():
            # a selector may be a correlated subquery that binds its own aliases
            local = bound | bound_aliases(colr["selector"])
            for alias in referenced_aliases(colr["selector"]):
                if alias not in local:
                    errs.append(f"{kind}.{key}: selector references unbound alias '{alias}'")
            if not colr.get("filterTags"):
                errs.append(f"{kind}.{key}: no filterTags (column will not resolve externally)")
            if set(colr.get("filterTags", [])).isdisjoint(cfg["filterTags"]):
                errs.append(f"{kind}.{key}: filterTags do not intersect report filterTags")

    for old_rel in retired:
        old_path = os.path.join(ROOT, old_rel)
        if not os.path.exists(old_path):
            old_path = os.path.join(ROOT, "_retired", os.path.basename(old_rel))
            if not os.path.exists(old_path):
                errs.append(f"coverage: retired config not found: {old_rel}")
                continue
        with open(old_path) as fh:
            old = json.load(fh)
        for kind in ("attributes", "metrics"):
            missing = set(old.get(kind) or {}) - set(cfg[kind])
            missing.discard("placeholder_metric")
            missing -= DROPPED.get(rel, {}).get(kind, set())
            if missing:
                errs.append(
                    f"coverage: {os.path.basename(old_rel)} {kind} not covered: {sorted(missing)}"
                )
    return errs


def main():
    _load_coverage()
    if not COVERAGE:
        print("no merge specs found", file=sys.stderr)
        return 1

    total = 0
    for rel in sorted(COVERAGE):
        errs = check(rel, COVERAGE[rel])
        name = os.path.basename(rel)
        if errs:
            total += len(errs)
            print(f"FAIL {name}")
            for e in errs:
                print(f"       {e}")
        else:
            note = ""
            if rel in DROPPED:
                d = sorted(DROPPED[rel]["attributes"] | DROPPED[rel]["metrics"])
                note = f"  [deliberately dropped: {d}]"
            print(f"ok   {name}  (covers {len(COVERAGE[rel])} retired){note}")
    print(f"\n{len(COVERAGE)} merged configs, {total} problems")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
