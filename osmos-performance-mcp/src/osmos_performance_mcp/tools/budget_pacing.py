"""Budget-pacing tools — backs the debug-budget-pacing skill (PLA only).
Pending each KAM_AGENT_BUDGET_PACING_* config / minute-level data source."""
from typing import Optional

from fastmcp import Context
from fastmcp.exceptions import ToolError

from ..config.settings import settings
from .decorators import rate_limit

_PENDING = "KAM config pending validation — implement like tools/roas.check_gmv_attribution."


def register_budget_pacing_tools(mcp):
    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def get_budget_delivery_mode(marketing_campaign_ids: list[str], ctx: Context = None) -> dict:
        """MANDATORY first diagnostic: ACCELERATED vs STANDARD per campaign."""
        raise ToolError(f"get_budget_delivery_mode: {_PENDING}")

    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def get_budget_pacing_buckets(agency_id: int, date: str, ctx: Context = None) -> dict:
        """Pacing time buckets for the marketplace + date."""
        raise ToolError(f"get_budget_pacing_buckets: {_PENDING}")

    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def get_campaign_daily_budget(marketing_campaign_ids: list[str], date: str, ctx: Context = None) -> dict:
        """Effective daily budget for the campaign(s) on the date."""
        raise ToolError(f"get_campaign_daily_budget: {_PENDING}")

    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def get_minute_level_cpc_data(marketing_campaign_ids: list[str], date: str, ctx: Context = None) -> dict:
        """Minute-level clicks + spend (CPC marketplaces)."""
        raise ToolError(f"get_minute_level_cpc_data: {_PENDING}")

    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def get_minute_level_cpm_data(marketing_campaign_ids: list[str], date: str, ctx: Context = None) -> dict:
        """Minute-level impressions + spend (CPM marketplaces)."""
        raise ToolError(f"get_minute_level_cpm_data: {_PENDING}")

    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def check_budget_changes_on_date(marketing_campaign_ids: list[str], date: str, ctx: Context = None) -> dict:
        """Budget-change audit events on the given date."""
        raise ToolError(f"check_budget_changes_on_date: {_PENDING}")
