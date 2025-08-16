import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
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

logger = logging.getLogger(__name__)


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
            # Read the content if it hasn't been read yet
            if hasattr(response, "_content") and response._content is None:
                response.read()

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
    """Hook called before sending a request."""
    log_request(request)


def response_hook(response):
    """Hook called after receiving a response."""
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
        """Make an authenticated request with retry logic."""
        if not self.auth_data:
            logger.debug("Getting authentication data for OAuth2")
            self.auth_data = self._get_auth_data_func()

        request.headers["Authorization"] = f"Bearer {self.auth_data.access_token}"
        return request

    def auth_flow(self, request):
        # Apply authentication headers with retry logic
        request = self._make_authenticated_request(request)

        log_request(request)
        response = yield request
        log_response(response)

        if response.status_code == 401:
            logger.debug("Received 401, refreshing authentication data")
            self.auth_data = self._get_auth_data_func()
            retry_request = request
            retry_request.headers["Authorization"] = (
                f"Bearer {self.auth_data.access_token}"
            )

            logger.debug("Retrying request with new authentication")
            log_request(retry_request)
            retry_response = yield retry_request
            log_response(retry_response)


class IGClient:
    def __init__(
        self,
        username: str,
        password: str,
        account_id: str,
        api_key: str,
        base_url: str = settings.IG_DEMO_API_BASE_URL,
    ):
        self.username = username
        self.password = password
        self.api_key = api_key
        self.base_url = base_url
        self.account_id = account_id

        self.client = httpx.Client(
            auth=OAuth2(self._get_auth_data),
            base_url=base_url,
            headers={
                "X-IG-API-KEY": self.api_key,
                "IG-ACCOUNT-ID": self.account_id,
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Version": "3",
            },
            event_hooks={"request": [request_hook], "response": [response_hook]},
        )

    @classmethod
    def create_for_user(cls, user: User) -> "IGClient":
        """
        Create IG client instance using user's mode-specific credentials.

        Args:
            user: The authenticated user with settings containing IG credentials

        Returns:
            IGClient: Configured IG client instance

        Raises:
            HTTPException: If user settings are missing or credentials are incomplete
        """

        if not user.settings:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User settings not found. Please configure your IG credentials.",
            )

        if user.settings.mode == UserSettingsMode.DEMO:
            api_key = user.settings.demo_api_key
            username = user.settings.demo_username
            password = user.settings.demo_password
            base_url = settings.IG_DEMO_API_BASE_URL
            account_id = user.settings.demo_account_id
        else:  # LIVE mode
            api_key = settings.live_api_key
            username = settings.live_username
            password = settings.live_password
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

        return cls(
            username=username,
            password=password,
            api_key=api_key,
            base_url=base_url,
            account_id=account_id,
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()

    @ig_api_retry
    def get_session(self) -> GetSessionResponse:
        """
        Retrieves the session information from the IG API.
        This includes the access token and other session details.
        """
        with httpx.Client(
            base_url=self.base_url,
            headers={
                "X-IG-API-KEY": self.api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Version": "3",
            },
            event_hooks={"request": [request_hook], "response": [response_hook]},
        ) as client:
            response = client.post(
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
    def get_history(self, filters: GetHistoryFilters) -> GetHistoryResponse:
        """
        Retrieves the historical data for the account.
        """
        response = self.client.get(
            "history/activity",
            params=filters.model_dump(by_alias=True, mode="json", exclude_none=True),
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
    def get_positions(self) -> PositionsResponse:
        """
        Retrieve open positions for the account.
        """
        response = self.client.get("positions", headers={"Version": "2"})

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
    def create_position(self, data: CreatePositionRequest) -> CreatePositionResponse:
        """
        Create a new position in the account.
        """
        response = self.client.post(
            "positions/otc",
            json=data.model_dump(by_alias=True, mode="json", exclude_none=True),
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

        return CreatePositionResponse(**data)

    @ig_api_retry
    def get_working_orders(self) -> WorkingOrdersResponse:
        """
        Retrieve working orders for the account.
        """
        response = self.client.get("workingorders", headers={"Version": "2"})

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
    def create_working_order(
        self, data: CreateWorkingOrderRequest
    ) -> CreateWorkingOrderResponse:
        """
        Create a new working order in the account.
        """
        response = self.client.post(
            "workingorders/otc",
            json=data.model_dump(by_alias=True, mode="json", exclude_none=True),
            headers={"Version": "2"},
        )

        # Handle non-200 responses appropriately for retry logic
        if response.status_code >= 500 or response.status_code == 429:
            response.raise_for_status()

        data = response.json()
        print(data)

        if response.status_code != 200:
            raise IGAPIError(
                message=data.get("errorCode", "Unknown error"),
                status_code=response.status_code,
                error_code=data.get("errorCode"),
            )

        return CreateWorkingOrderResponse(**data)

    @ig_api_retry
    def delete_working_order(
        self, data: DeleteWorkingOrderRequest
    ) -> DeleteWorkingOrderResponse:
        """
        Delete a working order by its deal reference.
        """
        response = self.client.delete(
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
    def get_working_order_confirmation(
        self, data: ConfirmDealRequest
    ) -> DealConfirmation:
        """
        Confirm a working order by its deal reference.
        """
        response = self.client.get(
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
    def get_user_quick_stats(self) -> UserQuickStats:
        """
        Get quick stats about the user account including:
        - Number of open positions
        - Number of open working orders
        - Recent activities from the last day

        This method combines multiple API calls to provide a summary dashboard view.
        """
        # Get current timestamp
        current_time = datetime.now(timezone.utc)

        # Get open positions
        positions_response = self.get_positions()
        open_positions_count = len(positions_response.positions)

        # Get working orders
        orders_response = self.get_working_orders()
        open_orders_count = len(orders_response.working_orders)

        # Get recent activity (last 24 hours)
        from_date = current_time - timedelta(days=1)
        history_filters = GetHistoryFilters(
            from_date=from_date,
            to_date=current_time,
            detailed=True,
            page_size=50,
        )

        history_response = self.get_history(history_filters)
        recent_activities = history_response.activities

        return UserQuickStats(
            open_positions_count=open_positions_count,
            open_orders_count=open_orders_count,
            recent_activities=recent_activities,
            stats_timestamp=current_time,
        )

    @ig_api_retry
    def _get_auth_data(self) -> AuthenticationData:
        """
        Retrieves the authentication data for the IG API session.
        """
        try:
            session = self.get_session()
        except IGAPIError as e:
            raise IGAuthenticationError(f"Failed to get session: {e.error_code}") from e

        return AuthenticationData(
            access_token=session.oauth_token.access_token,
        )
