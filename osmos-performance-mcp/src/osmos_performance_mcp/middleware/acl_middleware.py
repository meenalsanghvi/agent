"""
ACL Middleware
==============
Token validation via Hades /authorize using os-pyutils AuthHandler — ported from
osmos-reporting-mcp. Reads the token from the x-token header and stores user_id /
user_scope in context state for downstream rate limiting and scope checks.

Single internal endpoint → `allowed_entity_types=None` (all entity types allowed).
"""
from __future__ import annotations

import logging

from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_http_headers
from fastmcp.server.middleware import Middleware, MiddlewareContext

from os_pyutils.authentication import AuthHandler
from os_pyutils.caching import Cache
from os_pyutils.common import RequestDetails
from os_pyutils.constants import APP_IP_AUTH_CACHE
from os_pyutils.enums import AclLevel, Permission

from ..auth.scopes import resolve_user_scope
from ..config.settings import settings

logger = logging.getLogger(__name__)


class _AuthHandlerFromSettings(AuthHandler):
    """AuthHandler that reads config from settings instead of a JSON file."""

    def __init__(self, hades_auth_url: str, app_name: str):
        self.hades_auth_url = hades_auth_url
        self.is_auth_enabled = True
        self.logger = logging.getLogger(f"AuthHandler.{app_name}")
        self.app_name = app_name
        try:
            self.cache = Cache.register_lru_cache(APP_IP_AUTH_CACHE, maxsize=1024)
        except ValueError:
            self.cache = Cache.get_cache(APP_IP_AUTH_CACHE)


class ACLMiddleware(Middleware):
    """Validates the x-token via Hades /authorize and injects user_id/user_scope into state.

    Args:
        allowed_entity_types: restrict entity types (e.g. ["AGENCY"]). None = allow all.
    """

    def __init__(self, allowed_entity_types: list[str] | None = None):
        from osSvcClient4pyV2.hades_svc_client import HadesSvcClient
        hades_client = HadesSvcClient(
            app_name=settings.APP_NAME,
            env_domain=settings.ENV_DOMAIN,
        )
        self.auth_handler = _AuthHandlerFromSettings(
            hades_auth_url=hades_client.hades_authorize,
            app_name=settings.APP_NAME,
        )
        self.allowed_entity_types = (
            {t.upper() for t in allowed_entity_types} if allowed_entity_types else None
        )

    @staticmethod
    def _extract_token(headers: dict) -> str | None:
        return headers.get("x-token")

    def _build_request_details(self, headers: dict, token: str, tool_args: dict) -> RequestDetails:
        headers = dict(headers)
        headers["x-token"] = token

        entity_type = tool_args.get("entity_type")
        entity_id = tool_args.get("entity_id")
        agency_id = (
            headers.get("x-retailer-id")
            or str(tool_args.get("agency_id", ""))
            or (str(entity_id) if entity_type == "AGENCY" and entity_id else "")
        )
        headers["x-retailer-id"] = agency_id

        data = {}
        if entity_type and entity_id:
            data["entityId"] = entity_id
            data["entityType"] = entity_type
            if entity_type == "CLIENT":
                data["clientId"] = entity_id
        if agency_id:
            data["agencyId"] = agency_id
        data["application"] = settings.APP_NAME

        return RequestDetails(
            ip_address_=headers.get("x-forwarded-for", ""),
            method="POST",
            headers=headers,
            cookies={},
            data=data,
        )

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        headers = get_http_headers() or {}
        token = self._extract_token(headers)
        if not token:
            raise ToolError("Authentication required")

        args = context.message.arguments or {}

        entity_type = args.get("entity_type", "").upper() if args.get("entity_type") else ""
        if self.allowed_entity_types and entity_type and entity_type not in self.allowed_entity_types:
            raise ToolError("Access denied")

        request_details = self._build_request_details(headers, token, args)

        entity_auth_config = None
        entity_id = args.get("entity_id")
        if entity_type and entity_id:
            entity_auth_config = {"entityIdKey": "entityId", "entityTypeKey": "entityType"}

        try:
            author_details = await self.auth_handler._authenticate_request(
                request_details=request_details,
                permission=Permission.ACL_READ.value,
                entity_auth_config=entity_auth_config,
                acl_level=AclLevel.CLIENT.value,
            )
        except Exception:
            raise ToolError("Access denied")

        user_id = author_details.get("author") if author_details else None
        user_scope = resolve_user_scope(str(user_id), entity_type) if user_id else ""

        if context.fastmcp_context:
            await context.fastmcp_context.set_state("user_id", user_id, serializable=False)
            await context.fastmcp_context.set_state("user_scope", user_scope, serializable=False)

        return await call_next(context)

    async def on_list_tools(self, context: MiddlewareContext, call_next):
        """Return all tools — auth is checked at call time."""
        return await call_next(context)
