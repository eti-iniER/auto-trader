import json
import logging
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

    if hasattr(request, "content") and request.content:
        try:
            if request.headers.get("content-type", "").startswith("application/json"):
                body = json.loads(request.content.decode("utf-8"))
                logger.debug(f"Body: {json.dumps(body, indent=2)}")
            else:
                logger.debug(f"Body: {request.content.decode('utf-8')}")
        except (UnicodeDecodeError, json.JSONDecodeError):
            logger.debug(f"Body (raw): {request.content}")
    logger.debug("=== END REQUEST ===")


def log_response(response):
    """Log the incoming response details."""
    logger.debug(f"=== RESPONSE ===")
    logger.debug(f"Status Code: {response.status_code}")
    logger.debug(f"Headers: {dict(response.headers)}")

    try:
        if response.content:
            if response.headers.get("content-type", "").startswith("application/json"):
                body = response.json()
                logger.debug(f"Body: {json.dumps(body, indent=2)}")
            else:
                logger.debug(f"Body: {response.text}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        logger.debug(f"Body (raw): {response.content}")
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

            response.raise_for_status()

        data = response.json()

        if response.status_code != 200:
            raise IGAPIError(
                message=data.get("errorCode", "Unknown error"),
                status_code=response.status_code,
                error_code=data.get("errorCode"),
            )

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
