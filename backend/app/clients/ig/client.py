import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import asyncio
import httpx
from aiocache import Cache
from aiolimiter import AsyncLimiter
from app.config import settings
from app.db.enums import UserSettingsMode
from app.db.models import User
from fastapi import HTTPException, status
from tenacity import (
    after_log,
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .exceptions import IGAPIError, IGAuthenticationError
from .types import *

logger = logging.getLogger("ig_client")


# Common retry decorator for API methods
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


def log_request(request):
    """Log the outgoing request details."""
    logger.debug(f"=== REQUEST ===")
    logger.debug(f"Method: {request.method}")
    logger.debug(f"URL: {request.url}")
    logger.debug(f"Headers: {dict(request.headers)}")

    # For httpx, check if request has content to log
    try:
        if hasattr(request, "content") and request.content:
            content = request.content
            if isinstance(content, bytes):
                try:
                    if request.headers.get("content-type", "").startswith(
                        "application/json"
                    ):
                        body = json.loads(content.decode("utf-8"))
                        logger.debug(f"Body: {json.dumps(body, indent=2)}")
                    else:
                        logger.debug(f"Body: {content.decode('utf-8')}")
                except (UnicodeDecodeError, json.JSONDecodeError):
                    logger.debug(f"Body (raw): {content}")
            else:
                logger.debug(f"Body: {content}")
        elif hasattr(request, "stream") and request.stream:
            # For streamed requests, we can't easily log the body without consuming it
            logger.debug("Body: <streamed content>")
    except Exception as e:
        logger.debug(f"Could not log request body: {e}")
    logger.debug("=== END REQUEST ===")


def log_response(response):
    """Log the incoming response details."""
    logger.debug(f"=== RESPONSE ===")
    logger.debug(f"Status Code: {response.status_code}")
    logger.debug(f"Headers: {dict(response.headers)}")

    try:
        # Ensure the response content is read
        if not response.is_closed:
            # For sync responses, .read() ensures content; async hook ensures aread() beforehand
            if hasattr(response, "_content") and response._content is None:
                try:
                    response.read()
                except Exception:
                    # In async context, read is handled in async hook
                    pass

        if response.content:
            if response.headers.get("content-type", "").startswith("application/json"):
                try:
                    body = response.json()
                    logger.debug(f"Body: {json.dumps(body, indent=2)}")
                except json.JSONDecodeError:
                    # Fallback to text if JSON parsing fails
                    logger.debug(f"Body: {response.text}")
            else:
                logger.debug(f"Body: {response.text}")
        else:
            logger.debug("Body: <empty>")
    except (json.JSONDecodeError, UnicodeDecodeError):
        try:
            logger.debug(f"Body (raw): {response.content}")
        except Exception:
            logger.debug("Body: <could not decode>")
    except Exception as e:
        logger.debug(f"Could not log response body: {e}")
    logger.debug("=== END RESPONSE ===")


def request_hook(request):
    """Hook called before sending a request (sync client)."""
    log_request(request)


def response_hook(response):
    """Hook called after receiving a response (sync client)."""
    log_response(response)


async def async_request_hook(request):
    """Async hook called before sending a request (AsyncClient)."""
    log_request(request)


async def async_response_hook(response):
    """Async hook called after receiving a response (AsyncClient)."""
    try:
        # Ensure content is read in async context for safe logging
        await response.aread()
    except Exception:
        pass
    log_response(response)


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


class IGClient:
    # Class-level cache for storing client instances
    _client_cache = Cache.MEMORY(namespace="ig_clients")

    def __init__(
        self,
        username: str,
        password: str,
        account_id: str,
        api_key: str,
        base_url: str = settings.IG_DEMO_API_BASE_URL,
        rpm_limit: int = 60,
        managed_by_cache: bool = False,
        cache_key: Optional[str] = None,
    ):
        self.username = username
        self.password = password
        self.api_key = api_key
        self.base_url = base_url
        self.account_id = account_id
        # Whether this client instance lifecycle is managed by the class-level cache
        self._managed_by_cache = managed_by_cache
        self._cache_key = cache_key
        # Per-user async rate limiter (default 60 requests per minute)
        self._limiter = AsyncLimiter(max_rate=rpm_limit, time_period=60)

        # Async HTTP client
        self.client = httpx.AsyncClient(
            auth=OAuth2(self._get_auth_data),
            base_url=base_url,
            headers={
                "X-IG-API-KEY": self.api_key,
                "IG-ACCOUNT-ID": self.account_id,
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Version": "3",
            },
            event_hooks={
                "request": [async_request_hook],
                "response": [async_response_hook],
            },
        )

    @classmethod
    async def create_for_user(cls, user: User) -> "IGClient":
        """
        Create IG client instance using user's mode-specific credentials.
        Returns a cached client if available, otherwise creates and caches a new one.

        Args:
            user: The authenticated user with settings containing IG credentials

        Returns:
            IGClient: Configured IG client instance (cached or new)

        Raises:
            HTTPException: If user settings are missing or credentials are incomplete
        """
        if not user.settings:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User settings not found. Please configure your IG credentials.",
            )

        # Create cache key based on user ID and mode
        user_mode = user.settings.mode.value
        cache_key = f"user:{user.id}:mode:{user_mode}"

        # Try to get cached client first
        try:
            cached_client = await cls._client_cache.get(cache_key)
            if cached_client is not None:
                # Ensure cached instance is marked correctly
                cached_client._managed_by_cache = True
                cached_client._cache_key = cache_key
                logger.debug(
                    f"Using cached IG client for user {user.id} in {user_mode} mode"
                )
                return cached_client
        except Exception as e:
            logger.warning(f"Failed to retrieve cached client for user {user.id}: {e}")
            # Continue to create new client if cache retrieval fails

        # No cached client found, create new one
        logger.debug(f"Creating new IG client for user {user.id} in {user_mode} mode")

        if user.settings.mode == UserSettingsMode.DEMO:
            api_key = user.settings.demo_api_key
            username = user.settings.demo_username
            password = user.settings.demo_password
            base_url = settings.IG_DEMO_API_BASE_URL
            account_id = user.settings.demo_account_id
        else:  # LIVE mode
            api_key = user.settings.live_api_key
            username = user.settings.live_username
            password = user.settings.live_password
            base_url = settings.IG_LIVE_API_BASE_URL
            account_id = user.settings.live_account_id

        if not all([api_key, username, password]):
            mode_str = user.settings.mode.value.lower()
            logger.error(
                f"Credentials are: {api_key}, {username}, {password}, {account_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing {mode_str} mode IG credentials. Please configure your {mode_str} API key, username, and password.",
            )

        client = cls(
            username=username,
            password=password,
            api_key=api_key,
            base_url=base_url,
            account_id=account_id,
            managed_by_cache=True,
            cache_key=cache_key,
        )

        # Cache the client for 30 minutes (IG sessions typically last 6+ hours)
        try:
            await cls._client_cache.set(cache_key, client, ttl=1800)
            logger.debug(
                f"Cached IG client for user {user.id} in {user_mode} mode (TTL: 30 minutes)"
            )
        except Exception as e:
            logger.warning(f"Failed to cache client for user {user.id}: {e}")
            # Continue even if caching fails

        return client

    @classmethod
    async def invalidate_user_cache(cls, user: User):
        """
        Invalidate cached IG client for a specific user.
        Useful when user credentials change or when forcing a fresh client.

        Args:
            user: The user whose cached client should be invalidated
        """
        if not user.settings:
            return

        user_mode = user.settings.mode.value
        cache_key = f"user:{user.id}:mode:{user_mode}"

        try:
            # Close and remove cached client if present
            cached_client = await cls._client_cache.get(cache_key)
            if cached_client is not None:
                try:
                    await cached_client.client.aclose()
                except Exception as e:
                    logger.warning(
                        f"Failed to close cached client for user {user.id}: {e}"
                    )
            await cls._client_cache.delete(cache_key)
            logger.debug(
                f"Invalidated cached IG client for user {user.id} in {user_mode} mode"
            )
        except Exception as e:
            logger.warning(f"Failed to invalidate cache for user {user.id}: {e}")

    @classmethod
    async def clear_all_cache(cls):
        """
        Clear all cached IG clients.
        Useful for maintenance or when global cache reset is needed.
        """
        try:
            await cls._client_cache.clear()
            logger.info("Cleared all cached IG clients")
        except Exception as e:
            logger.warning(f"Failed to clear IG client cache: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # For sync contexts; ensure proper close if used inadvertently
        # Do not close if managed by cache; lifecycle controlled elsewhere
        if self._managed_by_cache:
            return
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.client.aclose())
            else:
                loop.run_until_complete(self.client.aclose())
        except Exception:
            pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        # Do not close if managed by cache; lifecycle controlled elsewhere
        if not self._managed_by_cache:
            await self.client.aclose()

    async def close(self):
        # If this instance is returned from cache, treat close() as a no-op to avoid
        # shutting down a shared client unexpectedly. Use invalidate_user_cache to
        # explicitly dispose of a cached client.
        if not self._managed_by_cache:
            await self.client.aclose()

    @ig_api_retry
    async def get_session(self) -> GetSessionResponse:
        """
        Retrieves the session information from the IG API.
        This includes the access token and other session details.
        """
        async with httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "X-IG-API-KEY": self.api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Version": "3",
            },
            event_hooks={
                "request": [async_request_hook],
                "response": [async_response_hook],
            },
        ) as client:
            async with self._limiter:
                response = await client.post(
                    "session",
                    json={
                        "identifier": self.username,
                        "password": self.password,
                    },
                )

            # Process the response while the client is still open
            try:
                data = response.json()
            except Exception as e:
                logger.error(f"Failed to parse response JSON: {e}")
                logger.error(f"Response status: {response.status_code}")
                logger.error(f"Response content: {response.content}")
                raise IGAPIError(
                    message="Failed to parse response",
                    status_code=response.status_code,
                    error_code="PARSE_ERROR",
                )

            if response.status_code != 200:
                logger.error(
                    f"Session request failed with status {response.status_code}"
                )
                logger.error(f"Error response body: {data}")
                raise IGAPIError(
                    message=data.get("errorCode", "Unknown error"),
                    status_code=response.status_code,
                    error_code=data.get("errorCode"),
                )

            logger.info("Session data retrieved successfully")
            return GetSessionResponse(**data)

    @ig_api_retry
    async def get_history(self, filters: GetHistoryFilters) -> GetHistoryResponse:
        """
        Retrieves the historical data for the account.
        """
        async with self._limiter:
            response = await self.client.get(
                "history/activity",
                params=filters.model_dump(
                    by_alias=True, mode="json", exclude_none=True
                ),
            )

        # Handle non-200 responses appropriately for retry logic
        if response.status_code >= 500 or response.status_code == 429:
            response.raise_for_status()

        data = response.json()

        if response.status_code != 200:
            raise IGAPIError(
                message=data.get("errorCode", "Unknown error"),
                status_code=response.status_code,
                error_code=data.get("errorCode"),
            )

        return GetHistoryResponse(**data)

    @ig_api_retry
    async def get_positions(self) -> PositionsResponse:
        """
        Retrieve open positions for the account.
        """
        async with self._limiter:
            response = await self.client.get("positions", headers={"Version": "2"})

        # Handle non-200 responses appropriately for retry logic
        if response.status_code >= 500 or response.status_code == 429:
            response.raise_for_status()

        data = response.json()

        if response.status_code != 200:
            raise IGAPIError(
                message=data.get("errorCode", "Unknown error"),
                status_code=response.status_code,
                error_code=data.get("errorCode"),
            )

        return PositionsResponse(**data)

    @ig_api_retry
    async def create_position(
        self, data: CreatePositionRequest
    ) -> CreatePositionResponse:
        """
        Create a new position in the account.
        """
        async with self._limiter:
            response = await self.client.post(
                "positions/otc",
                json=data.model_dump(by_alias=True, mode="json", exclude_none=True),
                headers={"Version": "2"},
            )

        # Handle non-200 responses appropriately for retry logic
        if response.status_code >= 500 or response.status_code == 429:
            response.raise_for_status()

        data: dict = response.json()

        if response.status_code != 200:
            raise IGAPIError(
                message=data.get("errorCode", "Unknown error"),
                status_code=response.status_code,
                error_code=data.get("errorCode", "Unknown error"),
            )

        return CreatePositionResponse(**data)

    @ig_api_retry
    async def get_working_orders(self) -> WorkingOrdersResponse:
        """
        Retrieve working orders for the account.
        """
        async with self._limiter:
            response = await self.client.get("workingorders", headers={"Version": "2"})

        # Handle non-200 responses appropriately for retry logic
        if response.status_code >= 500 or response.status_code == 429:
            response.raise_for_status()

        data = response.json()

        if response.status_code != 200:
            raise IGAPIError(
                message=data.get("errorCode", "Unknown error"),
                status_code=response.status_code,
                error_code=data.get("errorCode"),
            )

        return WorkingOrdersResponse(**data)

    @ig_api_retry
    async def create_working_order(
        self, data: CreateWorkingOrderRequest
    ) -> CreateWorkingOrderResponse:
        """
        Create a new working order in the account.
        """
        async with self._limiter:
            response = await self.client.post(
                "workingorders/otc",
                json=data.model_dump(by_alias=True, mode="json", exclude_none=True),
                headers={"Version": "2"},
            )

        # Handle non-200 responses appropriately for retry logic
        if response.status_code >= 500 or response.status_code == 429:
            response.raise_for_status()

        data: dict = response.json()
        print(data)

        if response.status_code != 200:
            raise IGAPIError(
                message=data.get("errorCode", "Unknown error"),
                status_code=response.status_code,
                error_code=data.get("errorCode", "None"),
            )

        return CreateWorkingOrderResponse(**data)

    @ig_api_retry
    async def delete_working_order(
        self, data: DeleteWorkingOrderRequest
    ) -> DeleteWorkingOrderResponse:
        """
        Delete a working order by its deal reference.
        """
        async with self._limiter:
            response = await self.client.delete(
                f"workingorders/otc/{data.deal_id}",
                headers={"Version": "2"},
            )

        if response.status_code >= 500 or response.status_code == 429:
            response.raise_for_status()

        data = response.json()

        if response.status_code != 200:
            raise IGAPIError(
                message=data.get("errorCode", "Unknown error"),
                status_code=response.status_code,
                error_code=data.get("errorCode"),
            )

        return DeleteWorkingOrderResponse(**data)

    @ig_api_retry
    async def delete_position(
        self, data: DeletePositionRequest
    ) -> DeletePositionResponse:
        """
        Delete/close a position by its deal ID.
        """
        async with self._limiter:
            response = await self.client.delete(
                f"positions/otc/{data.deal_id}",
                headers={"Version": "1"},
            )

        if response.status_code >= 500 or response.status_code == 429:
            response.raise_for_status()

        response_data = response.json()

        if response.status_code != 200:
            raise IGAPIError(
                message=response_data.get("errorCode", "Unknown error"),
                status_code=response.status_code,
                error_code=response_data.get("errorCode"),
            )

        return DeletePositionResponse(**response_data)

    @ig_api_retry
    async def confirm_deal(self, data: ConfirmDealRequest) -> DealConfirmation:
        """
        Confirm a deal request by its deal reference.
        """
        async with self._limiter:
            response = await self.client.get(
                f"confirms/{data.deal_reference}",
                headers={"Version": "1"},
            )

        # Handle non-200 responses appropriately for retry logic
        if response.status_code >= 500 or response.status_code == 429:
            response.raise_for_status()

        data = response.json()

        if response.status_code != 200:
            raise IGAPIError(
                message=data.get("errorCode", "Unknown error"),
                status_code=response.status_code,
                error_code=data.get("errorCode"),
            )

        return DealConfirmation(**data)

    @ig_api_retry
    async def get_position_by_deal_id(
        self, data: GetPositionByDealIdRequest
    ) -> PositionData:
        """
        Get position details by deal ID.
        """
        async with self._limiter:
            response = await self.client.get(
                f"positions/{data.deal_id}",
                headers={"Version": "2"},
            )

        # Handle non-200 responses appropriately for retry logic
        if response.status_code >= 500 or response.status_code == 429:
            response.raise_for_status()

        data = response.json()

        if response.status_code != 200:
            raise IGAPIError(
                message=data.get("errorCode", "Unknown error"),
                status_code=response.status_code,
                error_code=data.get("errorCode"),
            )

        return PositionData(**data)

    @ig_api_retry
    async def get_user_quick_stats(self) -> UserQuickStats:
        """
        Get quick stats about the user account including:
        - Number of open positions
        - Number of open working orders
        - Recent activities from the last day

        This method combines multiple API calls to provide a summary dashboard view.
        """
        # Get current timestamp
        current_time = datetime.now(timezone.utc)

        # Fetch data concurrently
        positions_task = asyncio.create_task(self.get_positions())
        orders_task = asyncio.create_task(self.get_working_orders())

        # Get recent activity (last 24 hours)
        from_date = current_time - timedelta(days=1)
        history_filters = GetHistoryFilters(
            from_date=from_date,
            to_date=current_time,
            detailed=True,
            page_size=50,
        )

        history_task = asyncio.create_task(self.get_history(history_filters))

        positions_response, orders_response, history_response = await asyncio.gather(
            positions_task, orders_task, history_task
        )

        open_positions_count = len(positions_response.positions)
        open_orders_count = len(orders_response.working_orders)
        recent_activities = history_response.activities

        return UserQuickStats(
            open_positions_count=open_positions_count,
            open_orders_count=open_orders_count,
            recent_activities=recent_activities,
            stats_timestamp=current_time,
        )

    @ig_api_retry
    async def get_prices(self, params: GetPricesRequest) -> GetPricesResponse:
        """
        Returns historical prices for a particular instrument.
        Returns the most recent second-level price by default.

        Version: 3
        """
        # Build query parameters
        query_params = {
            "resolution": params.resolution,
            "max": params.max_points,
            "pageSize": params.page_size,
            "pageNumber": params.page_number,
        }

        # Add optional date parameters if provided
        if params.from_date:
            query_params["from"] = params.from_date
        if params.to_date:
            query_params["to"] = params.to_date

        async with self._limiter:
            response = await self.client.get(
                f"prices/{params.epic}",
                headers={"Version": "3"},
                params=query_params,
            )

        if response.status_code >= 500 or response.status_code == 429:
            response.raise_for_status()

        data = response.json()

        if response.status_code != 200:
            raise IGAPIError(
                status_code=response.status_code,
                error_code=data.get("errorCode", "UNKNOWN_ERROR"),
            )

        return GetPricesResponse(**data)

    @ig_api_retry
    async def _get_auth_data(self) -> AuthenticationData:
        """
        Retrieves the authentication data for the IG API session.
        """
        try:
            session = await self.get_session()
        except IGAPIError as e:
            raise IGAuthenticationError(f"Failed to get session: {e.error_code}") from e

        return AuthenticationData(
            access_token=session.oauth_token.access_token,
        )
