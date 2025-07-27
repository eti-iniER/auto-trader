import logging
from typing import List, Optional
import json

import httpx
from app.config import settings

from .exceptions import IGAPIError, IGAuthenticationError
from .types import *

logger = logging.getLogger(__name__)


def log_request(request):
    """Log the outgoing request details."""
    logger.debug(f"=== REQUEST ===")
    logger.debug(f"Method: {request.method}")
    logger.debug(f"URL: {request.url}")
    logger.debug(f"Headers: {dict(request.headers)}")

    # Log request body if present
    if hasattr(request, "content") and request.content:
        try:
            # Try to parse as JSON for better formatting
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

    # Log response body if present
    try:
        if response.content:
            # Try to parse as JSON for better formatting
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

    def auth_flow(self, request):
        if not self.auth_data:
            logger.debug("Getting authentication data for OAuth2")
            self.auth_data = self._get_auth_data_func()

        request.headers["Authorization"] = f"Bearer {self.auth_data.access_token}"
        request.headers["Ig-Account-Id"] = self.auth_data.account_id

        log_request(request)
        response = yield request
        log_response(response)

        if response.status_code == 401:
            logger.debug("Received 401, refreshing authentication data")
            self.auth_data = self._get_auth_data_func()
            retry_request = request.copy()
            retry_request.headers["Authorization"] = (
                f"Bearer {self.auth_data.access_token}"
            )
            retry_request.headers["Ig-Account-Id"] = self.auth_data.account_id

            logger.debug("Retrying request with new authentication")
            log_request(retry_request)
            retry_response = yield retry_request
            log_response(retry_response)


class IGClient:
    def __init__(
        self,
        username: str = settings.IG_USERNAME,
        password: str = settings.IG_PASSWORD,
        api_key: str = settings.IG_API_KEY,
        base_url: str = settings.IG_API_BASE_URL,
    ):
        self.username = username
        self.password = password
        self.api_key = api_key
        self.base_url = base_url

        self.client = httpx.Client(
            auth=OAuth2(self._get_auth_data),
            base_url=base_url,
            headers={
                "X-IG-API-KEY": self.api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Version": "3",
            },
            event_hooks={"request": [request_hook], "response": [response_hook]},
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()

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

        data = response.json()

        if response.status_code != 200:
            raise IGAPIError(
                message=data.get("errorCode", "Unknown error"),
                status_code=response.status_code,
                error_code=data.get("errorCode"),
            )

        return GetSessionResponse(**data)

    def get_history(self, filters: GetHistoryFilters) -> GetHistoryResponse:
        """
        Retrieves the historical data for the account.
        """
        response = self.client.get(
            "history/activity",
            params=filters.model_dump(by_alias=True, mode="json", exclude_none=True),
        )
        data = response.json()

        if response.status_code != 200:
            raise IGAPIError(
                message=data.get("errorCode", "Unknown error"),
                status_code=response.status_code,
                error_code=data.get("errorCode"),
            )

        return GetHistoryResponse(**data)

    def get_positions(self) -> PositionsResponse:
        """
        Retrieve open positions for the account.
        """
        response = self.client.get("positions", headers={"Version": "2"})
        data = response.json()

        if response.status_code != 200:
            raise IGAPIError(
                message=data.get("errorCode", "Unknown error"),
                status_code=response.status_code,
                error_code=data.get("errorCode"),
            )

        return PositionsResponse(**data)

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
            account_id=session.account_id,
        )
