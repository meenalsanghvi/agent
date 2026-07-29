"""Profile the BigQuery cost/performance of a KAM report config, per grain.

KAM does not report query cost. What it DOES give us is the fully resolved SQL, via
POST /kamService/report/query (`reportQuery`) -- the identical substitution path as
/report/fetch. So the pipeline is:

    KAM resolver  ->  resolved SQL  ->  BigQuery job stats

Three tiers, selected by --mode:

  latency   no BQ credential needed. Wall-clock of /report/fetch per grain. Coarse:
            conflates KAM overhead + queue + BQ + serialization. Regression signal only.
  dryrun    needs BQ read access. dry_run=True: bytes that WOULD be scanned, plus the
            referenced tables. Free, no execution, deterministic -- the best single
            signal for "is this config's shape efficient", and the only one safe to
            run repeatedly in CI.
  execute   needs BQ access + willingness to actually run. Real job stats: slot_ms,
            bytes billed, cache hit, per-stage plan.

A report config is profiled ONE GRAIN AT A TIME, because a merged config's cost is a
property of the requested column set, not of the config. RR_DISPLAY answers 5 distinct
questions and they do not cost the same.

Usage:
    # tier 0 -- no credential
    HTTP_PROXY= HTTPS_PROXY= NO_PROXY="*" python3 query_cost_profile.py \
        --config ../kam_report_configs/rr/INTERNAL_PERF_RR_DISPLAY.json \
        --agency 105 --current 2026-07-19 2026-07-21 --mode latency

    # tier 1 -- needs GOOGLE_APPLICATION_CREDENTIALS or ADC
    ... --mode dryrun

    # profile SQL you already have, skipping KAM entirely
    ... --mode dryrun --sql-file resolved.sql

Emits scripts/out/query_cost_<REPORT_TYPE>.csv and prints a summary table.
"""

import argparse
import csv
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = "http://test.onlinesales.ai"
APP = "irisTestApplication"
H = {"Content-Type": "application/json"}

# Grains worth profiling per report. A grain = the column set a real caller requests.
# Keyed by reportType; extend as you profile more reports.
GRAINS = {
    "INTERNAL_PERF_RR_DISPLAY": [
        {"name": "page_type",
         "attributes": ["page_type"],
         "filters": [{"key": "page_type", "operator": "NOT IN", "values": ["", "NA"]}],
         "note": "old RR_DISPLAY_PAGE_TYPE_REPORT"},
        {"name": "hour",
         "attributes": ["hour"], "filters": [],
         "note": "old RR_HOURLY_REPORT -- hourly RR curve"},
        {"name": "ad_unit",
         "attributes": ["ad_unit"], "filters": [],
         "note": "old RR_HOURLY_AD_UNIT_REPORT"},
        {"name": "keyword",
         "attributes": ["keyword"],
         "filters": [{"key": "keyword", "operator": "NOT IN", "values": [""]}],
         "note": "old SEARCH_QUERY_RR_DISPLAY_REPORT -- the grain that timed out unscoped"},
        {"name": "keyword+ad_unit",
         "attributes": ["keyword", "ad_unit"],
         "filters": [{"key": "keyword", "operator": "NOT IN", "values": [""]}],
         "note": "old SEARCH_QUERY_RR_DISPLAY_AD_UNIT_REPORT"},
        {"name": "ALL_ATTRIBUTES",
         "attributes": None, "filters": [],
         "note": "worst case -- every dimension at once; not a real call, a ceiling"},
    ],
}

METRIC_KEYS = ["requests", "responses", "response_rate"]


def fetch_body(report_type, agency, window, attributes, metrics, filters,
               use_external):
    """Build a KAM request body.

    NOTE the asymmetry between the two endpoints, learned the hard way:
      /report/fetch  accepts the EXTERNAL reportType with useExternalNames:true
      /report/query  (the resolver) only knows INTERNAL reportTypes -- passing the
                     external name returns 500 "report type '...' is not configured
                     yet". Matches scripts/build_query_csv.py:85.
    """
    body = {"application": APP, "agencyId": agency, "reportType": report_type,
            "requestType": "REPORTING",
            "attributes": attributes, "metrics": metrics,
            "dateRanges": [{"startDate": window[0], "endDate": window[1]}],
            "filters": filters, "limit": 1000, "offset": 0}
    if use_external:
        body["useExternalNames"] = True
    return body


