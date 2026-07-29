"""Profile the EXTREME grain of every active KAM report config, one TSV per config.

Extreme grain = every requestable attribute at once. That is deliberately not a real
call; it is the ceiling a caller can reach, which is what tells you whether a config is
risk-prone. RR_DISPLAY taught the lesson: bytes barely moved (2.4x) while slot_ms went
43x and shuffle went ~1.5 millionx, because the cost lives in output cardinality, not
scan volume. Bytes alone will not find that.

Safety: every config is DRY-RUN first. If the planner's estimate exceeds --max-gb the
real execution is skipped and the row is flagged, so one pathological config cannot run
away with the bill.

Output: scripts/out/perf/<CONFIG_ID>_<REPORT_TYPE>.tsv  (config ids from
scripts/out/query_consolidated_matrix.csv) plus scripts/out/perf/_index.tsv.

Usage (needs the ETL_pipeline venv python for the hades/osClient libs):
    HTTP_PROXY= HTTPS_PROXY= NO_PROXY="*" \
    "/Users/.../ETL_pipeline copy/.venv/bin/python" profile_all_configs.py \
        --agency 105 --current 2026-07-19 2026-07-21
"""

import argparse
import csv
import json
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import query_cost_profile as Q  # noqa: E402

ROOT = os.path.dirname(HERE)
MATRIX = os.path.join(HERE, "out", "query_consolidated_matrix.csv")

# Attributes that cannot be requested: the template has no __ATTRIBUTES__ slot for them,
# or they were deliberately dropped in the merge. Mirrors build_query_csv.py:UNREQUESTABLE.
UNREQUESTABLE = {
    "INTERNAL_PERF_GMV_ATTRIBUTION": {"channel"},
    "INTERNAL_PERF_RR_DISPLAY": {"store_id"},
}

# Values for externalRequiredFilters. Known-good test ids for agency 105 (takealot, ZAR),
# from TODO_REPORTS_TO_BUILD.md / REMAINING_QUEUE.md.
KNOWN_IDS = {
    "campaign_id": ["1322334"],
    "os_client_id": ["277661"],
    "search_query": ["iphone"],
    "keyword": ["iphone"],
    "ad_unit": ["cart-bottom"],
    # action_type_id is INT64 in audit_logs_v2. With operator IN, KAM emits IN ('17')
    # and BigQuery rejects: "No matching signature for operator IN for argument types
    # INT64 and {STRING}". '=' is the form that survives the type check.
    "action_type_id": ["17"],
}
NUMERIC_FILTERS = {"action_type_id"}


def load_config_ids():
    csv.field_size_limit(10 ** 9)
    ids = {}
    for r in csv.DictReader(open(MATRIX)):
        rt = json.loads(r["report_config"])["reportType"]
        ids.setdefault(rt, r["config_id"])
    return ids


def config_paths():
    import glob
    out = {}
    for f in glob.glob(os.path.join(ROOT, "kam_report_configs", "*", "*.json")):
        if "_retired" in f:
            continue
        out[json.load(open(f))["reportType"]] = f
    return out


