import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

import httpx
from aiocache import caches, RedisCache
from aiolimiter import AsyncLimiter
from app.config import settings
from app.db.enums import UserSettingsMode
from app.db.models import User
from fastapi import HTTPException, status

from .authentication import OAuth2
from .caching import cache_client_request
from .exceptions import IGAPIError, IGAuthenticationError, MissingCredentialsError
from .logging import async_request_hook, async_response_hook
from .retries import ig_api_retry
from .types import *

logger = logging.getLogger(__name__)

POSITIONS_AND_WORKING_ORDERS_CACHE_TTL = 5  # seconds


class IGClient:
    # Class-level cache for storing client instances
    _client_cache: RedisCache = caches.get("ig_clients")

    # Class-level cache for per-user rate limiters
    _user_limiters: Dict[str, AsyncLimiter] = {}

    def __init__(
        self,
        username: str,
        password: str,
        account_id: str,
        api_key: str,
        user_id: str,
        base_url: str = settings.IG_DEMO_API_BASE_URL,
        rpm_limit: int = settings.IG_API_MAX_REQUESTS_PER_MINUTE,
        managed_by_cache: bool = False,
        cache_key: Optional[str] = None,
    ):
        self.username = username
        self.password = password
        self.api_key = api_key
        self.base_url = base_url
        self.account_id = account_id
        self.user_id = user_id
        # Whether this client instance lifecycle is managed by the class-level cache
        self._managed_by_cache = managed_by_cache
        self._cache_key = cache_key
        # Get or create a rate limiter for this specific user
        self._limiter = self._get_user_limiter(str(user_id), rpm_limit)

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
            timeout=httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=30.0),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=40),
            event_hooks={
                "request": [async_request_hook],
                "response": [async_response_hook],
            },
        )

    @classmethod
    def _get_user_limiter(cls, user_id: str, rpm_limit: int) -> AsyncLimiter:
        """Get or create a rate limiter for a specific user.
        Note: if a limiter already exists for the user, its rate will not be updated by subsequent calls.
        """
        limiter = cls._user_limiters.get(user_id)
        if limiter is None:
            limiter = cls._user_limiters.setdefault(
                user_id, AsyncLimiter(max_rate=rpm_limit, time_period=60)
            )
        return limiter

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
        cache_key = f":user:{user.id}:mode:{user_mode}"

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

        if not all([api_key, username, password, account_id]):
            mode_str = user.settings.mode.value.lower()
            logger.error(f"Incomplete {mode_str} IG credentials for user {user.id}")
            raise MissingCredentialsError(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=f"Missing {mode_str} IG credentials. Please set API key, username, password, and account ID.",
            )

        client = cls(
            username=username,
            password=password,
            api_key=api_key,
            base_url=base_url,
            account_id=account_id,
            user_id=str(user.id),
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
            # Remove the per-user limiter to prevent unbounded growth if not reused
            removed = cls._user_limiters.pop(str(user.id), None)
            if removed is not None:
                logger.debug(
                    f"Removed rate limiter for user {user.id} after cache invalidation"
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
            # Also clear all per-user limiters
            cls._user_limiters.clear()
            logger.info("Cleared all IG client per-user rate limiters")
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
            timeout=httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=30.0),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=40),
            event_hooks={
                "request": [async_request_hook],
                "response": [async_response_hook],
            },
        ) as client:
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

            if not response.is_success:
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

    def _safe_json(self, response: httpx.Response) -> dict:
        try:
            if (
                response.headers.get("Content-Type", "").startswith("application/json")
                and response.content
            ):
                return response.json()
        except Exception as e:
            logger.debug(f"Response JSON parse error: {e}")
        return {}

    @ig_api_retry
    async def get_history(self, filters: GetHistoryFilters) -> GetHistoryResponse:
        """
        Retrieves the historical data for the account.
        """
        response = await self.client.get(
            "history/activity",
            params=filters.model_dump(by_alias=True, mode="json", exclude_none=True),
        )

        # Handle non-200 responses appropriately for retry logic
        if response.status_code >= 500 or response.status_code == 429:
            response.raise_for_status()

        if not response.is_success:
            data = self._safe_json(response)
            raise IGAPIError(
                message=data.get("errorCode", "Unknown error"),
                status_code=response.status_code,
                error_code=data.get("errorCode"),
            )

        data = self._safe_json(response)
        return GetHistoryResponse(**data)

    @cache_client_request(ttl=POSITIONS_AND_WORKING_ORDERS_CACHE_TTL)
    @ig_api_retry
    async def get_positions(self) -> PositionsResponse:
        """
        Retrieve open positions for the account.
        """
        response = await self.client.get("positions", headers={"Version": "2"})

        # Handle non-200 responses appropriately for retry logic
        if response.status_code >= 500 or response.status_code == 429:
            response.raise_for_status()

        if not response.is_success:
            data = self._safe_json(response)
            raise IGAPIError(
                message=data.get("errorCode", "Unknown error"),
                status_code=response.status_code,
                error_code=data.get("errorCode"),
            )

        data = self._safe_json(response)
        return PositionsResponse(**data)

    @ig_api_retry
    async def create_position(
        self, data: CreatePositionRequest
    ) -> CreatePositionResponse:
        """
        Create a new position in the account.
        """
        response = await self.client.post(
            "positions/otc",
            json=data.model_dump(by_alias=True, mode="json", exclude_none=True),
            headers={"Version": "2"},
        )

        # Handle non-200 responses appropriately for retry logic
        if response.status_code >= 500 or response.status_code == 429:
            response.raise_for_status()

        if not response.is_success:
            err = self._safe_json(response)
            raise IGAPIError(
                message=err.get("errorCode", "Unknown error"),
                status_code=response.status_code,
                error_code=err.get("errorCode", "Unknown error"),
            )

        data_parsed: dict = self._safe_json(response)
        return CreatePositionResponse(**data_parsed)

    @cache_client_request(ttl=POSITIONS_AND_WORKING_ORDERS_CACHE_TTL)
    @ig_api_retry
    async def get_working_orders(self) -> WorkingOrdersResponse:
        """
        Retrieve working orders for the account.
        """
        response = await self.client.get("workingorders", headers={"Version": "2"})

        # Handle non-200 responses appropriately for retry logic
        if response.status_code >= 500 or response.status_code == 429:
            response.raise_for_status()

        if not response.is_success:
            data = self._safe_json(response)
            raise IGAPIError(
                message=data.get("errorCode", "Unknown error"),
                status_code=response.status_code,
                error_code=data.get("errorCode"),
            )

        data = self._safe_json(response)
        return WorkingOrdersResponse(**data)

    @ig_api_retry
    async def create_working_order(
        self, data: CreateWorkingOrderRequest
    ) -> CreateWorkingOrderResponse:
        """
        Create a new working order in the account.
        """
        response = await self.client.post(
            "workingorders/otc",
            json=data.model_dump(by_alias=True, mode="json", exclude_none=True),
            headers={"Version": "2"},
        )

        # Handle non-200 responses appropriately for retry logic
        if response.status_code >= 500 or response.status_code == 429:
            response.raise_for_status()

        if not response.is_success:
            err = self._safe_json(response)
            raise IGAPIError(
                message=err.get("errorCode", "Unknown error"),
                status_code=response.status_code,
                error_code=err.get("errorCode", "None"),
            )

        data_parsed: dict = self._safe_json(response)
        return CreateWorkingOrderResponse(**data_parsed)

    @ig_api_retry
    async def delete_working_order(
        self, data: DeleteWorkingOrderRequest
    ) -> DeleteWorkingOrderResponse:
        """
        Delete a working order by its deal reference.
        """
        response = await self.client.delete(
            f"workingorders/otc/{data.deal_id}",
            headers={"Version": "2"},
        )

        if response.status_code >= 500 or response.status_code == 429:
            response.raise_for_status()

        if not response.is_success:
            data = self._safe_json(response)
            raise IGAPIError(
                message=data.get("errorCode", "Unknown error"),
                status_code=response.status_code,
                error_code=data.get("errorCode"),
            )

        data = self._safe_json(response)
        return DeleteWorkingOrderResponse(**data)

    @ig_api_retry
    async def delete_position(
        self, data: DeletePositionRequest
    ) -> DeletePositionResponse:
        """
        Delete/close a position by its deal ID.
        """
        response = await self.client.delete(
            f"positions/otc/{data.deal_id}",
            headers={"Version": "1"},
        )

        if response.status_code >= 500 or response.status_code == 429:
            response.raise_for_status()

        if not response.is_success:
            response_data = self._safe_json(response)
            raise IGAPIError(
                message=response_data.get("errorCode", "Unknown error"),
                status_code=response.status_code,
                error_code=response_data.get("errorCode"),
            )

        response_data = self._safe_json(response)
        return DeletePositionResponse(**response_data)

    @ig_api_retry
    async def confirm_deal(self, data: ConfirmDealRequest) -> DealConfirmation:
        """
        Confirm a deal request by its deal reference.
        """
        response = await self.client.get(
            f"confirms/{data.deal_reference}",
            headers={"Version": "1"},
        )

        # Handle non-200 responses appropriately for retry logic
        if response.status_code >= 500 or response.status_code == 429:
            response.raise_for_status()

        if not response.is_success:
            data = self._safe_json(response)
            raise IGAPIError(
                message=data.get("errorCode", "Unknown error"),
                status_code=response.status_code,
                error_code=data.get("errorCode"),
            )

        data = self._safe_json(response)
        return DealConfirmation(**data)

    @ig_api_retry
    async def get_position_by_deal_id(
        self, data: GetPositionByDealIdRequest
    ) -> PositionData:
        """
        Get position details by deal ID.
        """
        response = await self.client.get(
            f"positions/{data.deal_id}",
            headers={"Version": "2"},
        )

        # Handle non-200 responses appropriately for retry logic
        if response.status_code >= 500 or response.status_code == 429:
            response.raise_for_status()

        if not response.is_success:
            data = self._safe_json(response)
            raise IGAPIError(
                message=data.get("errorCode", "Unknown error"),
                status_code=response.status_code,
                error_code=data.get("errorCode"),
            )

        data = self._safe_json(response)
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

        # Drop None values
        query_params = {k: v for k, v in query_params.items() if v is not None}

        # Add optional date parameters if provided
        if params.from_date:
            query_params["from"] = (
                params.from_date.isoformat()
                if isinstance(params.from_date, datetime)
                else params.from_date
            )
        if params.to_date:
            query_params["to"] = (
                params.to_date.isoformat()
                if isinstance(params.to_date, datetime)
                else params.to_date
            )

        response = await self.client.get(
            f"prices/{params.epic}",
            headers={"Version": "3"},
            params=query_params,
        )

        if response.status_code >= 500 or response.status_code == 429:
            response.raise_for_status()

        if not response.is_success:
            err = self._safe_json(response)
            raise IGAPIError(
                status_code=response.status_code,
                error_code=err.get("errorCode", "UNKNOWN_ERROR"),
            )

        data = self._safe_json(response)
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