def resolve_sql(session, body):
    """POST /report/query -> the SQL BigQuery would run. No execution."""
    r = session.post(f"{BASE}/kamService/report/query",
                     data=json.dumps(body), headers=H, timeout=120)
    if r.status_code != 200:
        return None, f"HTTP {r.status_code}: {r.text[:200]}"
    sql = (r.json() or {}).get("reportQuery")
    return (sql, None) if sql else (None, "empty reportQuery")


def time_fetch(session, body):
    """Tier 0: wall-clock of a real fetch. Includes all KAM-side overhead."""
    t0 = time.perf_counter()
    r = session.post(f"{BASE}/kamService/report/fetch",
                     data=json.dumps(body), headers=H, timeout=600)
    elapsed_ms = (time.perf_counter() - t0) * 1000
    rows = len((r.json() or {}).get("data", [])) if r.status_code == 200 else None
    return {"wall_ms": round(elapsed_ms, 1), "http": r.status_code, "rows": rows,
            "error": None if r.status_code == 200 else r.text[:200]}


def build_bq_client(a):
    """Return a raw google.cloud.bigquery.Client.

    --creds hades mirrors ETL_pipeline/pipeline.py:get_bigquery_client -- Hades hands
    back a service-account context for an app_key, which BigQueryServiceClient turns
    into a real bigquery.Client. We reach through to `.big_query_client` because the
    wrapper's fetch_query() returns only rows and DISCARDS the QueryJob -- and the job
    is the only place bytes/slot_ms live.
    """
    if a.creds == "hades":
        from osSvcClient4pyV2.hades_svc_client import HadesSvcClient
        from osClient4pyV2.big_query_client import BigQueryServiceClient
        hades = HadesSvcClient(a.hades_application, env_domain=a.hades_env)
        context = hades.get_app_context_by_app_key(a.hades_app_key)
        if not context:
            raise RuntimeError(f"Hades returned no context for app_key={a.hades_app_key}")
        return BigQueryServiceClient(big_query_cred_context=context).big_query_client
    from google.cloud import bigquery
    return bigquery.Client(project=a.project) if a.project else bigquery.Client()


def bq_dry_run(client, sql):
    """Tier 1: bytes that would be scanned + referenced tables. Free, no execution."""
    from google.cloud import bigquery
    cfg = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
    job = client.query(sql, job_config=cfg)
    return {
        "total_bytes_processed": job.total_bytes_processed,
        "gb_processed": round((job.total_bytes_processed or 0) / 1024 ** 3, 3),
        "referenced_tables": ";".join(
            f"{t.dataset_id}.{t.table_id}" for t in (job.referenced_tables or [])),
        "statement_type": job.statement_type,
    }


