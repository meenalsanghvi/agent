#!/usr/bin/env python3
"""
post_external.py — post an INLINE + EXTERNAL KAM report and fetch it via useExternalNames
=========================================================================================
The chosen workflow: an inline (Gen1) report config carrying the external-report fields
(`externalReportType`, `visibility`, `filterTags`) and per-column `externalColumnName` is
posted to KAM; its columnMetadata is derived from the config and posted; then it's fetched
with `useExternalNames: true` — exactly how osmos-reporting-mcp's run_report calls it.

Steps: (1) derive + POST columnMetadata from the config's externalColumnName columns,
(2) POST the config, (3) GET /report/config/external to confirm it's catalogued,
(4) POST /report/fetch with useExternalNames:true using the EXTERNAL names.

Usage:
  python post_external.py --config shared/INTERNAL_PERF_PAGE_LEVEL.json \
    --agency 105 --current 2026-07-19 2026-07-21
No auth token / no proxy (KAM test env is internal-network trust; session ignores env proxies).
"""
from __future__ import annotations
import argparse, json, sys
import requests

BASE = "http://test.onlinesales.ai"
APP = "irisTestApplication"
H = {"Content-Type": "application/json"}
S = requests.Session(); S.trust_env = False


def _extract_external_columns(cfg):
    """Return {externalColumnName: {description, filterTags}} for every exposed column."""
    out = {}
    for section in ("attributes", "metrics"):
        for _, d in (cfg.get(section) or {}).items():
            ext = d.get("externalColumnName")
            if ext:
                out[ext] = {"description": d.get("description", ""),
                            "filterTags": d.get("filterTags", [])}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--agency", type=int, required=True)
    ap.add_argument("--current", nargs=2, metavar=("START", "END"), required=True)
    ap.add_argument("--attributes", nargs="*", default=None, help="External attr names (default: all)")
    ap.add_argument("--metrics", nargs="*", default=None, help="External metric names (default: all)")
    ap.add_argument("--filter", action="append", default=[], dest="filters",
                    metavar="KEY:OP:V1,V2",
                    help="Repeatable fetch filter, e.g. --filter os_client_id:IN:277661 "
                         "or --filter search_query:IN:iphone,tv%20bracket (external names).")
    ap.add_argument("--visibility", default=None,
                    help="Override the config's visibility in the POSTed body only; the file "
                         "on disk is not modified. Needed while INTERNAL_PERFORMANCE is not yet "
                         "in kamService's VALID_VISIBILITY_VALUES on this env — post as "
                         "INTERNAL_USER and reconcile later via repost_internal_performance.sh.")
    ap.add_argument("--skip-post", action="store_true")
    ap.add_argument("--no-fetch", action="store_true",
                    help="Post config + columnMetadata only; skip the validation fetch "
                         "(use for bulk re-posts where per-report fetch is unnecessary/heavy).")
    args = ap.parse_args()

    def _parse_filter(s):
        key, op, vals = s.split(":", 2)
        return {"key": key, "operator": op, "values": vals.split(",")}
    fetch_filters = [_parse_filter(f) for f in args.filters]

    cfg = json.load(open(args.config))
    if args.visibility:
        print(f"[visibility] {cfg.get('visibility')} -> {args.visibility} (posted body only)")
        cfg["visibility"] = args.visibility
    ext_cols = _extract_external_columns(cfg)
    ext_rt = cfg["externalReportType"]

    if not args.skip_post:
        # MERGE, never replace: columnMetadata is global by columnName, so union this
        # report's tags with (a) the production-file tags and (b) the current test-env tags,
        # so we never strip another report's (BEATS/PULSE/LOCALIUM or ours) filterTags.
        from sync_column_metadata import prod_tags as _prod, current_tags as _cur
        prod = _prod(); cur = _cur(list(ext_cols))
        cols = []
        for n, v in ext_cols.items():
            merged = sorted(set(v.get("filterTags") or [])
                            | prod.get(n, {}).get("tags", set())
                            | cur.get(n, set()))
            cols.append({"columnName": n,
                         "description": prod.get(n, {}).get("desc") or v["description"],
                         "filterTags": merged})
        r = S.post(f"{BASE}/kamService/report/column-metadata",
                   data=json.dumps({"application": APP, "columns": cols}), headers=H, timeout=60)
        print(f"[columnMetadata] {r.status_code} {r.text[:160]}")
        # Look up the existing config id for update-in-place.
        # Guarded: only ever write a document we just read AND positively identified as
        # ours. A wrong id here overwrites somebody else's report config.
        if not cfg["reportType"].startswith("INTERNAL_PERF_"):
            sys.exit(f"[guard] refusing to post non-INTERNAL_PERF_ reportType: {cfg['reportType']}")
        q = json.dumps({"reportTypes": [cfg["reportType"]], "application": APP})
        g = S.get(f"{BASE}/kamService/report/config", params={"jsonQuery": q}, headers=H, timeout=60)
        if g.status_code != 200:
            sys.exit(f"[guard] config lookup failed ({g.status_code}); refusing to post blind")
        existing = (g.json() or {}).get("reports", [])
        body = dict(cfg)
        if len(existing) > 1:
            sys.exit(f"[guard] {len(existing)} configs match {cfg['reportType']} — ambiguous, "
                     "refusing to guess which to overwrite")
        if existing:
            doc = existing[0]
            if doc.get("reportType") != cfg["reportType"]:
                sys.exit(f"[guard] lookup returned reportType {doc.get('reportType')!r}, "
                         f"expected {cfg['reportType']!r} — refusing to overwrite")
            eid = doc.get("id") or doc.get("_id")
            if isinstance(eid, dict): eid = eid.get("$oid")
            if eid: body["id"] = eid
        r = S.post(f"{BASE}/kamService/report/config", data=json.dumps(body), headers=H, timeout=60)
        if r.status_code != 200: sys.exit(f"[config] {r.status_code}: {r.text}")
        print(f"[config] OK — {cfg['reportType']} ({'updated' if existing else 'inserted'})")

    g = S.get(f"{BASE}/kamService/report/config/external", params={"application": APP}, headers=H, timeout=60)
    reports = (g.json() or {}).get("reports", []) if g.status_code == 200 else []
    present = any((x.get("externalReportType") == ext_rt) for x in reports)
    print(f"[catalogue] {g.status_code} · {len(reports)} reports · {ext_rt} present: {present}")

    if args.no_fetch:
        return

    attrs = args.attributes if args.attributes is not None else [
        c for c in ext_cols if c in _extract_external_columns({"attributes": cfg.get("attributes")})]
    metrics = args.metrics if args.metrics is not None else [
        c for c in ext_cols if c in _extract_external_columns({"metrics": cfg.get("metrics")})]
    body = {"application": APP, "agencyId": args.agency, "reportType": ext_rt,
            "requestType": "REPORTING", "useExternalNames": True,
            "attributes": attrs, "metrics": metrics,
            "dateRanges": [{"startDate": args.current[0], "endDate": args.current[1]}],
            "filters": fetch_filters, "limit": 1000, "offset": 0}
    r = S.post(f"{BASE}/kamService/report/fetch", data=json.dumps(body), headers=H, timeout=120)
    print(f"[fetch useExternalNames] {r.status_code}")
    if r.status_code == 200:
        data = r.json().get("data", [])
        print(f"  {len(data)} row(s):")
        print(json.dumps(data[:10], indent=2))
    else:
        print("  ", r.text[:400])


if __name__ == "__main__":
    main()
