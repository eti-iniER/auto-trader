import logging
from functools import wraps
from urllib.parse import urlparse

from aiocache import Cache
from aiocache.serializers import PickleSerializer

from app.config import settings

logger = logging.getLogger("ig_client")

# Parse REDIS_URL only once (e.g. redis://:password@host:port/db)
_redis_url = urlparse(settings.REDIS_URL)
_redis_host = _redis_url.hostname or "localhost"
_redis_port = _redis_url.port or 6379
_redis_db = int((_redis_url.path or "/0").lstrip("/")) if _redis_url.path else 0
_redis_password = _redis_url.password

# Create a module-level Redis cache instance with Pickle serialization.
# Pickle lets us store/retrieve pydantic models (v2) and arbitrary python objects
# without maintaining custom (de)serialization code.
_redis_cache = Cache(
    Cache.REDIS,
    endpoint=_redis_host,
    port=_redis_port,
    db=_redis_db,
    password=_redis_password,
    serializer=PickleSerializer(),
)


def cache_client_request(ttl: int = 60, namespace: str = "ig_client"):
    """
    Caching decorator for IG client methods.
    Automatically includes client credentials hash and method parameters in cache key.

    Args:
        ttl: Time to live for the cache in seconds.
        namespace: Namespace for cache keys.
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Build cache key based on client identity and method parameters
            cache_key_parts = [f"{namespace}", func.__name__]

            # Add client identity (use username and account_id to identify unique client)
            cache_key_parts.extend(
                [f"user:{self.username}", f"account:{self.account_id}"]
            )

            # Add method arguments to cache key
            for arg in args:
                if hasattr(arg, "model_dump"):
                    # Pydantic model - use its serialized form
                    arg_dict = arg.model_dump(exclude_none=True)
                    for key, value in arg_dict.items():
                        cache_key_parts.append(f"{key}:{value}")
                else:
                    # Simple type
                    cache_key_parts.append(str(arg))

            for key, value in kwargs.items():
                if hasattr(value, "model_dump"):
                    # Pydantic model - use its serialized form
                    value_dict = value.model_dump(exclude_none=True)
                    for k, v in value_dict.items():
                        cache_key_parts.append(f"{key}_{k}:{v}")
                else:
                    cache_key_parts.append(f"{key}:{value}")

            cache_key = ":".join(cache_key_parts)

            # Reuse the module-level Redis cache; namespace still influences the key.
            cache = _redis_cache

            try:
                cached_value = await cache.get(cache_key, namespace=namespace)
                if cached_value is not None:
                    logger.debug(f"Cache hit for {func.__name__}: {cache_key}")
                    # PickleSerializer returns the original python object directly.
                    return cached_value
            except Exception as e:
                logger.warning(f"Cache retrieval failed for {func.__name__}: {e}")

            # Call the original method
            response = await func(self, *args, **kwargs)

            try:
                # Store the serialized data
                await cache.set(cache_key, response, ttl=ttl, namespace=namespace)
                logger.debug(
                    f"Cached response for {func.__name__}: {cache_key} (TTL: {ttl}s)"
                )
            except Exception as e:
                logger.warning(f"Cache storage failed for {func.__name__}: {e}")

            return response

        return wrapper

    return decorator
