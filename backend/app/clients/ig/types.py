from decimal import Decimal
from typing import List, Literal, Optional

from pydantic import AwareDatetime, BaseModel, Field


class ErrorResponse(BaseModel):
    status_code: int = Field(..., description="HTTP status code of the error")
    error_code: str = Field(
        ..., description="Error code indicating the type of error", alias="errorCode"
    )


type AccountStatus = Literal["DISABLED", "ENABLED", "SUSPENDED_FROM_DEALING"]
type AccountType = Literal["CFD", "PHYSICAL", "SPREADBET"]


class AccountBalance(BaseModel):
    available: Decimal = Field(..., description="Available balance for trading")
    balance: Decimal = Field(..., description="Total balance in the account")
    deposit: Decimal = Field(..., description="Deposit amount in the account")
    profit_loss: Decimal = Field(
        ..., description="Profit or loss in the account", alias="profitLoss"
    )


class Account(BaseModel):
    account_alias: str = Field(
        ..., description="Alias of the account", alias="accountAlias"
    )
    account_id: str = Field(
        ..., description="Unique identifier for the account", alias="accountId"
    )
    account_name: str = Field(
        ..., description="Name of the account", alias="accountName"
    )
    status: AccountStatus = Field(
        ..., description="Current status of the account", alias="status"
    )
    account_type: AccountType = Field(
        ..., description="Type of the account", alias="accountType"
    )
    can_transfer_from: bool = Field(
        ...,
        description="Indicates if funds can be transferred from this account",
        alias="canTransferFrom",
    )
    can_transfer_to: bool = Field(
        ...,
        description="Indicates if funds can be transferred to this account",
        alias="canTransferTo",
    )
    currency: str = Field(..., description="Currency of the account", alias="currency")
    preferred: bool = Field(
        ..., description="Indicates if this is the preferred account", alias="preferred"
    )


type ActivityChannel = Literal[
    "DEALER", "MOBILE", "PUBLIC_FIX_API", "PUBLIC_WEB_API", "SYSTEM", "WEB"
]


type ActivityActionType = Literal[
    "LIMIT_ORDER_AMENDED",
    "LIMIT_ORDER_DELETED",
    "LIMIT_ORDER_FILLED",
    "LIMIT_ORDER_OPENED",
    "LIMIT_ORDER_ROLLED",
    "POSITION_CLOSED",
    "POSITION_DELETED",
    "POSITION_OPENED",
    "POSITION_PARTIALLY_CLOSED",
    "POSITION_ROLLED",
    "STOP_LIMIT_AMENDED",
    "STOP_ORDER_AMENDED",
    "STOP_ORDER_DELETED",
    "STOP_ORDER_FILLED",
    "STOP_ORDER_OPENED",
    "STOP_ORDER_ROLLED",
    "UNKNOWN",
    "WORKING_ORDER_DELETED",
]


class ActivityAction(BaseModel):
    action_type: ActivityActionType = Field(
        ..., description="Type of the activity action", alias="actionType"
    )
    affected_deal_id: str = Field(
        ..., description="ID of the deal affected by the action", alias="affectedDealId"
    )


class Activity(BaseModel):
    channel: ActivityChannel = Field(
        ..., description="Channel through which the activity occurred"
    )
    date: AwareDatetime = Field(..., description="Date and time of the activity")


class OauthToken(BaseModel):
    access_token: str = Field(..., description="Access token for authentication")
    refresh_token: str = Field(..., description="Refresh token for renewing access")
    scope: str = Field(..., description="Scope of the access token")
    token_type: str = Field(..., description="Type of the token, e.g., Bearer")
    expires_in: str = Field(..., description="Expiration time of the token in seconds")


class GetSessionResponse(BaseModel):
    client_id: str = Field(..., description="Client ID", alias="clientId")
    account_id: str = Field(..., description="Account ID", alias="accountId")
    timezone_offset: int = Field(
        ..., description="Timezone offset in minutes", alias="timezoneOffset"
    )
    lightstreamer_endpoint: str = Field(
        ..., description="Endpoint for Lightstreamer", alias="lightstreamerEndpoint"
    )
    oauth_token: OauthToken = Field(
        ..., description="OAuth token for authentication", alias="oauthToken"
    )


class AuthenticationData(BaseModel):
    access_token: str = Field(..., description="Access token for the session")
    account_id: str = Field(
        ..., description="ID of the account associated with the session"
    )


class GetHistoryFilters(BaseModel):
    from_date: AwareDatetime = Field(
        ..., description="Start date for the history filter", alias="from"
    )
    to_date: Optional[AwareDatetime] = Field(
        None, description="End date for the history filter", alias="to"
    )
    detailed: bool = Field(
        False, description="Whether to include detailed history information"
    )
    deal_id: Optional[str] = Field(
        None, description="Specific deal ID to filter the history", alias="dealId"
    )
    filter: Optional[str] = Field(
        None, description="Filter string to apply to the history query"
    )
    page_size: int = Field(
        100, description="Number of records to return per page", alias="pageSize"
    )


class Paging(BaseModel):
    next: str = Field(..., description="Token for the next page of results")
    size: int = Field(..., description="Number of records per page")


class GetHistoryMetadata(BaseModel):
    paging: Paging = Field(
        ..., description="Paging information for the history results"
    )


class GetHistoryResponse(BaseModel):
    activities: List[Activity] = Field(
        ..., description="List of activities in the history", alias="activities"
    )
    metadata: GetHistoryMetadata = Field(
        ..., description="Metadata about the history results", alias="metadata"
    )


class Price(BaseModel):
    bid: Decimal = Field(..., description="Bid price")
    ask: Decimal = Field(..., description="Ask price")
    last_traded: Optional[Decimal] = Field(
        None, description="Last traded price", alias="lastTraded"
    )


class Position(BaseModel):
    deal_reference: str = Field(
        ..., description="Deal reference identifier", alias="dealReference"
    )
    epic: str = Field(..., description="Instrument epic identifier", alias="epic")
    direction: Literal["BUY", "SELL"] = Field(
        ..., description="Position direction", alias="direction"
    )
    size: Decimal = Field(..., description="Position size", alias="size")
    level: Decimal = Field(..., description="Entry level price", alias="level")
    limit_level: Optional[Decimal] = Field(
        None, description="Limit order level", alias="limitLevel"
    )
    stop_level: Optional[Decimal] = Field(
        None, description="Stop order level", alias="stopLevel"
    )
    trailing_step: Optional[Decimal] = Field(
        None, description="Trailing step distance", alias="trailingStep"
    )
    trailing_stop_distance: Optional[Decimal] = Field(
        None, description="Trailing stop distance", alias="trailingStopDistance"
    )
    price: Optional[Price] = Field(
        None, description="Current price snapshot at time of response", alias="price"
    )


class PositionsResponse(BaseModel):
    positions: List[Position] = Field(
        ..., description="List of open positions", alias="positions"
    )
