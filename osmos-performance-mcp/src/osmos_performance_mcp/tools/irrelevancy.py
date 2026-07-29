"""Irrelevancy tools — backs the debug-irrelevancy skill (PLA, SEARCH page only).
Pending KAM_AGENT_IRRELEVANCY_* config."""
from fastmcp import Context
from fastmcp.exceptions import ToolError

from ..config.settings import settings
from .decorators import rate_limit

_PENDING = "KAM config pending validation — implement like tools/roas.check_gmv_attribution."


def register_irrelevancy_tools(mcp):
    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def get_responded_skus(marketplace_client_id: int, start_date: str, end_date: str,
                                 search_queries: list[str], campaign_ids: list[str],
                                 product_name_like: str = None, ctx: Context = None) -> dict:
        """Per keyword × cache_type × SKU: the SKUs actually served (cache_type = the
        relevancy algorithm that served each). The core irrelevancy signal."""
        raise ToolError(f"get_responded_skus: {_PENDING}")
