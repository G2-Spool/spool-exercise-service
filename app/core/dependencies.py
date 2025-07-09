"""Shared dependencies for Exercise Service."""

from typing import Optional
import httpx
from aiocache import Cache
import structlog

from app.core.config import settings

logger = structlog.get_logger()

# Global instances
_redis_cache: Optional[Cache] = None
_http_client: Optional[httpx.AsyncClient] = None


async def get_redis_cache():
    """Get Redis cache instance."""
    global _redis_cache

    if _redis_cache is None:
        try:
            _redis_cache = Cache.from_url(settings.REDIS_URL)
            await _redis_cache.exists("test")  # Test connection
            logger.info("Redis cache connection established")
        except Exception as e:
            logger.warning(f"Redis cache not available: {e}")
            # Fallback to in-memory cache
            _redis_cache = Cache(Cache.MEMORY)

    return _redis_cache


async def get_http_client() -> httpx.AsyncClient:
    """Get HTTP client for service communication."""
    global _http_client

    if _http_client is None:
        _http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            headers={
                "Content-Type": "application/json",
                "User-Agent": f"{settings.SERVICE_NAME}/{settings.APP_VERSION}",
            },
        )

    return _http_client


async def get_content_service_client() -> httpx.AsyncClient:
    """Get HTTP client configured for content service."""
    client = await get_http_client()
    # Could add specific headers or auth here
    return client


async def get_profile_service_client() -> httpx.AsyncClient:
    """Get HTTP client configured for profile service."""
    client = await get_http_client()
    # Could add specific headers or auth here
    return client
