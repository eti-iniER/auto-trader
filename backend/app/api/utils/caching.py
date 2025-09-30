from functools import wraps
from aiocache import caches
from fastapi import HTTPException


def serialize_for_cache(data):
    """Serialize data for caching using model_dump() to avoid JSON serialization issues."""
    # If it's a Pydantic model, use model_dump
    if hasattr(data, "model_dump"):
        return data.model_dump()
    elif isinstance(data, list):
        # Handle list of Pydantic models
        return [
            item.model_dump() if hasattr(item, "model_dump") else item for item in data
        ]
    else:
        # For plain dictionaries or other serializable data
        return data


def deserialize_from_cache(data):
    """Deserialize data from cache - no conversion needed since we store dicts."""
    return data


def cache(ttl: int = 60, namespace: str = "main", extra_keys: dict = None):
    """
    Caching decorator for FastAPI endpoints.
    Automatically includes user ID and user mode in cache key when available.

    Args:
        ttl: Time to live for the cache in seconds.
        namespace: Namespace for cache keys in Redis.
        extra_keys: Additional keys to include in the cache key for more granularity.
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Try to find user in kwargs
            user = kwargs.get("user")

            cache_key_parts = [f"{namespace}"]

            if user:
                user_mode = user.settings.mode.value if user.settings else "unknown"
                cache_key_parts.extend([f"user:{user.id}", f"mode:{user_mode}"])

            # Add any extra keys provided
            if extra_keys:
                for key, value in extra_keys.items():
                    cache_key_parts.append(f"{key}:{value}")

            # Add function arguments to cache key (like id parameter)
            for key, value in kwargs.items():
                if key not in [
                    "user",
                    "db",
                    "request",
                    "pagination",
                    "sorting",
                    "filters",
                ]:
                    cache_key_parts.append(f"{key}:{value}")

            cache_key = ":".join(cache_key_parts)

            cache = caches.get("requests")

            cached_value = await cache.get(cache_key)
            if cached_value:
                return deserialize_from_cache(cached_value)

            response = await func(*args, **kwargs)

            try:
                # Store the serialized data directly (no JSON encoding needed)
                await cache.set(cache_key, serialize_for_cache(response), ttl=ttl)
            except Exception:
                # Don't fail the request if caching fails
                pass

            return response

        return wrapper

    return decorator


def cache_user_data(ttl: int = 60, namespace: str = "main"):
    """
    Caching decorator for functions that take a user parameter.
    Automatically includes user ID and user mode in cache key.

    Args:
        ttl: Time to live for the cache in seconds.
        namespace: Namespace for cache keys in Redis.
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Try to find user in args or kwargs
            user = None
            if args and hasattr(args[0], "id"):  # User is first positional argument
                user = args[0]
            elif "user" in kwargs:
                user = kwargs["user"]

            if not user:
                # If no user found, call function without caching
                return await func(*args, **kwargs)

            # Build user-specific cache key
            user_mode = user.settings.mode.value if user.settings else "unknown"
            cache_key = f"{namespace}:user:{user.id}:mode:{user_mode}"

            cache = caches.get("requests")

            cached_value = await cache.get(cache_key)
            if cached_value:
                return deserialize_from_cache(cached_value)

            response = await func(*args, **kwargs)

            try:
                # Store the serialized data directly (no JSON encoding needed)
                await cache.set(cache_key, serialize_for_cache(response), ttl=ttl)
            except Exception:
                # Don't fail the request if caching fails, just log it
                pass

            return response

        return wrapper

    return decorator


def cache_with_pagination(
    ttl: int = 60, namespace: str = "main", extra_keys: dict = None
):
    """
    Caching decorator for paginated endpoints that includes pagination params in cache key.
    Automatically includes user ID and user mode in cache key for user-specific caching.

    Args:
        ttl: Time to live for the cache in seconds.
        namespace: Namespace for cache keys in Redis.
        extra_keys: Additional keys to include in the cache key for more granularity.
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            pagination = kwargs.get("pagination")
            user = kwargs.get("user")
            offset = pagination.offset if pagination else 0
            limit = pagination.limit if pagination else 100

            # Build cache key with user information for isolation
            cache_key_parts = [f"{namespace}"]

            if user:
                user_mode = user.settings.mode.value if user.settings else "unknown"
                cache_key_parts.extend([f"user:{user.id}", f"mode:{user_mode}"])

            cache_key_parts.extend([f"offset:{offset}", f"limit:{limit}"])

            # Add sorting parameters if available
            sorting = kwargs.get("sorting")
            if sorting:
                if hasattr(sorting, "sort_by") and sorting.sort_by:
                    cache_key_parts.append(f"sort_by:{sorting.sort_by}")
                if hasattr(sorting, "sort_order") and sorting.sort_order:
                    cache_key_parts.append(f"sort_order:{sorting.sort_order}")

            # Add filter parameters if available
            filters = kwargs.get("filters")
            if filters:
                filter_dict = filters.to_dict() if hasattr(filters, "to_dict") else {}
                for key, value in filter_dict.items():
                    if value is not None:
                        cache_key_parts.append(f"filter_{key}:{value}")

            if extra_keys:
                for key, value in extra_keys.items():
                    cache_key_parts.append(f"{key}:{value}")

            cache_key = ":".join(cache_key_parts)

            cache = caches.get("requests")

            cached_value = await cache.get(cache_key)
            if cached_value:
                return deserialize_from_cache(cached_value)

            response = await func(*args, **kwargs)

            try:
                # Store the serialized data directly (no JSON encoding needed)
                await cache.set(cache_key, serialize_for_cache(response), ttl=ttl)
                return response
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error caching data: {e}")

        return wrapper

    return decorator
