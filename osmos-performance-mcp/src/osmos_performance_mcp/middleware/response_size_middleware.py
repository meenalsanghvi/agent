"""
Response Size Middleware
=======================
Rejects tool responses that exceed an estimated token limit (~2.5 bytes/token).
Reused verbatim from osmos-reporting-mcp.
"""
from __future__ import annotations

import logging

import pydantic_core
from fastmcp.exceptions import ToolError
from fastmcp.server.middleware import Middleware, MiddlewareContext

from ..config.settings import settings

logger = logging.getLogger(__name__)


def estimate_tokens(data: bytes) -> int:
    """Estimate token count from serialized bytes."""
    return int(len(data) / settings.BYTES_PER_TOKEN)


class ResponseSizeMiddleware(Middleware):
    """Rejects oversized tool responses with a helpful error message."""

    def __init__(self, *, max_tokens: int = settings.MAX_RESPONSE_TOKENS, tools: list[str] | None = None):
        if max_tokens <= 0:
            raise ValueError(f"max_tokens must be positive, got {max_tokens}")
        self.max_tokens = max_tokens
        self.tools = set(tools) if tools is not None else None

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        result = await call_next(context)

        if self.tools is not None and context.message.name not in self.tools:
            return result

        serialized = pydantic_core.to_json(result, fallback=str)
        token_estimate = estimate_tokens(serialized)

        if token_estimate <= self.max_tokens:
            return result

        logger.warning(
            "Tool %r response exceeds token limit: ~%d tokens > %d max",
            context.message.name,
            token_estimate,
            self.max_tokens,
        )
        raise ToolError(
            f"Response too large (~{token_estimate:,} tokens, limit {self.max_tokens:,}). "
            f'Narrow the period, add filters, or request fewer merchants/SKUs.'
        )
