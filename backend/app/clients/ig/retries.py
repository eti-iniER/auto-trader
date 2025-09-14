import logging
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
    """Decorator for retrying IG API methods with exponential backoff."""

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

    return retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=should_retry,
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.INFO),
        reraise=True,
    )(method)
