"""
Report map
==========
The single place that names the KAM_AGENT_* reports each SOP tool fetches and the
metric keys to request per program_type. Keys on the LEFT are the "combine" names
the metrics layer expects; values on the RIGHT are the KAM class metric keys the
report exposes. The tool fetches the KAM keys, normalizes to combine keys
(`context.read_row`), then hands off to `metrics.*`. Reports are single-period; the
tool fetches current + baseline separately and combines.

Only ROAS `check_gmv_attribution` is fully mapped (its configs are the reference).
Add entries here as each KAM_AGENT_* config is authored + validated in
`osmos-data-analysis-agent/kam_report_configs/`.
"""

from __future__ import annotations

# ── ROAS: check_gmv_attribution (two-report split — see kam_report_configs/roas) ──
CHECK_GMV_ATTRIBUTION = {
    "program_report": "KAM_AGENT_ROAS_PROGRAM_FUNNEL",   # ClientVendorChannelPerformanceFacts (per-click-timestamp)
    "site_report": "KAM_AGENT_ROAS_SITE_FUNNEL",          # MonetizeMerchantFacts (site_*)
    "program_metrics": {
        "all": {
            "spend": "spend",
            "program_gmv": "program_per_click_timestamp_sales",
            "program_orders": "program_per_click_timestamp_conversions",
            "program_viewproducts": "program_per_click_timestamp_viewproduct",
            "program_add2carts": "program_per_click_timestamp_add_to_cart",
        },
        "pla": {
            "spend": "pla_spend",
            "program_gmv": "pla_program_per_click_timestamp_sales",
            "program_orders": "pla_program_per_click_timestamp_conversions",
            "program_viewproducts": "pla_program_per_click_timestamp_viewproduct",
            "program_add2carts": "pla_program_per_click_timestamp_add_to_cart",
        },
        "display": {
            "spend": "display_spend",
            "program_gmv": "display_program_per_click_timestamp_sales",
            "program_orders": "display_program_per_click_timestamp_conversions",
            "program_viewproducts": "display_program_per_click_timestamp_viewproduct",
            "program_add2carts": "display_program_per_click_timestamp_add_to_cart",
        },
    },
    "site_metrics": {
        "site_revenue": "site_revenue",
        "site_orders": "site_orders",
        "site_viewproducts": "site_viewproducts",
        "site_add2carts": "site_add2carts",
    },
}


def program_key_map(spec: dict, program_type: str | None) -> dict:
    """Pick the program metric key-map for a program_type (default 'all')."""
    pt = (program_type or "all").lower()
    return spec["program_metrics"].get(pt, spec["program_metrics"]["all"])


# ── CTR: check_ctr_overall (single report, existing MonetizeMerchantFacts classes) ──
# Buildable today with NO kamService change — clicks/impressions/ctr/spend are base
# metrics inherited by MonetizeMerchantFacts.
CHECK_CTR_OVERALL = {
    "report": "KAM_AGENT_CTR_OVERALL",
    "metrics": {
        "clicks": "clicks",
        "impressions": "impressions",
        "ctr": "ctr",
        "spend": "spend",
    },
}
