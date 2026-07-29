"""Unit tests for the derived-metric layer (no network / internal deps).

KAM returns single-period rows (no comparison variants), so combine_* take separate
current + baseline row dicts — one per KAM fetch."""
from osmos_performance_mcp import metrics


def test_pct_change_and_ratios():
    assert metrics.pct_change(110, 100) == 10.0
    assert metrics.pct_change(5, 0) is None          # undefined vs ~0 base
    assert metrics.roi_ratio(200, 100) == 2.0
    assert metrics.roi_ratio(200, 0) == 0.0
    assert metrics.cvr(10, 100) == 10.0
    assert metrics.cvr(10, 0) == 0.0
    assert metrics.ctr_ratio(5, 100) == 5.0
    assert metrics.contribution_pct(50, 100) == 50.0
    assert metrics.contribution_pct(50, 0) is None


def test_sanitize_output_handles_nan_and_inf():
    out = metrics.sanitize_output({"a": float("nan"), "b": float("inf"), "c": 1.5, "d": [float("nan"), 2]})
    assert out == {"a": None, "b": None, "c": 1.5, "d": [None, 2]}


def test_combine_ctr_overall_decomposes():
    # clicks +5%, impressions +20% → CTR falls (impression dilution)
    current = {"clicks": 105, "impressions": 1200, "spend": 50}
    baseline = {"clicks": 100, "impressions": 1000, "spend": 48}
    r = metrics.combine_ctr_overall(current, baseline)
    assert r["current"]["ctr"] == round(105 / 1200 * 100, 2)
    assert r["baseline"]["ctr"] == 10.0
    assert r["change"]["impressions_change_pct"] == 20.0
    assert r["change"]["ctr_change_pct"] < 0


def test_combine_ctr_overall_single_period():
    r = metrics.combine_ctr_overall({"clicks": 100, "impressions": 1000, "spend": 10}, {})
    assert r["current"]["ctr"] == 10.0
    assert r["change"]["ctr_change_pct"] is None      # no baseline


def test_combine_gmv_attribution_verdict_and_shape():
    # program conversion holds, organic holds → program_cvr_stable
    prog_cur = {"spend": 1000, "program_gmv": 5000, "program_orders": 100,
                "program_viewproducts": 1000, "program_add2carts": 200}
    prog_base = dict(prog_cur)
    site_cur = {"site_revenue": 20000, "site_orders": 500, "site_viewproducts": 5000, "site_add2carts": 900}
    site_base = dict(site_cur)
    r = metrics.combine_gmv_attribution(prog_cur, prog_base, site_cur, site_base, "PLA (Product Ads)")
    assert r["program_analyzed"] == "PLA (Product Ads)"
    assert r["current"]["actual_roi"] == 5.0            # 5000 / 1000
    assert r["current"]["attributed_cvr"] == 10.0       # 100 / 1000
    assert r["current"]["site_cvr"] == 10.0             # 500 / 5000
    assert r["trend_verdict"]["verdict"] == "program_cvr_stable"


def test_combine_gmv_flags_user_intent_decline():
    # spend & views flat, program GMV + attributed CVR down → intent decline suspected
    prog_cur = {"spend": 1000, "program_gmv": 4000, "program_orders": 80,
                "program_viewproducts": 1000, "program_add2carts": 200}
    prog_base = {"spend": 1000, "program_gmv": 6000, "program_orders": 120,
                 "program_viewproducts": 1000, "program_add2carts": 200}
    site = {"site_revenue": 20000, "site_orders": 500, "site_viewproducts": 5000, "site_add2carts": 900}
    r = metrics.combine_gmv_attribution(prog_cur, prog_base, site, dict(site))
    assert r["user_intent_diagnostic"]["user_intent_decline_suspected"] is True
