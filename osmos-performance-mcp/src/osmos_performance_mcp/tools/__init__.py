"""SOP tool groups. Each module exposes register_<group>_tools(mcp)."""
from .roas import register_roas_tools
from .cpc import register_cpc_tools
from .ctr import register_ctr_tools
from .bu import register_bu_tools
from .rr import register_rr_tools
from .budget_pacing import register_budget_pacing_tools
from .keyword_delivery import register_keyword_delivery_tools
from .keyword_low_rr import register_keyword_low_rr_tools
from .irrelevancy import register_irrelevancy_tools
from .campaign import register_campaign_tools
from .common import register_common_tools


def register_all_tools(mcp):
    """Register every SOP tool group on an MCP instance."""
    register_common_tools(mcp)
    register_roas_tools(mcp)
    register_cpc_tools(mcp)
    register_ctr_tools(mcp)
    register_bu_tools(mcp)
    register_rr_tools(mcp)
    register_budget_pacing_tools(mcp)
    register_keyword_delivery_tools(mcp)
    register_keyword_low_rr_tools(mcp)
    register_irrelevancy_tools(mcp)
    register_campaign_tools(mcp)


__all__ = ["register_all_tools"]
