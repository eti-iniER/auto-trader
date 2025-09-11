import logging
from functools import wraps
from aiocache import Cache

logger = logging.getLogger("ig_client")


def serialize_for_client_cache(data):
    """Serialize data for client caching using model_dump() to avoid JSON serialization issues."""
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


def deserialize_from_client_cache(data):
    """Deserialize data from client cache - no conversion needed since we store dicts."""
    return data


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

            cache = Cache.MEMORY(namespace=namespace)

            try:
                cached_value = await cache.get(cache_key)
                if cached_value:
                    logger.debug(f"Cache hit for {func.__name__}: {cache_key}")
                    # Reconstruct the original response type
                    if (
                        hasattr(func, "__annotations__")
                        and "return" in func.__annotations__
                    ):
                        return_type = func.__annotations__["return"]
                        if hasattr(return_type, "__origin__"):
                            # Handle generic types like Optional[Type]
                            if (
                                hasattr(return_type, "__args__")
                                and return_type.__args__
                            ):
                                return_type = return_type.__args__[0]

                        # If the return type is a Pydantic model, reconstruct it
                        if hasattr(return_type, "model_validate"):
                            return return_type.model_validate(cached_value)

                    return deserialize_from_client_cache(cached_value)
            except Exception as e:
                logger.warning(f"Cache retrieval failed for {func.__name__}: {e}")

            # Call the original method
            response = await func(self, *args, **kwargs)

            try:
                # Store the serialized data
                await cache.set(
                    cache_key, serialize_for_client_cache(response), ttl=ttl
                )
                logger.debug(
                    f"Cached response for {func.__name__}: {cache_key} (TTL: {ttl}s)"
                )
            except Exception as e:
                logger.warning(f"Cache storage failed for {func.__name__}: {e}")

            return response

        return wrapper

    return decorator
