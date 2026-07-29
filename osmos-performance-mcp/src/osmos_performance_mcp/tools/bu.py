"""BU tools — backs the debug-bu skill. Pending each KAM_AGENT_BU_* config.

Note the retention-limited underlying tables (get_category_request_volume,
get_filter_presence_response_rates: 15-day; quadrant: 7-day) — enforce the
data-retention gate here when implementing.
"""
from typing import Optional

from fastmcp import Context
from fastmcp.exceptions import ToolError

from ..config.settings import settings
from .decorators import rate_limit

_PENDING = "KAM config pending validation — implement like tools/roas.check_gmv_attribution."


def register_bu_tools(mcp):
    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def check_program_spend(agency_id: int, start_date: str, end_date: str,
                                  program_type: Optional[str] = None, ctx: Context = None) -> dict:
        """BU STEP 1: program spend vs budget."""
        raise ToolError(f"check_program_spend: {_PENDING}")

    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def check_requests(agency_id: int, start_date: str, end_date: str,
                             program_type: Optional[str] = None, ctx: Context = None) -> dict:
        """BU/RR STEP 1: overall request/response counts (shared with RR)."""
        raise ToolError(f"check_requests: {_PENDING}")

    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def get_true_bu_campaign_data(agency_id: int, start_date: str, end_date: str, ctx: Context = None) -> dict:
        """BU STEP 1: campaign budget/spend snapshot (paused, budget drops, wallet)."""
        raise ToolError(f"get_true_bu_campaign_data: {_PENDING}")

    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def get_merchant_bu_breakdown(agency_id: int, start_date: str, end_date: str,
                                        baseline_start_date: Optional[str] = None,
                                        baseline_end_date: Optional[str] = None, ctx: Context = None) -> dict:
        """BU: merchant contribution to the spend change (comparison mode)."""
        raise ToolError(f"get_merchant_bu_breakdown: {_PENDING}")

    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def get_response_rate_by_dimension(agency_id: int, start_date: str, end_date: str,
                                             group_by_column: Optional[str] = None,
                                             program_type: str = "pla", ctx: Context = None) -> dict:
        """BU/RR: RR grouped by a dimension. Call without group_by_column first for available columns."""
        raise ToolError(f"get_response_rate_by_dimension: {_PENDING}")
