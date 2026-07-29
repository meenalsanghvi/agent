"""
Common tools — lookups, campaign metadata, and shared performance tools used across
skills. Several of these have candidate mappings to the existing
osmos-campaign-management-mcp (see the gap analysis) — reuse those under the hood
where the schema matches. Pending config/reuse wiring.
"""
from typing import Optional

from fastmcp import Context
from fastmcp.exceptions import ToolError

from ..config.settings import settings
from .decorators import rate_limit

_PENDING = "KAM config / osmos-campaign-management reuse pending — see mcp-tool-gap-analysis.md."


def register_common_tools(mcp):
    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def lookup_campaign(raw_ids: list[str], id_type: str, ctx: Context = None) -> dict:
        """Resolve any campaign ID to marketing_campaign_id + client_id + subtype + bidding_strategy.
        id_type ∈ marketing_campaign_id / marketing_campaign_group_id / campaign_id / campaign_group_id."""
        raise ToolError(f"lookup_campaign: {_PENDING}")

    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def lookup_merchant(agency_id: int, name: Optional[str] = None, seller_id: Optional[str] = None,
                              client_id: Optional[str] = None, ctx: Context = None) -> dict:
        """Resolve a merchant name / seller_id / client_id ↔ os_client_id."""
        raise ToolError(f"lookup_merchant: {_PENDING}")

    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def get_campaign_performance(agency_id: int, start_date: str, end_date: str,
                                       marketing_campaign_ids: Optional[list[str]] = None,
                                       client_ids: Optional[list[str]] = None,
                                       seller_ids: Optional[list[str]] = None,
                                       baseline_start_date: Optional[str] = None,
                                       baseline_end_date: Optional[str] = None, ctx: Context = None) -> dict:
        """Campaign-level cost/orders/revenue/ROI/CPC (comparison mode)."""
        raise ToolError(f"get_campaign_performance: {_PENDING}")

    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def get_campaign_product_selection(marketplace_client_id: int, marketing_campaign_id: str,
                                             ctx: Context = None) -> dict:
        """Current active products in a campaign (with category_l1/l2/l3)."""
        raise ToolError(f"get_campaign_product_selection: {_PENDING}")

    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def get_campaign_status_changes(agency_id: int, timezone: str, start_date: str, end_date: str,
                                          client_ids: Optional[list[str]] = None,
                                          marketing_campaign_ids: Optional[list[str]] = None,
                                          ctx: Context = None) -> dict:
        """Campaign status-change audit trail (changed_by_type=EXTERNAL = merchant-initiated)."""
        raise ToolError(f"get_campaign_status_changes: {_PENDING}")

    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def get_merchant_wallet_balance(client_ids: list[str], ctx: Context = None) -> dict:
        """Merchant wallet balance (zero/near-zero → campaign can't spend)."""
        raise ToolError(f"get_merchant_wallet_balance: {_PENDING}")

    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def get_search_query_performance(agency_id: int, start_date: str, end_date: str,
                                           sort_by: str = "spend",
                                           breakdown_by: Optional[str] = None,
                                           search_queries: Optional[list[str]] = None,
                                           marketing_campaign_ids: Optional[list[str]] = None,
                                           baseline_start_date: Optional[str] = None,
                                           baseline_end_date: Optional[str] = None, ctx: Context = None) -> dict:
        """Search-query performance — what end-users TYPED (impressions/clicks/spend/ctr/cpc,
        AUTO vs manual). breakdown_by='campaign' → served-on competition."""
        raise ToolError(f"get_search_query_performance: {_PENDING}")

    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def get_merchant_keyword_performance(agency_id: int, client_ids: list[str], start_date: str, end_date: str,
                                               baseline_start_date: Optional[str] = None,
                                               baseline_end_date: Optional[str] = None, ctx: Context = None) -> dict:
        """A merchant's targeted keywords × campaign (comparison). NO rows = purely AUTO."""
        raise ToolError(f"get_merchant_keyword_performance: {_PENDING}")

    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def get_merchant_category_performance(agency_id: int, client_ids: list[str], start_date: str, end_date: str,
                                                baseline_start_date: Optional[str] = None,
                                                baseline_end_date: Optional[str] = None, ctx: Context = None) -> dict:
        """A merchant's performance by category × campaign (comparison)."""
        raise ToolError(f"get_merchant_category_performance: {_PENDING}")

    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def get_category_level_performance(agency_id: int, start_date: str, end_date: str,
                                             group_by_merchant: bool = False,
                                             baseline_start_date: Optional[str] = None,
                                             baseline_end_date: Optional[str] = None, ctx: Context = None) -> dict:
        """Category L1/L2/L3 performance (PLA), comparison mode."""
        raise ToolError(f"get_category_level_performance: {_PENDING}")

    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def get_product_selection_changes(agency_id: int, timezone: str, start_date: str, end_date: str,
                                            client_ids: Optional[list[str]] = None,
                                            marketing_campaign_ids: Optional[list[str]] = None,
                                            ctx: Context = None) -> dict:
        """Product additions/removals (audit log)."""
        raise ToolError(f"get_product_selection_changes: {_PENDING}")

    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False})
    @rate_limit(points=settings.RATE_LIMIT_CALLS, duration=settings.RATE_LIMIT_PERIOD)
    async def get_display_ad_unit_performance(agency_id: int, start_date: str, end_date: str,
                                              baseline_start_date: Optional[str] = None,
                                              baseline_end_date: Optional[str] = None, ctx: Context = None) -> dict:
        """Display ad-unit performance (Display only)."""
        raise ToolError(f"get_display_ad_unit_performance: {_PENDING}")
