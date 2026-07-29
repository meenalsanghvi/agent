"""
CPC tools — backs the debug-cpc skill.
Registered with the standard pattern; bodies pending each KAM_AGENT_CPC_* config.
Fill in exactly like tools/roas.py::check_gmv_attribution (fetch via
KAMClient.fetch_agent_report → normalize → metrics.*).
"""
from typing import Optional

from fastmcp import Context
from fastmcp.exceptions import ToolError

from ..config.settings import settings
from .decorators import rate_limit

_PENDING = "KAM config pending validation — implement like tools/roas.check_gmv_attribution."


def register_cpc_tools(mcp):
    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def get_page_level_performance(agency_id: int, start_date: str, end_date: str,
                                         program_type: Optional[str] = None,
                                         baseline_start_date: Optional[str] = None,
                                         baseline_end_date: Optional[str] = None, ctx: Context = None) -> dict:
        """CPC STEP 1: page-type CPC/spend/clicks + I/R, comparison mode. (Shared with CTR/BU.)"""
        raise ToolError(f"get_page_level_performance: {_PENDING}")

    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def get_merchant_cpc_breakdown(agency_id: int, start_date: str, end_date: str,
                                         program_type: Optional[str] = None,
                                         baseline_start_date: Optional[str] = None,
                                         baseline_end_date: Optional[str] = None, ctx: Context = None) -> dict:
        """CPC STEP 3: merchant CPC contribution to the spend change."""
        raise ToolError(f"get_merchant_cpc_breakdown: {_PENDING}")

    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def get_campaign_subtype_cpc_breakdown(agency_id: int, start_date: str, end_date: str,
                                                 baseline_start_date: Optional[str] = None,
                                                 baseline_end_date: Optional[str] = None, ctx: Context = None) -> dict:
        """CPC STEP 2 (PLA): CPC by campaign subtype (smart_shopping vs os_ads_search)."""
        raise ToolError(f"get_campaign_subtype_cpc_breakdown: {_PENDING}")

    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def get_merchant_category_cpc_comparison(agency_id: int, client_ids: list[str], start_date: str, end_date: str,
                                                   baseline_start_date: Optional[str] = None,
                                                   baseline_end_date: Optional[str] = None, ctx: Context = None) -> dict:
        """CPC STEP 4 (PLA): merchant categories vs category average, with verdict."""
        raise ToolError(f"get_merchant_category_cpc_comparison: {_PENDING}")

    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def get_sku_level_cpc_performance(agency_id: int, client_ids: list[str], start_date: str, end_date: str,
                                            baseline_start_date: Optional[str] = None,
                                            baseline_end_date: Optional[str] = None, ctx: Context = None) -> dict:
        """CPC STEP 6 (PLA): SKU-level CPC contribution."""
        raise ToolError(f"get_sku_level_cpc_performance: {_PENDING}")