def required_filters(cfg):
    """Fill externalRequiredFilters with known test ids. Returns (filters, unmet)."""
    filters, unmet = [], []
    for name in cfg.get("externalRequiredFilters") or []:
        if name in KNOWN_IDS:
            op = "=" if name in NUMERIC_FILTERS else "IN"
            filters.append({"key": name, "operator": op, "values": KNOWN_IDS[name]})
        else:
            unmet.append(name)
    return filters, unmet


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agency", type=int, default=105)
    ap.add_argument("--current", nargs=2, metavar=("START", "END"),
                    default=["2026-07-19", "2026-07-21"])
    ap.add_argument("--max-gb", type=float, default=200.0,
                    help="Skip real execution if the dry-run estimate exceeds this.")
    ap.add_argument("--only", action="append", default=None,
                    help="Only these reportTypes or config ids (repeatable).")
    ap.add_argument("--dry-only", action="store_true",
                    help="Stop after the dry run; never execute.")
    ap.add_argument("--creds", choices=["adc", "hades"], default="hades")
    ap.add_argument("--hades-app-key",
                    default="DATA_VALIDATION_FRAMEWORK_BQ_REPORTING_CREDS")
    ap.add_argument("--hades-application", default="irisTestApplication")
    ap.add_argument("--hades-env", default="prod", choices=["test", "prod"])
    ap.add_argument("--project", default=None)
    a = ap.parse_args()

    ids, paths = load_config_ids(), config_paths()
    targets = sorted(ids.items(), key=lambda kv: kv[1])  # by config_id
    if a.only:
        want = set(a.only)
        targets = [(rt, cid) for rt, cid in targets if rt in want or cid in want]
        if not targets:
            sys.exit(f"nothing matched {a.only}")

    client = Q.build_bq_client(a)
    import requests
    session = requests.Session()
    session.trust_env = False

    outdir = os.path.join(HERE, "out", "perf")
    os.makedirs(outdir, exist_ok=True)
    index = []

    for rt, cid in targets:
        cfg = json.load(open(paths[rt]))
        attrs = [k for k in (cfg.get("attributes") or {})
                 if k not in UNREQUESTABLE.get(rt, set())]
        metrics = list((cfg.get("metrics") or {}).keys())
        filters, unmet = required_filters(cfg)

        rec = {"config_id": cid, "report_type": rt,
               "external_report_type": cfg["externalReportType"],
               "grain": "EXTREME_ALL_ATTRIBUTES",
               "attributes": ",".join(attrs), "n_attributes": len(attrs),
               "metrics": ",".join(metrics), "n_metrics": len(metrics),
               "required_filters": ",".join(cfg.get("externalRequiredFilters") or []),
               "filters_applied": json.dumps(filters) if filters else "",
               "unmet_required_filters": ",".join(unmet),
               "date_start": a.current[0], "date_end": a.current[1],
               "agency": a.agency, "status": "", "error": ""}

        try:
            body = Q.fetch_body(rt, a.agency, a.current, attrs, metrics, filters,
                                use_external=False)
            sql, err = Q.resolve_sql(session, body)
            if err:
                rec["status"], rec["error"] = "RESOLVER_FAILED", err[:400]
            else:
                rec["sql_chars"] = len(sql)
                rec.update(Q.bq_dry_run(client, sql))
                est = rec.get("gb_processed") or 0
                if a.dry_only:
                    rec["status"] = "DRYRUN_ONLY"
                elif est > a.max_gb:
                    rec["status"] = f"SKIPPED_OVER_{a.max_gb}GB"
                else:
                    dry_gb = est
                    rec.update(Q.bq_execute(client, sql))
                    rec["dryrun_gb_estimate"] = dry_gb
                    rec["dryrun_overestimate_x"] = (
                        round(dry_gb / rec["gb_processed"], 1)
                        if rec.get("gb_processed") else None)
                    rec["status"] = "OK"
        except Exception as e:
            rec["status"] = rec["status"] or "ERROR"
            rec["error"] = f"{type(e).__name__}: {e}"[:400]
            if os.environ.get("PROFILE_TRACE"):
                traceback.print_exc()

        cols = list(rec.keys())
        path = os.path.join(outdir, f"{cid}_{rt}.tsv")
        with open(path, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, delimiter="\t",
                               quoting=csv.QUOTE_ALL)
            w.writeheader()
            w.writerow(rec)
        index.append(rec)

        print("  %-5s %-45s %-22s rows=%-10s gb=%-7s slot_ms=%-8s shuffle_mb=%s" % (
            cid, rt, rec["status"], rec.get("rows", "-"), rec.get("gb_processed", "-"),
            rec.get("slot_ms", "-"),
            round((rec.get("shuffle_output_bytes") or 0) / 1024 ** 2, 1)
            if rec.get("shuffle_output_bytes") is not None else "-"))
        sys.stdout.flush()

    icols = []
    for r in index:
        for k in r:
            if k not in icols:
                icols.append(k)
    ipath = os.path.join(outdir, "_index.tsv")
    with open(ipath, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=icols, delimiter="\t",
                           quoting=csv.QUOTE_ALL, restval="")
        w.writeheader()
        w.writerows(index)

    ok = sum(1 for r in index if r["status"] == "OK")
    print(f"\n{len(index)} configs · {ok} OK · "
          f"{len(index) - ok} not executed (see status column)")
    print(f"wrote {len(index)} per-config TSVs + _index.tsv in scripts/out/perf/")


if __name__ == "__main__":
    main()
