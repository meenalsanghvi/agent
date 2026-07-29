"""
Derived-metric layer
=====================
The Python math the agent computes on raw KAM aggregates. Lifted verbatim from
`weekly_analysis_agent/utils/helpers.py` (generic helpers) plus the ROAS combine
logic from `roi_analysis_tools.py`. This is the "math stays in Python" decision:
KAM returns raw aggregates; these functions produce deltas, contribution %, CVRs,
verdicts, and Pareto lists.

Comparison mode: KAM does NOT emit comparison variants — each report is single-period.
The tools fetch current and baseline as separate KAM calls and pass both row dicts to
the combine_* functions (mirroring the legacy roi_analysis_tools two-`_overall` design).
"""
import math
from datetime import date as _date, datetime as _datetime
from decimal import Decimal


# ── generic helpers (verbatim from utils/helpers.py) ─────────────────────

def pct_change(cur, base):
    """% change of cur vs base; None when base ~0 (undefined)."""
    if base is None or abs(base) < 1e-9:
        return None
    return round((cur - base) / base * 100.0, 2)


def contribution_pct(delta, total_delta):
    """Signed share of the marketplace-level change this entity's delta represents."""
    if total_delta is None or abs(total_delta) < 1e-9:
        return None
    return round(delta / total_delta * 100.0, 2)


def share_pct(value, total):
    """Entity value as % of marketplace total for the period; None when total ~0."""
    if total is None or abs(total) < 1e-9:
        return None
    return round(value / total * 100.0, 2)


def cvr(orders, views):
    """Conversion rate = orders / viewproducts * 100; 0 when no views."""
    if views is None or views <= 0:
        return 0.0
    return round(orders * 100.0 / views, 2)


def roi_ratio(gmv, spend):
    """ROI/ROAS = GMV / spend; 0 when no spend."""
    if spend is None or spend <= 0:
        return 0.0
    return round(gmv / spend, 2)


def cpc_ratio(spend, clicks):
    if clicks is None or clicks <= 0:
        return 0.0
    return round(spend / clicks, 4)


def ctr_ratio(clicks, impressions):
    if impressions is None or impressions <= 0:
        return 0.0
    return round(clicks * 100.0 / impressions, 2)


def ir_ratio(impressions, responses):
    if responses is None or responses <= 0:
        return 0.0
    return round(impressions / responses, 4)


def pareto_high_impact(records, threshold=0.8):
    """Pareto 'vital few': active_both records ranked by current spend desc, returning
    the smallest set whose cumulative current spend reaches `threshold` of the total."""
    def _spend(r):
        return float((r.get("current") or {}).get("spend", 0) or 0)
    ab = sorted([r for r in records if r.get("status") == "active_both"], key=_spend, reverse=True)
    total = sum(_spend(r) for r in ab)
    out, cum = [], 0.0
    for r in ab:
        cum += _spend(r)
        out.append({**r, "cumulative_spend_share_pct": round(cum * 100.0 / total, 2) if total > 0 else 0})
        if total > 0 and cum >= threshold * total:
            break
    return out


