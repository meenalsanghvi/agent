"""CTR tools — backs the debug-ctr skill.
check_ctr_overall is WIRED (existing MonetizeMerchantFacts classes, no kamService change);
the rest are pending their KAM_AGENT_CTR_* configs."""
import logging
from typing import Annotated, Optional

from fastmcp import Context
from fastmcp.exceptions import ToolError
from pydantic import Field

from .. import report_map, metrics
from ..config.settings import settings
from .context import get_kam_client, read_row
from .decorators import rate_limit

logger = logging.getLogger(__name__)

_PENDING = "KAM config pending validation — implement like tools/roas.check_gmv_attribution."


def register_ctr_tools(mcp):
    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def check_ctr_overall(
        agency_id: Annotated[int, Field(description="Marketplace agency ID.")],
        start_date: Annotated[str, Field(description="Current period start YYYY-MM-DD.")],
        end_date: Annotated[str, Field(description="Current period end YYYY-MM-DD.")],
        program_type: Annotated[Optional[str], Field(description='"pla", "display", or null/"all".')] = None,
        baseline_start_date: Annotated[Optional[str], Field(description="Baseline start YYYY-MM-DD.")] = None,
        baseline_end_date: Annotated[Optional[str], Field(description="Baseline end YYYY-MM-DD.")] = None,
        ctx: Context = None,
    ) -> dict:
        """CTR STEP 1: marketplace-level ad clicks / impressions / CTR / spend, comparison
        mode. Returns the clicks-vs-impressions decomposition for scenario triage."""
        spec = report_map.CHECK_CTR_OVERALL
        km = spec["metrics"]
        kam = get_kam_client(ctx)

        def _fetch(sd, ed):
            # single-period fetch — KAM does not emit comparison variants, so we call once per window
            rows = kam.fetch_agent_report(
                spec["report"], agency_id, [{"startDate": sd, "endDate": ed}], metrics=list(km.values()))
            return read_row(rows[0] if rows else {}, km)

        try:
            current = _fetch(start_date, end_date)
            baseline = _fetch(baseline_start_date, baseline_end_date) if (baseline_start_date and baseline_end_date) else {}
        except Exception as e:
            logger.error(f"check_ctr_overall KAM fetch failed: {e}")
            raise ToolError("Failed to fetch CTR data from KAM. Try again later.")

        result = metrics.combine_ctr_overall(current, baseline)
        result["period"] = {"start_date": start_date, "end_date": end_date}
        if baseline_start_date and baseline_end_date:
            result["baseline_period"] = {"start_date": baseline_start_date, "end_date": baseline_end_date}
        return metrics.sanitize_output(result)

    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def get_merchant_ctr_breakdown(agency_id: int, start_date: str, end_date: str,
                                         program_type: Optional[str] = None,
                                         baseline_start_date: Optional[str] = None,
                                         baseline_end_date: Optional[str] = None, ctx: Context = None) -> dict:
        """CTR STEP 4: merchant CTR contribution + Pareto high-impact spenders."""
        raise ToolError(f"get_merchant_ctr_breakdown: {_PENDING}")

    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def get_sku_level_ctr_performance(agency_id: int, client_ids: list[str], start_date: str, end_date: str,
                                            baseline_start_date: Optional[str] = None,
                                            baseline_end_date: Optional[str] = None, ctx: Context = None) -> dict:
        """CTR SKU drill (PLA): SKU contribution to the impressions change + ctr change."""
        raise ToolError(f"get_sku_level_ctr_performance: {_PENDING}")

    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def get_keyword_seller_breakdown(agency_id: int, search_queries: list[str], start_date: str, end_date: str,
                                           baseline_start_date: Optional[str] = None,
                                           baseline_end_date: Optional[str] = None, ctx: Context = None) -> dict:
        """CTR keyword drill (PLA): per-keyword per-seller CTR; new low-CTR sellers."""
        raise ToolError(f"get_keyword_seller_breakdown: {_PENDING}")
