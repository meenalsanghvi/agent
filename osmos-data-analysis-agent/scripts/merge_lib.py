"""Shared helpers for building merged KAM report configs.

Each merge is declared as a spec: which existing configs it absorbs, which extra
columns it adds, and the query template it runs. The merged config's columns are the
UNION of its members' columns (first definition wins, unless overridden), so the
provenance of every column stays traceable to the config it came from.
"""

import json
import os
from collections import OrderedDict

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "kam_report_configs")
ROOT = os.path.normpath(ROOT)


def load(rel):
    """Load a config by its original relative path.

    Falls back to `_retired/` so the merge specs stay re-runnable after
    retire_merged.py has moved the absorbed members out of their skill directories.
    """
    path = os.path.join(ROOT, rel)
    if not os.path.exists(path):
        retired = os.path.join(ROOT, "_retired", os.path.basename(rel))
        if os.path.exists(retired):
            path = retired
    with open(path) as fh:
        return json.load(fh)


def union_columns(members, kind, order, overrides=None, extra=None, tags=None, drop=None):
    """Union `kind` ('attributes'|'metrics') across member configs.

    order    - explicit key order for the merged config
    overrides- {key: {field: value}} patched onto the inherited definition
    extra    - {key: full column dict} for columns no member has
    tags     - filterTags applied to every column (reports and columns must intersect)
    drop     - member columns to deliberately NOT carry forward. Dropping is opt-in and
               must be justified in the spec: the default is that omitting a member
               column is an error, which is what guarantees the merge loses nothing.
    """
    pool = {}
    for m in members:
        for key, col in (m.get(kind) or {}).items():
            pool.setdefault(key, dict(col))
    if extra:
        for key, col in extra.items():
            pool[key] = dict(col)

    out = OrderedDict()
    for key in order:
        if key not in pool:
            raise KeyError(f"{kind}.{key} not found in any member and not supplied as extra")
        col = dict(pool[key])
        if overrides and key in overrides:
            col.update(overrides[key])
        col["key"] = key
        col.setdefault("externalColumnName", key)
        if tags:
            col["filterTags"] = list(tags)
        out[key] = col

    missing = set(pool) - set(order) - set(drop or ())
    if missing:
        raise ValueError(f"{kind}: member columns dropped without being listed: {sorted(missing)}")
    return out


def build(spec):
    """Build one merged config from a spec dict and write it to disk."""
    members = [load(p) for p in spec["absorbs"]]
    base = members[0]
    tags = spec["filterTags"]

    cfg = OrderedDict()
    cfg["reportType"] = spec["reportType"]
    cfg["externalReportType"] = spec["externalReportType"]
    cfg["visibility"] = base.get("visibility", "INTERNAL_PERFORMANCE")
    cfg["filterTags"] = list(tags)
    cfg["externalRequiredFilters"] = spec.get("externalRequiredFilters", [])
    cfg["description"] = " ".join(spec["description"].split())
    cfg["source"] = base["source"]
    cfg["sourceInfo"] = base["sourceInfo"]
    cfg["cacheInfo"] = base["cacheInfo"]
    cfg["attributes"] = union_columns(
        members, "attributes", spec["attributes"],
        spec.get("attribute_overrides"), spec.get("extra_attributes"), tags,
        spec.get("drop_attributes"),
    )
    cfg["metrics"] = union_columns(
        members, "metrics", spec["metrics"],
        spec.get("metric_overrides"), spec.get("extra_metrics"), tags,
        spec.get("drop_metrics"),
    )
    cfg["dateRanges"] = spec.get("dateRanges", base.get("dateRanges"))
    cfg["query"] = {"REPORTING": " ".join(spec["query"].split()), "MERCHANT": "", "GROUPED": ""}
    cfg["application"] = base.get("application", "irisTestApplication")

    path = os.path.join(ROOT, spec["path"])
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(cfg, fh, indent=2)
        fh.write("\n")
    return cfg, path


def run(specs):
    for spec in specs:
        cfg, path = build(spec)
        print(
            f"  wrote {os.path.relpath(path, ROOT):55s} "
            f"attrs={len(cfg['attributes']):2d} metrics={len(cfg['metrics']):2d} "
            f"absorbs={len(spec['absorbs'])}"
        )


def col(selector, ctype, description, external=None):
    """Shorthand for an `extra` column definition."""
    return {
        "selector": selector,
        "type": ctype,
        "description": " ".join(description.split()),
        **({"externalColumnName": external} if external else {}),
    }