def sanitize_output(obj):
    """Coerce a dict/list structure into JSON-serializable values (NaN/Decimal/dates/numpy)."""
    if isinstance(obj, dict):
        return {k: sanitize_output(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_output(v) for v in obj]
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    if isinstance(obj, Decimal):
        f = float(obj)
        return None if (math.isnan(f) or math.isinf(f)) else f
    if isinstance(obj, (_datetime, _date)):
        return obj.isoformat()
    if hasattr(obj, "item") and not isinstance(obj, (str, bytes)):
        try:
            return sanitize_output(obj.item())
        except (ValueError, TypeError):
            return obj
    return obj


# ── ROAS: combine program + site funnels (from roi_analysis_tools) ───────

def _trend_verdict(prog_cvr_cur, prog_cvr_base, site_cvr_cur, site_cvr_base, tol_pp=10.0):
    """Program attributed-CVR trend vs organic site-CVR trend → is the ROAS drop
    ours or market-wide?"""
    prog_chg = pct_change(prog_cvr_cur, prog_cvr_base)
    org_chg = pct_change(site_cvr_cur, site_cvr_base)
    verdict, interp = "inconclusive", None
    if prog_chg is not None and org_chg is not None:
        if prog_chg >= -2:
            verdict = "program_cvr_stable"
            interp = "Program conversion held — if ROAS still fell, look at spend/reach or GMV-per-order, not conversion."
        elif org_chg < 0 and abs(prog_chg - org_chg) <= tol_pp:
            verdict = "market_wide_user_decline"
            interp = "Program and organic conversion fell together — marketplace-wide user/demand decline, not ad serving."
        else:
            verdict = "ad_system_issue"
            interp = "Program conversion fell faster than organic — ad-system-specific decline. Drill into merchants/SKUs."
    return {
        "program_attributed_cvr": {"current": prog_cvr_cur, "baseline": prog_cvr_base, "change_pct": prog_chg},
        "organic_site_cvr": {"current": site_cvr_cur, "baseline": site_cvr_base, "change_pct": org_chg},
        "gap_pp": round(prog_chg - org_chg, 2) if (prog_chg is not None and org_chg is not None) else None,
        "verdict": verdict,
        "interpretation": interp,
    }


def _intent_diagnostic(spend_chg, views_chg, gmv_chg, cvr_cur, cvr_base, tol=15.0):
    """Spend flat + program views flat + program GMV down + attributed CVR down ⇒
    ROAS drop is a purchase-intent (conversion) decline, not reach/bidding."""
    spend_flat = spend_chg is not None and abs(spend_chg) <= tol
    views_flat = views_chg is not None and abs(views_chg) <= tol
    cvr_dropped = cvr_base > 0 and cvr_cur < cvr_base
    gmv_declined = gmv_chg is not None and gmv_chg < 0
    triggered = bool(spend_flat and views_flat and cvr_dropped and gmv_declined)
    return {
        "user_intent_decline_suspected": triggered,
        "spend_flat": spend_flat,
        "viewproducts_flat": views_flat,
        "attributed_cvr_dropped": cvr_dropped,
        "program_gmv_declined": gmv_declined,
        "interpretation": (
            "Spend and product views held steady but conversion/GMV fell — ROAS drop is "
            "driven by lower user purchase intent, not reach or bidding."
        ) if triggered else None,
    }


def _num(d: dict, key: str) -> float:
    try:
        return float((d or {}).get(key) or 0)
    except (TypeError, ValueError):
        return 0.0


def _gmv_period(prog: dict, site: dict) -> dict:
    spend = _num(prog, "spend"); gmv = _num(prog, "program_gmv")
    orders = _num(prog, "program_orders"); views = _num(prog, "program_viewproducts")
    a2c = _num(prog, "program_add2carts")
    srev = _num(site, "site_revenue"); sorders = _num(site, "site_orders")
    sviews = _num(site, "site_viewproducts"); sa2c = _num(site, "site_add2carts")
    return {
        "spend": round(spend, 2), "program_gmv": round(gmv, 2),
        "program_orders": orders, "program_viewproducts": views, "program_add2carts": a2c,
        "site_revenue": round(srev, 2), "site_orders": sorders,
        "site_viewproducts": sviews, "site_add2carts": sa2c,
        "actual_roi": roi_ratio(gmv, spend),
        "attributed_cvr": cvr(orders, views),
        "site_cvr": cvr(sorders, sviews),
        "organic_gmv": round(srev - gmv, 2),
        "organic_orders": sorders - orders,
    }


def combine_gmv_attribution(program_current: dict, program_baseline: dict,
                            site_current: dict, site_baseline: dict,
                            program_label: str = "All Programs") -> dict:
    """Combine the program funnel (cvcpf per-click-timestamp) + site funnel (mmf) into
    the check_gmv_attribution result: PROGRAM vs SITE funnels, CVRs, trend_verdict,
    user_intent_diagnostic. Each arg is a single-period row dict (metrics-layer keys) —
    the tool fetches current + baseline as SEPARATE KAM calls (KAM does not auto-emit
    comparison variants). Reproduces roi_analysis_tools.check_gmv_attribution.
    """
    current = _gmv_period(program_current, site_current)
    baseline = _gmv_period(program_baseline, site_baseline)

    verdict = _trend_verdict(
        current["attributed_cvr"], baseline["attributed_cvr"],
        current["site_cvr"], baseline["site_cvr"],
    )
    intent = _intent_diagnostic(
        pct_change(current["spend"], baseline["spend"]),
        pct_change(current["program_viewproducts"], baseline["program_viewproducts"]),
        pct_change(current["program_gmv"], baseline["program_gmv"]),
        current["attributed_cvr"], baseline["attributed_cvr"],
    )
    change = {
        "spend_change_pct": pct_change(current["spend"], baseline["spend"]),
        "program_gmv_change_pct": pct_change(current["program_gmv"], baseline["program_gmv"]),
        "program_orders_change_pct": pct_change(current["program_orders"], baseline["program_orders"]),
        "site_revenue_change_pct": pct_change(current["site_revenue"], baseline["site_revenue"]),
        "site_orders_change_pct": pct_change(current["site_orders"], baseline["site_orders"]),
    }
    return {
        "program_analyzed": program_label,
        "current": current,
        "baseline": baseline,
        "change": change,
        "trend_verdict": verdict,
        "user_intent_diagnostic": intent,
    }


# ── CTR: marketplace overall (check_ctr_overall) ─────────────────────────

def combine_ctr_overall(current_row: dict, baseline_row: dict) -> dict:
    """Marketplace-level CTR decomposition. `current_row`/`baseline_row` are single-period
    row dicts (metrics-layer keys) from two separate KAM fetches. Reproduces
    check_ctr_overall: clicks/impressions/CTR/spend for both periods + the
    clicks-vs-impressions decomposition the CTR SOP needs. Pass an empty baseline_row
    for a single-period (no-comparison) request."""
    def _period(d):
        cl = _num(d, "clicks"); im = _num(d, "impressions"); sp = _num(d, "spend")
        return {"clicks": cl, "impressions": im, "spend": round(sp, 2), "ctr": ctr_ratio(cl, im)}

    current = _period(current_row)
    baseline = _period(baseline_row)
    return {
        "current": current,
        "baseline": baseline,
        "change": {
            "ctr_change_pct": pct_change(current["ctr"], baseline["ctr"]),
            "clicks_change_pct": pct_change(current["clicks"], baseline["clicks"]),
            "impressions_change_pct": pct_change(current["impressions"], baseline["impressions"]),
            "spend_change_pct": pct_change(current["spend"], baseline["spend"]),
        },
    }
