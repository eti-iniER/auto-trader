import logging
import asyncio
from functools import wraps
import httpx
from tenacity import (
    after_log,
    before_sleep_log,
    retry,
    stop_after_attempt,
    wait_exponential,
)

from .exceptions import IGAPIError, IGAuthenticationError

logger = logging.getLogger("ig_client")


def ig_api_retry(method):
    """Decorator for retrying IG API methods with exponential backoff and rate limiting."""

    def should_retry(exception):
        """Custom retry condition for IG API calls."""
        # Always retry on network-related errors
        if isinstance(
            exception,
            (
                httpx.HTTPStatusError,
                httpx.RequestError,
                httpx.ConnectError,
                httpx.TimeoutException,
            ),
        ):
            return True

        # Retry on specific IG API errors that are transient
        if isinstance(exception, IGAPIError):
            # Retry on server errors (5xx) and rate limiting
            if exception.status_code in (500, 502, 503, 504, 429):
                return True
            # Don't retry on client errors (4xx) except for rate limiting
            if 400 <= exception.status_code < 500 and exception.status_code != 429:
                return False

        # Don't retry authentication errors (they need credential refresh)
        if isinstance(exception, IGAuthenticationError):
            return False

        return False

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=should_retry,
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.INFO),
        reraise=True,
    )
    @wraps(method)
    async def rate_limited_wrapper(*args, **kwargs):
        """Wrapper that applies rate limiting before calling the method."""
        # First argument should be 'self' (the IGClient instance)
        if args and hasattr(args[0], "_limiter"):
            client_instance = args[0]
            # Apply rate limiting before calling the actual method
            async with client_instance._limiter:
                # Call the method without the rate limiter (since we're handling it here)
                return await method(*args, **kwargs)
        else:
            # Fallback if no rate limiter available
            logger.warning(f"No rate limiter found for method {method.__name__}")
            return await method(*args, **kwargs)

    return rate_limited_wrapper
