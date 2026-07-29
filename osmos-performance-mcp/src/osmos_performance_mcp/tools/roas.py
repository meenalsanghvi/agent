"""
ROAS tools
==========
Backs the debug-roas skill. `check_gmv_attribution` is fully wired (the validated
two-report split + Python combine); the remaining ROAS tools are registered with
the same pattern and raise a clear "config pending" error until their KAM_AGENT_*
configs are authored + validated.
"""
import logging
from typing import Annotated, Optional

from fastmcp import Context
from fastmcp.exceptions import ToolError
from pydantic import Field

from .. import report_map
from ..config.settings import settings
from .. import metrics
from .context import get_kam_client, read_row
from .decorators import rate_limit

logger = logging.getLogger(__name__)

_PROGRAM_LABEL = {"pla": "PLA (Product Ads)", "display": "Display Ads"}


def register_roas_tools(mcp):
    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def check_gmv_attribution(
        agency_id: Annotated[int, Field(description="Marketplace agency ID.")],
        start_date: Annotated[str, Field(description="Current period start YYYY-MM-DD.")],
        end_date: Annotated[str, Field(description="Current period end YYYY-MM-DD.")],
        program_type: Annotated[Optional[str], Field(description='"pla", "display", or null/"all".')] = None,
        baseline_start_date: Annotated[Optional[str], Field(description="Baseline start YYYY-MM-DD (enables comparison).")] = None,
        baseline_end_date: Annotated[Optional[str], Field(description="Baseline end YYYY-MM-DD.")] = None,
        ctx: Context = None,
    ) -> dict:
        """STEP 1 of the ROAS SOP: marketplace-level PROGRAM (ad-attributed) vs SITE
        (organic) funnel, comparison mode. Returns raw funnels + attributed/site CVRs,
        a trend_verdict (market-wide decline vs ad-system issue), and a
        user_intent_diagnostic. Pass baseline dates for the verdict.
        """
        spec = report_map.CHECK_GMV_ATTRIBUTION
        program_km = report_map.program_key_map(spec, program_type)
        site_km = spec["site_metrics"]
        kam = get_kam_client(ctx)

        def _fetch(report, km, sd, ed):
            # single-period fetch — KAM does not emit comparison variants; call once per window
            rows = kam.fetch_agent_report(report, agency_id, [{"startDate": sd, "endDate": ed}], metrics=list(km.values()))
            return read_row(rows[0] if rows else {}, km)

        has_baseline = bool(baseline_start_date and baseline_end_date)
        try:
            program_current = _fetch(spec["program_report"], program_km, start_date, end_date)
            site_current = _fetch(spec["site_report"], site_km, start_date, end_date)
            if has_baseline:
                program_baseline = _fetch(spec["program_report"], program_km, baseline_start_date, baseline_end_date)
                site_baseline = _fetch(spec["site_report"], site_km, baseline_start_date, baseline_end_date)
            else:
                program_baseline, site_baseline = {}, {}
        except Exception as e:
            logger.error(f"check_gmv_attribution KAM fetch failed: {e}")
            raise ToolError("Failed to fetch GMV-attribution data from KAM. Try again later.")

        result = metrics.combine_gmv_attribution(
            program_current, program_baseline, site_current, site_baseline,
            program_label=_PROGRAM_LABEL.get((program_type or "").lower(), "All Programs"))
        result["period"] = {"start_date": start_date, "end_date": end_date}
        if has_baseline:
            result["baseline_period"] = {"start_date": baseline_start_date, "end_date": baseline_end_date}
        return metrics.sanitize_output(result)

    # ── remaining ROAS tools — same pattern, pending KAM config validation ──

    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def get_merchant_breakdown(agency_id: int, start_date: str, end_date: str,
                                     program_type: Optional[str] = None,
                                     baseline_start_date: Optional[str] = None,
                                     baseline_end_date: Optional[str] = None, ctx: Context = None) -> dict:
        """ROAS STEP 3: merchant-level contribution to the program GMV change."""
        raise ToolError("get_merchant_breakdown: KAM config (KAM_AGENT_ROAS_MERCHANT_BREAKDOWN) pending validation.")

    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def get_daily_order_trends(agency_id: int, start_date: str, end_date: str,
                                     program_type: Optional[str] = None, ctx: Context = None) -> dict:
        """ROAS drill: daily PROGRAM vs SITE funnel."""
        raise ToolError("get_daily_order_trends: KAM config (KAM_AGENT_ROAS_DAILY_ORDER_TRENDS) pending validation.")

    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def get_sku_level_performance(agency_id: int, client_ids: list[str], start_date: str, end_date: str,
                                        baseline_start_date: Optional[str] = None,
                                        baseline_end_date: Optional[str] = None, ctx: Context = None) -> dict:
        """ROAS STEP 4 (PLA only): per-SKU contribution for the problem merchants."""
        raise ToolError("get_sku_level_performance: KAM config (KAM_AGENT_ROAS_SKU_PERFORMANCE) pending validation.")

    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def get_target_roi(agency_id: int, ctx: Context = None) -> dict:
        """The marketplace target ROI benchmark."""
        raise ToolError("get_target_roi: KAM config (KAM_AGENT_ROAS_TARGET_ROI) pending validation.")
