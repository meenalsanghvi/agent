"""RR tools — backs the debug-rr skill. Pending each KAM_AGENT_RR_* config."""
from typing import Optional

from fastmcp import Context
from fastmcp.exceptions import ToolError

from ..config.settings import settings
from .decorators import rate_limit

_PENDING = "KAM config pending validation — implement like tools/roas.check_gmv_attribution."


def register_rr_tools(mcp):
    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def check_response_rate_by_page(agency_id: int, start_date: str, end_date: str,
                                          program_type: Optional[str] = None, ctx: Context = None) -> dict:
        """RR STEP 1: RR by page type (search_page_affected / non_search_pages_affected)."""
        raise ToolError(f"check_response_rate_by_page: {_PENDING}")

    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def get_category_response_rates(agency_id: int, start_date: str, end_date: str,
                                          category_l1_filter: Optional[str] = None,
                                          category_l2_filter: Optional[str] = None,
                                          category_l3_filter: Optional[str] = None, ctx: Context = None) -> dict:
        """RR non-search drill: category-level RR."""
        raise ToolError(f"get_category_response_rates: {_PENDING}")

    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def get_search_query_response_rates(agency_id: int, start_date: str, end_date: str,
                                              keywords_filter: Optional[list[str]] = None, ctx: Context = None) -> dict:
        """RR search drill: keyword-level RR."""
        raise ToolError(f"get_search_query_response_rates: {_PENDING}")

    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def get_merchant_rr_breakdown(agency_id: int, start_date: str, end_date: str,
                                        baseline_start_date: Optional[str] = None,
                                        baseline_end_date: Optional[str] = None, ctx: Context = None) -> dict:
        """RR STEP 5: merchant contribution to the impressions change (comparison mode)."""
        raise ToolError(f"get_merchant_rr_breakdown: {_PENDING}")
