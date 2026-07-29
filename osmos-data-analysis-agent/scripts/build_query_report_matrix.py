"""Build a query_title / sql_query / kam_report matrix.

Joins `query_inventory/**/*.sql` (the extracted legacy SQL) against
`kam_report_configs/**/*.json` (the authored KAM report configs).

Join direction is JSON -> SQL: every authored reportType claims the source queries
it implements. Most claim exactly one, which naturally handles the PLA/DISPLAY
splits where one SQL file backs two reportTypes. The consolidated reports claim
several -- see MERGED below. SQL files that no report claims are emitted with an
empty kam_report cell rather than a guess.

Matching is token-overlap within the same skill directory, after expanding the
abbreviations the config names use (RR -> response_rate, KW -> keyword, ...).
Anything the scorer is not confident about is listed in the OVERRIDES table; the
merged reports bypass the scorer entirely via MERGED, because they claim queries
from other skill directories that name matching would never reach.

`kam_report_configs/_retired/` is skipped: those configs were superseded by the
merges and their queries are claimed by the merged report instead.

Usage:
    python3 scripts/build_query_report_matrix.py [--outdir DIR]
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
QUERY_DIR = REPO / "query_inventory"
CONFIG_DIR = REPO / "kam_report_configs"

# Config names abbreviate; SQL filenames spell things out. Fold both sides onto
# ONE canonical spelling so a shared concept contributes a single token.
#
# Expanding instead of folding (rr -> {response, rate, rates}) is wrong: it hands
# every RR config three free tokens of overlap with every RR query, which drowns
# out the one token that actually discriminates (category / filter_presence).
# Applied longest-phrase-first against the underscore-joined name.
CANONICAL = [
    ("response_rates", "rr"),
    ("response_rate", "rr"),
    ("keywords", "kw"),
    ("keyword", "kw"),
    ("performance", "perf"),
    ("aggregated", "agg"),
]

# Tokens too common within a skill directory to carry signal.
NOISE = {"internal", "perf", "get", "check", "fetch", "data", "breakdown"}

# Merged reports claim MANY source queries, and often from other skill directories
# than their own -- so name matching cannot find them and the 1:1 assumption does not
# hold. Each entry is the explicit `absorbs` list of a merge spec in
# scripts/merge_wave{1,2,3}.py, expressed as "<skill>/<sql stem>".
# See kam_report_configs/MERGE_ANALYSIS.md.
MERGED = {
    "INTERNAL_PERF_RR_DISPLAY": [
        "rr/get_response_rate_by_dimension",
        "rr/check_display_page_type_rr",
        "rr/check_display_hourly_rr__hourly",
        "rr/check_display_hourly_rr__ad_unit",
        "rr/get_search_query_response_rates__display",
        "rr/get_search_query_response_rates__display_ad_unit",
    ],
    "INTERNAL_PERF_RR_PLA": [
        "rr/get_response_rate_by_dimension",
        "rr/get_category_response_rates",
        "rr/get_store_level_rr_buckets",
    ],
    "INTERNAL_PERF_SEARCH_QUERY_REQUESTS_PLA": [
        "rr/get_search_query_response_rates__pla",
        "rr/get_search_query_rr_buckets",
        "keyword_delivery/check_keyword_request_volume",
    ],
    "INTERNAL_PERF_PAGE_PERFORMANCE_PLA": [
        "shared/get_page_level_performance",
        "rr/check_response_rate_by_page",
        "bu/check_requests__pla",
    ],
    "INTERNAL_PERF_DISPLAY_AD_UNIT": [
        "bu/get_display_ad_unit_performance",
        "rr/check_response_rate_by_page",
        "bu/check_requests__display",
    ],
    "INTERNAL_PERF_MERCHANT_PERFORMANCE": [
        "roas/get_merchant_breakdown",
        "cpc/get_merchant_cpc_breakdown",
        "ctr/get_merchant_ctr_breakdown",
        "bu/get_merchant_bu_breakdown",
        "rr/get_merchant_rr_breakdown",
    ],
    "INTERNAL_PERF_SKU_PERFORMANCE": [
        "roas/get_sku_level_performance",
        "cpc/get_sku_level_cpc_performance",
        "ctr/get_sku_level_ctr_performance",
    ],
    "INTERNAL_PERF_GMV_ATTRIBUTION": [
        "roas/check_gmv_attribution",
        "bu/check_program_spend",
    ],
    "INTERNAL_PERF_CATEGORY_PERFORMANCE": [
        "shared/get_category_level_performance",
        "cpc/get_merchant_category_cpc_comparison",
    ],
    "INTERNAL_PERF_KEYWORD_PERFORMANCE": [
        "keyword_delivery/get_targeted_keyword_competition",
        "keyword_delivery/check_targeted_keyword_performance_in_campaigns",
        "shared/get_merchant_keyword_performance",
    ],
    "INTERNAL_PERF_SEARCH_QUERY_PERFORMANCE": [
        "shared/get_search_query_performance",
        "ctr/get_keyword_seller_breakdown",
    ],
    "INTERNAL_PERF_CAMPAIGN_PERFORMANCE": [
        "shared/get_campaign_performance__aggregated",
        "shared/get_campaign_performance__daily",
    ],
    "INTERNAL_PERF_AUDIT_EVENTS": [
        "shared/get_product_selection_changes",
        "shared/get_campaign_status_changes",
        "budget_pacing/check_budget_changes_on_date",
    ],
    "INTERNAL_PERF_CAMPAIGN_KEYWORDS": [
        "shared/get_campaign_targeted_keywords__targeted",
        "shared/get_campaign_targeted_keywords__negative",
    ],
    "INTERNAL_PERF_CAMPAIGN_NETWORKS": [
        "shared/get_campaign_targeted_networks__by_campaign_id",
        "shared/get_campaign_targeted_networks__via_ctd",
    ],
}

# reportType -> SQL stem, for the cases token overlap cannot resolve.
# Each entry is a deliberate reading of the config's `query` template against
# the candidate SQL bodies.
OVERRIDES = {
    "INTERNAL_PERF_MARKETPLACE_DIRECTORY": "fetch_marketplace_info__all",
    "INTERNAL_PERF_RR_HOURLY": "check_display_hourly_rr__hourly",
    "INTERNAL_PERF_RR_HOURLY_AD_UNIT": "check_display_hourly_rr__ad_unit",
    "INTERNAL_PERF_SEARCH_QUERY_RR_PLA": "get_search_query_response_rates__pla",
    "INTERNAL_PERF_SEARCH_QUERY_RR_DISPLAY": "get_search_query_response_rates__display",
    "INTERNAL_PERF_SEARCH_QUERY_RR_DISPLAY_AD_UNIT": "get_search_query_response_rates__display_ad_unit",
    "INTERNAL_PERF_SEARCH_QUERY_RR_BUCKETS": "get_search_query_rr_buckets",
    "INTERNAL_PERF_CAMPAIGN_DAILY_BUDGET_AVG": "get_campaign_daily_budget__avg_daily_budget",
    "INTERNAL_PERF_CAMPAIGN_DAILY_BUDGET_FLEXI": "get_campaign_daily_budget__flexi_budget",
    "INTERNAL_PERF_MINUTE_CPC": "get_minute_level_cpc_data",
    "INTERNAL_PERF_MINUTE_CPM": "get_minute_level_cpm_data",
    "INTERNAL_PERF_CAMPAIGN_KW_TARGETED": "get_campaign_targeted_keywords__targeted",
    "INTERNAL_PERF_CAMPAIGN_KW_NEGATIVE": "get_campaign_targeted_keywords__negative",
    "INTERNAL_PERF_CAMPAIGN_NETWORKS_BY_ID": "get_campaign_targeted_networks__by_campaign_id",
    "INTERNAL_PERF_CAMPAIGN_NETWORKS_VIA_CTD": "get_campaign_targeted_networks__via_ctd",
    "INTERNAL_PERF_SKU_ROAS": "get_sku_level_performance",
    "INTERNAL_PERF_MERCHANT_ROAS": "get_merchant_breakdown",
    "INTERNAL_PERF_TRUE_BU": "get_true_bu_campaign_data",
    "INTERNAL_PERF_WALLET_BALANCE": "get_merchant_wallet_balance",
    "INTERNAL_PERF_BUDGET_CHANGES": "check_budget_changes_on_date",
    "INTERNAL_PERF_KW_REQUEST_VOLUME": "check_keyword_request_volume",
    "INTERNAL_PERF_RESPONDED_SKUS": "get_responded_skus",
    "INTERNAL_PERF_PROGRAM_SPEND": "check_program_spend",
    "INTERNAL_PERF_CTR_OVERALL": "check_ctr_overall",
    "INTERNAL_PERF_CAMPAIGN_PERF_AGG": "get_campaign_performance__aggregated",
    "INTERNAL_PERF_CAMPAIGN_PERF_DAILY": "get_campaign_performance__daily",
    "INTERNAL_PERF_RR_BY_PAGE_PLA": "check_response_rate_by_page",
    "INTERNAL_PERF_RR_BY_PAGE_DISPLAY": "check_response_rate_by_page",
    "INTERNAL_PERF_RR_BY_DIMENSION_PLA": "get_response_rate_by_dimension",
    "INTERNAL_PERF_RR_BY_DIMENSION_DISPLAY": "get_response_rate_by_dimension",
    "INTERNAL_PERF_BU_REQUESTS_PLA": "check_requests__pla",
    "INTERNAL_PERF_BU_REQUESTS_DISPLAY": "check_requests__display",
    "INTERNAL_PERF_PRODUCT_SELECTION_CHANGES": "get_product_selection_changes",
}

HEADER_LINE = re.compile(r"^\s*--")
ID_FIELD = re.compile(r"^\s*--\s*id:\s*(\S+)", re.M)
DESC_FIELD = re.compile(r"^\s*--\s*description:\s*(.+?)\s*$", re.M)


def tokenize(name: str) -> set[str]:
    """Fold an identifier to its canonical lowercase token set."""
    text = re.sub(r"[^a-z0-9]+", "_", name.lower())
    for phrase, canon in CANONICAL:
        text = text.replace(phrase, canon)
    return {t for t in text.split("_") if t and t not in NOISE}


def parse_sql(path: Path) -> dict:
    """Split a query_inventory file into its header metadata and SQL body."""
    text = path.read_text()
    query_id = m.group(1) if (m := ID_FIELD.search(text)) else f"{path.parent.name}.{path.stem}"
    description = m.group(1).strip() if (m := DESC_FIELD.search(text)) else ""

    # Body = everything after the trailing `-- ===...` banner that closes the
    # header block. Fall back to dropping every leading comment line.
    lines = text.splitlines()
    banner_idxs = [i for i, ln in enumerate(lines) if re.match(r"^\s*--\s*={5,}", ln)]
    if len(banner_idxs) >= 2:
        body_lines = lines[banner_idxs[-1] + 1 :]
    else:
        body_lines = [ln for ln in lines if not HEADER_LINE.match(ln)]

    body = "\n".join(body_lines).strip("\n")
    # Strip the uniform leading indentation the extraction left behind.
    indents = [len(ln) - len(ln.lstrip()) for ln in body.splitlines() if ln.strip()]
    if indents and (pad := min(indents)):
        body = "\n".join(ln[pad:] if ln.strip() else ln for ln in body.splitlines())

    return {
        "skill": path.parent.name,
        "stem": path.stem,
        "query_id": query_id,
        "description": description,
        "sql": body.strip(),
        "path": str(path.relative_to(REPO)),
    }


def parse_config(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        print(f"  WARN: {path.relative_to(REPO)} is not valid JSON ({exc})", file=sys.stderr)
        return None
    rt = data.get("reportType")
    if not rt:
        return None
    # Re-serialise rather than passing the raw text through: uniform 2-space
    # indentation keeps the spreadsheet cells readable regardless of how each
    # config happened to be formatted on disk.
    return {
        "reportType": rt,
        "config": json.dumps(data, indent=2, ensure_ascii=False),
        "skill": path.parent.name,
        "path": str(path.relative_to(REPO)),
    }


def match(config: dict, queries: list[dict]) -> tuple[list[tuple[str, str]], str]:
    """Return ([(skill, sql_stem), ...], how) for a config, or ([], reason).

    A merged report claims several source queries, frequently from other skill
    directories, so the result is a list. Everything else claims exactly one.
    """
    if (absorbed := MERGED.get(config["reportType"])) is not None:
        known = {(q["skill"], q["stem"]) for q in queries}
        claims, missing = [], []
        for ref in absorbed:
            skill, _, stem = ref.partition("/")
            (claims if (skill, stem) in known else missing).append((skill, stem))
        if missing:
            return [], f"merged: source queries not found: {sorted(missing)}"
        return claims, f"merged ({len(claims)} queries)"

    if (forced := OVERRIDES.get(config["reportType"])) is not None:
        if any(q["stem"] == forced and q["skill"] == config["skill"] for q in queries):
            return [(config["skill"], forced)], "override"
        return [], f"override target {forced!r} missing in {config['skill']}/"

    pool = [q for q in queries if q["skill"] == config["skill"]]
    if not pool:
        return [], f"no SQL files in {config['skill']}/"

    ctoks = tokenize(config["reportType"])
    if not ctoks:
        return [], "config name yielded no tokens"

    # Jaccard, not overlap/len(config): it penalises EXTRA tokens on the query
    # side, so an exact `merchant_cpc` beats the superset
    # `merchant_category_cpc_comparison` instead of tying with it.
    ranked = []
    for q in pool:
        qtoks = tokenize(q["stem"])
        if not qtoks:
            continue
        union = ctoks | qtoks
        ranked.append((len(ctoks & qtoks) / len(union), q["stem"]))
    ranked.sort(reverse=True)

    if not ranked or ranked[0][0] < 0.5:
        best = ranked[0] if ranked else (0.0, "-")
        return [], f"no confident match (best={best[1]} jaccard={best[0]:.2f})"

    # An ambiguous top score means the names cannot decide it; demand an override
    # rather than silently picking whichever sorted first.
    if len(ranked) > 1 and ranked[1][0] == ranked[0][0]:
        return [], f"ambiguous tie between {ranked[0][1]!r} and {ranked[1][1]!r} (jaccard={ranked[0][0]:.2f}) — add an OVERRIDES entry"

    return [(config["skill"], ranked[0][1])], f"jaccard={ranked[0][0]:.2f}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default=str(REPO / "scripts" / "out"))
    args = ap.parse_args()

    sql_paths = sorted(QUERY_DIR.glob("*/*.sql"))
    cfg_paths = sorted(p for p in CONFIG_DIR.glob("*/*.json") if p.parent.name != "_retired")
    if not sql_paths or not cfg_paths:
        print("ERROR: expected query_inventory/*/*.sql and kam_report_configs/*/*.json", file=sys.stderr)
        return 1

    queries = [parse_sql(p) for p in sql_paths]
    configs = [c for p in cfg_paths if (c := parse_config(p))]

    # JSON -> SQL, so PLA/DISPLAY splits collapse onto their shared source query.
    reports_for: dict[tuple[str, str], list[dict]] = {}
    unmatched: list[tuple[str, str]] = []
    for cfg in configs:
        claims, how = match(cfg, queries)
        if not claims:
            unmatched.append((cfg["reportType"], how))
            continue
        for claim in claims:
            reports_for.setdefault(claim, []).append(cfg)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    rows = []
    for q in queries:
        matched = sorted(reports_for.get((q["skill"], q["stem"]), []), key=lambda c: c["reportType"])
        # A query backing two reports (the PLA/DISPLAY splits) gets both configs
        # in the cell, separated by a labelled banner so they stay tellable apart.
        config_cell = "\n\n".join(
            (f"/* ===== {c['reportType']} ===== */\n{c['config']}" if len(matched) > 1 else c["config"])
            for c in matched
        )
        rows.append({
            "query_title": q["query_id"],
            "sql_query": q["sql"],
            "kam_report_config": config_cell,
        })

    csv_path = outdir / "query_report_matrix.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(rows)

    xlsx_path = None
    try:
        import pandas as pd

        xlsx_path = outdir / "query_report_matrix.xlsx"
        pd.DataFrame(rows).to_excel(xlsx_path, index=False, sheet_name="query_report_matrix")
    except ImportError:
        print("  note: pandas/openpyxl absent — CSV only", file=sys.stderr)

    mapped = sum(1 for r in rows if r["kam_report_config"])
    print(f"SQL files:        {len(rows)}")
    print(f"Report configs:   {len(configs)}")
    print(f"Rows with report: {mapped}")
    print(f"Rows without:     {len(rows) - mapped}")
    print(f"Unmatched report configs: {len(unmatched)}")
    for rt, why in unmatched:
        print(f"   ! {rt}: {why}")
    print(f"\nwrote {csv_path.relative_to(REPO)}")
    if xlsx_path:
        print(f"wrote {xlsx_path.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
