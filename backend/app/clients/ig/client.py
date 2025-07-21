import logging
from typing import List, Optional

import httpx
from app.config import settings

from .exceptions import IGAPIError, IGAuthenticationError
from .types import *

logger = logging.getLogger(__name__)


class OAuth2(httpx.Auth):
    requires_response_body = True

    def __init__(self, get_auth_data_func):
        self._get_auth_data_func = get_auth_data_func
        self.auth_data: Optional[AuthenticationData] = None

    def auth_flow(self, request):
        if not self.auth_data:
            self.auth_data = self._get_auth_data_func()

        request.headers["Authorization"] = f"Bearer {self.auth_data.access_token}"
        request.headers["Ig-Account-Id"] = self.auth_data.account_id
        response = yield request

        if response.status_code == 401:
            self.auth_data = self._get_auth_data_func()
            retry_request = request.copy()
            retry_request.headers["Authorization"] = (
                f"Bearer {self.auth_data.access_token}"
            )
            retry_request.headers["Ig-Account-Id"] = self.auth_data.account_id
            yield retry_request


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
        ) as raw_client:
            response = raw_client.post(
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
