"""
User scope resolution
=====================
Internal analyst tooling: a single internal endpoint. `resolve_user_scope` is kept
as the extension point that osmos-reporting-mcp uses for visibility gating; here it
returns an INTERNAL scope. Tighten if per-user restrictions are later required.
"""


def resolve_user_scope(user_id: str, entity_type: str = "") -> str:
    """Return the access scope for an authenticated internal user.

    The agent runs at marketplace (agency) level for internal ops analysts, so the
    default scope is "INTERNAL". This is the hook to plug real per-user scope
    resolution into if/when the endpoint is exposed more broadly.
    """
    return "INTERNAL"
