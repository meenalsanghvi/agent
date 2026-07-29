"""Campaign-diagnostic tools — backs the debug-campaign skill (single campaign, PLA).
Most tools are shared (common.py: lookup_campaign, get_campaign_performance,
get_campaign_product_selection, get_merchant_wallet_balance, get_campaign_status_changes;
cpc.py, roas.py). This module adds the campaign-specific eligibility checks. Pending config."""
from typing import Optional

from fastmcp import Context
from fastmcp.exceptions import ToolError

from ..config.settings import settings
from .decorators import rate_limit

_PENDING = "KAM config pending validation — implement like tools/roas.check_gmv_attribution."


def register_campaign_tools(mcp):
    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def get_campaigns_in_category(agency_id: int, start_date: str, end_date: str,
                                        category_level: str = "l3",
                                        marketing_campaign_ids: Optional[list[str]] = None,
                                        category_l1_filter: Optional[str] = None,
                                        category_l2_filter: Optional[str] = None,
                                        category_l3_filter: Optional[str] = None,
                                        baseline_start_date: Optional[str] = None,
                                        baseline_end_date: Optional[str] = None, ctx: Context = None) -> dict:
        """Campaigns competing WITHIN a category (PLA): per-campaign cpc/cpm, subtype,
        new_entrants_in_period. Used by CPC/ROAS/keyword competition + campaign diagnostic."""
        raise ToolError(f"get_campaigns_in_category: {_PENDING}")

    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def get_campaign_targeted_keywords(marketplace_client_id: int, marketing_campaign_id: str,
                                             client_id: str, ctx: Context = None) -> dict:
        """The campaign's MANUAL targeted keywords (text, bidding_value) + negatives.
        The manual-vs-auto gate. SEARCH campaigns only."""
        raise ToolError(f"get_campaign_targeted_keywords: {_PENDING}")

    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def get_campaign_targeted_networks(client_id: str, marketing_campaign_id: Optional[str] = None,
                                             campaign_id: Optional[str] = None, ctx: Context = None) -> dict:
        """The networks a campaign targets (scope network-level RR drills)."""
        raise ToolError(f"get_campaign_targeted_networks: {_PENDING}")
