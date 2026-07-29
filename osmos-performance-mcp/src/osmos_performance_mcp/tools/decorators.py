"""Tool decorators for rate limiting (mirrors osmos-reporting-mcp)."""
import functools
import logging

from osSvcClient4pyV2.middlewares.os_redis_rate_limiting import OsRedisRateLimiting

from ..config.redis_config import redis_config_manager

logger = logging.getLogger(__name__)

_rate_limiters: dict = {}


def _get_rate_limiter(points: int, duration: int) -> OsRedisRateLimiting:
    key = (points, duration)
    if key not in _rate_limiters:
        _rate_limiters[key] = OsRedisRateLimiting(
            redis_client=redis_config_manager.client,
            points=points,
            duration=duration,
            key_prefix="osmos_performance_mcp_rl",
        )
    return _rate_limiters[key]


def rate_limit(points: int = 60, duration: int = 60):
    """Rate limit per user_id (read from context state set by ACLMiddleware)."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            ctx = kwargs.get("ctx")
            user_id = (await ctx.get_state("user_id")) if ctx else None
            if not user_id:
                return await func(*args, **kwargs)

            limiter = _get_rate_limiter(points, duration)
            result = limiter.validate_user_limit(
                request_data={"user_id": str(user_id)},
                limit_variable="user_id",
                throw_error=False,
            )
            if result.get("error"):
                logger.error(f"Rate limit Redis error: user={user_id}, error={result['error']}")
            if not result.get("allowed", True):
                retry_after = result.get("ms_before_next", 0) / 1000
                logger.warning(f"Rate limit exceeded: user={user_id}, retry_after={retry_after}s")
                return {"error": "Rate limit exceeded", "code": "RATE_LIMIT_EXCEEDED", "retry_after": retry_after}
            return await func(*args, **kwargs)
        return wrapper
    return decorator