def bq_execute(client, sql):
    """Tier 2: real job stats -- slot time is only available after execution."""
    from google.cloud import bigquery
    cfg = bigquery.QueryJobConfig(use_query_cache=False)
    job = client.query(sql, job_config=cfg)
    # total_rows off the RowIterator -- do NOT iterate. The RR_DISPLAY template has no
    # __LIMIT__ placeholder, so the resolved SQL is unbounded; iterating the keyword
    # grain would stream every row back over the wire.
    rows = job.result().total_rows
    stages = job.query_plan or []
    bytes_proc = job.total_bytes_processed or 0
    slot_ms = job.slot_millis or 0
    elapsed_ms = ((job.ended - job.started).total_seconds() * 1000
                  if job.ended and job.started else None)
    return {
        "job_id": job.job_id,
        "rows": rows,
        "total_bytes_processed": bytes_proc,
        "gb_processed": round(bytes_proc / 1024 ** 3, 3),
        "total_bytes_billed": job.total_bytes_billed,
        "cache_hit": job.cache_hit,
        "slot_ms": slot_ms,
        "elapsed_ms": round(elapsed_ms, 1) if elapsed_ms else None,
        "slot_ms_per_gb": (round(slot_ms / (bytes_proc / 1024 ** 3), 1)
                           if bytes_proc else None),
        "avg_parallelism": (round(slot_ms / elapsed_ms, 1)
                            if elapsed_ms else None),
        "stages": len(stages),
        "shuffle_output_bytes": sum((s.shuffle_output_bytes or 0) for s in stages),
        "records_read": sum((s.records_read or 0) for s in stages),
        "records_written": sum((s.records_written or 0) for s in stages),
        "slowest_stage": max(
            ((s.name, s.slot_ms or 0) for s in stages),
            key=lambda x: x[1], default=("", 0))[0],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, help="path to the KAM report config JSON")
    ap.add_argument("--agency", type=int, default=105)
    ap.add_argument("--current", nargs=2, metavar=("START", "END"),
                    default=["2026-07-19", "2026-07-21"])
    ap.add_argument("--mode", choices=["latency", "dryrun", "execute"], default="dryrun")
    ap.add_argument("--grain", action="append", default=None,
                    help="Only these grains by name (repeatable). Default: all.")
    ap.add_argument("--sql-file", default=None,
                    help="Profile this SQL directly and skip the KAM resolver.")
    ap.add_argument("--project", default=None, help="BQ billing project")
    ap.add_argument("--creds", choices=["adc", "hades"], default="hades",
                    help="Where the BQ credential comes from. 'hades' pulls a service "
                         "account from the internal Hades app-context service (needs "
                         "network access to osint.onlinesales.ai). 'adc' uses local ADC.")
    ap.add_argument("--hades-app-key", default="DATA_VALIDATION_FRAMEWORK_BQ_REPORTING_CREDS",
                    help="Hades application_key holding the BQ service account.")
    ap.add_argument("--hades-application", default="irisTestApplication")
    ap.add_argument("--hades-env", default="prod", choices=["test", "prod"])
    ap.add_argument("--outdir", default=os.path.join(HERE, "out"))
    a = ap.parse_args()

    cfg = json.load(open(a.config))
    rt, ext_rt = cfg["reportType"], cfg["externalReportType"]
    all_attrs = list((cfg.get("attributes") or {}).keys())

    grains = GRAINS.get(rt)
    if not grains:
        print(f"! no GRAINS entry for {rt}; profiling ALL_ATTRIBUTES only", file=sys.stderr)
        grains = [{"name": "ALL_ATTRIBUTES", "attributes": None, "filters": [], "note": ""}]
    if a.grain:
        grains = [g for g in grains if g["name"] in a.grain]
        if not grains:
            sys.exit(f"no grain matched {a.grain}")

    client = None
    if a.mode in ("dryrun", "execute"):
        try:
            client = build_bq_client(a)
        except Exception as e:
            sys.exit(f"BigQuery client unavailable ({type(e).__name__}: {e}).\n"
                     "--creds hades needs network access to osint.onlinesales.ai and the "
                     "osClient4pyV2 / osSvcClient4pyV2 libs on the path (run with the "
                     "ETL_pipeline venv python).\n--creds adc needs "
                     "GOOGLE_APPLICATION_CREDENTIALS or a local ADC file.\n"
                     "Or use --mode latency, which needs no BQ credential at all.")

    session = None
    if not a.sql_file:
        import requests
        session = requests.Session()
        session.trust_env = False

    preset_sql = open(a.sql_file).read() if a.sql_file else None
    rows = []
    for g in grains:
        attrs = g["attributes"] if g["attributes"] is not None else all_attrs
        rec = {"report_type": rt, "grain": g["name"], "attributes": ",".join(attrs),
               "n_attributes": len(attrs), "note": g.get("note", ""),
               "date_start": a.current[0], "date_end": a.current[1], "mode": a.mode}
        # latency profiles the real fetch (external names); dryrun/execute go through
        # the resolver, which is internal-only.
        use_external = (a.mode == "latency")
        body = fetch_body(ext_rt if use_external else rt, a.agency, a.current,
                          attrs, METRIC_KEYS, g["filters"], use_external)

        try:
            if a.mode == "latency":
                rec.update(time_fetch(session, body))
            else:
                sql = preset_sql
                if sql is None:
                    sql, err = resolve_sql(session, body)
                    if err:
                        rec["error"] = f"resolver: {err}"
                        rows.append(rec)
                        continue
                rec["sql_chars"] = len(sql)
                rec.update(bq_dry_run(client, sql) if a.mode == "dryrun"
                           else bq_execute(client, sql))
        except Exception as e:
            rec["error"] = f"{type(e).__name__}: {e}"[:300]

        rows.append(rec)
        print(f"  {g['name']:<18} " + "  ".join(
            f"{k}={v}" for k, v in rec.items()
            if k in ("gb_processed", "slot_ms", "elapsed_ms", "wall_ms", "rows",
                     "cache_hit", "error") and v is not None))

    os.makedirs(a.outdir, exist_ok=True)
    out = os.path.join(a.outdir, f"query_cost_{rt}.csv")
    cols = []
    for r in rows:
        for k in r:
            if k not in cols:
                cols.append(k)
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {os.path.relpath(out, os.path.dirname(HERE))}  "
          f"({len(rows)} grains, {len(cols)} metrics)")


if __name__ == "__main__":
    main()
