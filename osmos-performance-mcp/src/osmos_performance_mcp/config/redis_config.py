"""Redis configuration fetched from Hades at startup (mirrors osmos-reporting-mcp)."""
import logging
from typing import Any, Dict, Optional

import redis
from osSvcClient4pyV2.hades_svc_client import HadesSvcClient

from .settings import settings

logger = logging.getLogger(__name__)


class RedisConfigManager:
    """Manages Redis configuration fetched from Hades."""

    def __init__(self):
        self._config: Optional[Dict[str, Any]] = None
        self._redis_client: Optional[redis.Redis] = None
        self._hades_client = HadesSvcClient(
            app_name=settings.APP_NAME,
            env_domain=settings.ENV_DOMAIN,
        )

    def fetch_config(self) -> Dict[str, Any]:
        """Fetch Redis config from Hades using app key. Called once at startup."""
        logger.info(f"Fetching Redis config from Hades: {settings.REDIS_APP_KEY}")

        self._config = self._hades_client.get_app_context_by_app_key(
            app_key=settings.REDIS_APP_KEY,
            is_json=True,
            application=settings.APP_NAME,
        )

        host = self._config.get("host")
        port = self._config.get("port")
        password = self._config.get("password") or None

        self._redis_client = redis.Redis(
            host=host,
            port=int(port),
            password=password,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30,
        )
        logger.info(f"Redis client initialized: {host}:{port}")

        try:
            self._redis_client.ping()
            logger.info("Redis connection test: OK")
        except Exception as e:
            logger.error(f"Redis connection test FAILED: {e}")

        return self._config

    @property
    def client(self) -> Optional[redis.Redis]:
        return self._redis_client


redis_config_manager = RedisConfigManager()
