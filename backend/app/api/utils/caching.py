import json
from functools import wraps
from aiocache import Cache
from fastapi import HTTPException


def cache(ttl: int = 60, namespace: str = "main", extra_keys: dict = None):
    """
    Caching decorator for FastAPI endpoints.

    Args:
        message: Time to live for the cache in seconds.
        namespace: Namespace for cache keys in Redis.
        extra_keys: Additional keys to include in the cache key for more granularity.

    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user_id = kwargs.get("user_id") or args[0]

            cache_key_parts = [f"{namespace}:user:{user_id}"]

            if extra_keys:
                for key, value in extra_keys.items():
                    cache_key_parts.append(f"{key}:{value}")

            cache_key = ":".join(cache_key_parts)

            cache = Cache.MEMORY(namespace=namespace)

            cached_value = await cache.get(cache_key)
            if cached_value:
                return json.loads(cached_value)

            response = await func(*args, **kwargs)

            try:
                await cache.set(cache_key, json.dumps(response), ttl=ttl)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error caching data: {e}")

            return response

        return wrapper

    return decorator


def cache_with_pagination(
    ttl: int = 60, namespace: str = "main", extra_keys: dict = None
):
    """
    Caching decorator for paginated endpoints that includes pagination params in cache key.

    Args:
        ttl: Time to live for the cache in seconds.
        namespace: Namespace for cache keys in Redis.
        extra_keys: Additional keys to include in the cache key for more granularity.
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            pagination = kwargs.get("pagination")
            offset = pagination.offset if pagination else 0
            limit = pagination.limit if pagination else 100

            cache_key_parts = [f"{namespace}:offset:{offset}:limit:{limit}"]

            if extra_keys:
                for key, value in extra_keys.items():
                    cache_key_parts.append(f"{key}:{value}")

            cache_key = ":".join(cache_key_parts)

            cache = Cache.MEMORY(namespace=namespace)

            cached_value = await cache.get(cache_key)
            if cached_value:
                return json.loads(cached_value)

            response = await func(*args, **kwargs)

            try:
                if hasattr(response, "model_dump"):
                    response_dict = response.model_dump()
                else:
                    response_dict = response
                await cache.set(cache_key, json.dumps(response_dict), ttl=ttl)
                return response
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error caching data: {e}")

        return wrapper

    return decorator
