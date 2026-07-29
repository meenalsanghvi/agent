"""Keyword-low-RR tools — backs the debug-keyword-low-rr skill (PLA only, current period).
Reuses check_keyword_request_volume / get_keyword_categories / get_campaigns_in_category /
get_response_rate_by_dimension from other groups; this module adds nothing new yet.
Pending: get_campaigns_in_category (see common) + supply-side reports."""
from fastmcp import Context
from fastmcp.exceptions import ToolError

from ..config.settings import settings
from .decorators import rate_limit

_PENDING = "KAM config pending validation — implement like tools/roas.check_gmv_attribution."


def register_keyword_low_rr_tools(mcp):
    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def get_keyword_categories(marketplace_client_id: int, search_queries: list[str], ctx: Context = None) -> dict:
        """Categories mapped to keyword(s) from the S3 keyword-category files (PLA).
        Shared with debug-keyword-delivery / debug-irrelevancy."""
        raise ToolError(f"get_keyword_categories: {_PENDING}")
