"""
FastMCP Server
==============
MCP server exposing the data-analysis agent's SOP tools (KAM-backed + Python math).
Single internal endpoint (marketplace ops analysts), mirroring the osmos-reporting-mcp
skeleton (build_mcp factory + Starlette/uvicorn mount).

Endpoint:
  /osmosPerformanceMcp — internal analyst tooling (all entity types)
"""
from __future__ import annotations

import logging
import os

import uvicorn
from fastmcp import FastMCP
from fastmcp.server.lifespan import lifespan
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from .clients.kam_client import KAMClient
from .config.settings import settings
from .config.redis_config import redis_config_manager
from .middleware.acl_middleware import ACLMiddleware
from .middleware.response_size_middleware import ResponseSizeMiddleware
from .tools import register_all_tools

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

# ── Shared instances ────────────────────────────────────────────────
kam_client = KAMClient()


# ── MCP instance factory ────────────────────────────────────────────

def build_mcp(name: str, allowed_entity_types: list[str] | None = None) -> FastMCP:
    """Build a configured FastMCP instance."""

    @lifespan
    async def mcp_lifespan(server):
        yield {"kam_client": kam_client}

    mcp = FastMCP(name=name, lifespan=mcp_lifespan)

    register_all_tools(mcp)

    mcp.add_middleware(ACLMiddleware(allowed_entity_types=allowed_entity_types))
    mcp.add_middleware(ResponseSizeMiddleware())
    return mcp


# Single internal endpoint (all entity types allowed).
analysis_mcp = build_mcp(name=settings.APP_NAME, allowed_entity_types=None)


# ── Health endpoints ─────────────────────────────────────────────────

async def health_check(request):
    return JSONResponse({"status": "healthy", "service": settings.APP_NAME})


async def readiness_check(request):
    return JSONResponse({"status": "ready"})


# ── Entrypoint ───────────────────────────────────────────────────────

def main():
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8080"))

    # Redis for rate limiting
    redis_config_manager.fetch_config()

    analysis_app = analysis_mcp.http_app(path="/", stateless_http=True)

    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def combined_lifespan(app):
        async with analysis_app.lifespan(analysis_app):
            yield

    from starlette.middleware import Middleware as StarletteMiddleware

    class TrailingSlashMiddleware:
        """Add trailing slash so Mount matches the base path without one."""
        def __init__(self, app):
            self.app = app

        async def __call__(self, scope, receive, send):
            if scope["type"] == "http" and scope["path"] == "/osmosPerformanceMcp":
                scope["path"] = "/osmosPerformanceMcp/"
            await self.app(scope, receive, send)

    app = Starlette(
        routes=[
            Route("/health", health_check, methods=["GET"]),
            Route("/osmosPerformanceMcp/health", health_check, methods=["GET"]),
            Route("/osmosPerformanceMcp/ready", readiness_check, methods=["GET"]),
            Mount("/osmosPerformanceMcp", app=analysis_app),
        ],
        lifespan=combined_lifespan,
        middleware=[StarletteMiddleware(TrailingSlashMiddleware)],
    )

    logger.info(f"Starting {settings.APP_NAME} on http://{host}:{port}")
    logger.info("  endpoint: /osmosPerformanceMcp")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
