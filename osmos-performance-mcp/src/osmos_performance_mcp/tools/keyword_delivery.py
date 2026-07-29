"""Keyword-delivery tools — backs the debug-keyword-delivery skill (PLA only).
Pending each KAM_AGENT_KW_DELIVERY_* config."""
from typing import Optional

from fastmcp import Context
from fastmcp.exceptions import ToolError

from ..config.settings import settings
from .decorators import rate_limit

_PENDING = "KAM config pending validation — implement like tools/roas.check_gmv_attribution."


def register_keyword_delivery_tools(mcp):
    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def check_targeted_keyword_performance_in_campaigns(agency_id: int, client_ids: list[str],
                                                              marketing_campaign_ids: list[str],
                                                              start_date: str, end_date: str,
                                                              search_queries: Optional[list[str]] = None,
                                                              ctx: Context = None) -> dict:
        """Validate a targeted keyword INSIDE the user's campaign(s)."""
        raise ToolError(f"check_targeted_keyword_performance_in_campaigns: {_PENDING}")

    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def check_keyword_request_volume(search_queries: list[str], end_date: str, ctx: Context = None) -> dict:
        """>100 requests / trailing 7 days eligibility check."""
        raise ToolError(f"check_keyword_request_volume: {_PENDING}")

    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def get_targeted_keyword_competition(agency_id: int, search_queries: list[str], start_date: str, end_date: str,
                                               exclude_marketing_campaign_ids: Optional[list[str]] = None,
                                               baseline_start_date: Optional[str] = None,
                                               baseline_end_date: Optional[str] = None, ctx: Context = None) -> dict:
        """Rivals that TARGET the keyword + their bids (comparison, new_in_post)."""
        raise ToolError(f"get_targeted_keyword_competition: {_PENDING}")

    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def get_search_query_match_performance(agency_id: int, client_ids: list[str],
                                                 marketing_campaign_ids: list[str],
                                                 start_date: str, end_date: str,
                                                 search_queries: Optional[list[str]] = None, ctx: Context = None) -> dict:
        """Search-query Share of Voice (sov, top_search_impressions_share)."""
        raise ToolError(f"get_search_query_match_performance: {_PENDING}")
