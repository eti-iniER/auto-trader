import logging
from typing import Optional
import httpx
from tenacity import (
    after_log,
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .logging import log_request, log_response
from .types import AuthenticationData

logger = logging.getLogger("ig_client")


class OAuth2(httpx.Auth):
    requires_response_body = True

    def __init__(self, get_auth_data_func):
        self._get_auth_data_func = get_auth_data_func
        self.auth_data: Optional[AuthenticationData] = None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.RequestError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.INFO),
    )
    def _make_authenticated_request(self, request):
        """Make an authenticated request with retry logic (sync)."""
        if not self.auth_data:
            logger.debug("Getting authentication data for OAuth2 (sync)")
            # For sync flow, call synchronously
            self.auth_data = self._get_auth_data_func()

        request.headers["Authorization"] = f"Bearer {self.auth_data.access_token}"
        return request

    def auth_flow(self, request):
        # Sync flow retained for completeness (not used with AsyncClient)
        request = self._make_authenticated_request(request)
        log_request(request)
        response = yield request
        log_response(response)
        if response.status_code == 401:
            logger.debug("Received 401, refreshing authentication data (sync)")
            self.auth_data = self._get_auth_data_func()
            retry_request = request
            retry_request.headers["Authorization"] = (
                f"Bearer {self.auth_data.access_token}"
            )
            logger.debug("Retrying request with new authentication (sync)")
            log_request(retry_request)
            retry_response = yield retry_request
            log_response(retry_response)

    async def async_auth_flow(self, request):
        # Apply authentication headers with retry logic (async)
        if not self.auth_data:
            logger.debug("Getting authentication data for OAuth2 (async)")
            self.auth_data = await self._get_auth_data_func()

        request.headers["Authorization"] = f"Bearer {self.auth_data.access_token}"
        log_request(request)
        response = yield request
        # Ensure response body is available for potential retries
        try:
            await response.aread()
        except Exception:
            pass
        log_response(response)

        if response.status_code == 401:
            logger.debug("Received 401, refreshing authentication data (async)")
            self.auth_data = await self._get_auth_data_func()
            retry_request = request
            retry_request.headers["Authorization"] = (
                f"Bearer {self.auth_data.access_token}"
            )
            logger.debug("Retrying request with new authentication (async)")
            log_request(retry_request)
            retry_response = yield retry_request
            try:
                await retry_response.aread()
            except Exception:
                pass
            log_response(retry_response)
