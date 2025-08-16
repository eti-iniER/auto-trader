from decimal import Decimal
from typing import List, Literal, Optional

from pydantic import AwareDatetime, BaseModel, Field, NaiveDatetime

# Core Type Definitions
type InstrumentType = Literal[
    "BINARY",
    "BUNGEE_CAPPED",
    "BUNGEE_COMMODITIES",
    "BUNGEE_CURRENCIES",
    "BUNGEE_INDICES",
    "COMMODITIES",
    "CURRENCIES",
    "INDICES",
    "KNOCKOUTS_COMMODITIES",
    "KNOCKOUTS_CURRENCIES",
    "KNOCKOUTS_INDICES",
    "KNOCKOUTS_SHARES",
    "OPT_COMMODITIES",
    "OPT_CURRENCIES",
    "OPT_INDICES",
    "OPT_RATES",
    "OPT_SHARES",
    "RATES",
    "SECTORS",
    "SHARES",
    "SPRINT_MARKET",
    "TEST_MARKET",
    "UNKNOWN",
]

type MarketStatus = Literal[
    "CLOSED",
    "EDITS_ONLY",
    "OFFLINE",
    "ON_AUCTION",
    "ON_AUCTION_NO_EDITS",
    "SUSPENDED",
    "TRADEABLE",
]

type Direction = Literal["BUY", "SELL"]

type OrderType = Literal["LIMIT", "MARKET", "STOP"]

type TimeInForce = Literal["GOOD_TILL_CANCELLED", "GOOD_TILL_DATE"]

type PositionOrderType = Literal["LIMIT", "MARKET", "QUOTE"]

type PositionTimeInForce = Literal["EXECUTE_AND_ELIMINATE", "FILL_OR_KILL"]

type AccountStatus = Literal["DISABLED", "ENABLED", "SUSPENDED_FROM_DEALING"]

type AccountType = Literal["CFD", "PHYSICAL", "SPREADBET"]

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

type AffectedDealStatus = Literal[
    "AMENDED", "DELETED", "FULLY_CLOSED", "OPENED", "PARTIALLY_CLOSED"
]

type DealStatus = Literal["ACCEPTED", "REJECTED"]

type PositionStatus = Literal[
    "AMENDED", "CLOSED", "DELETED", "OPEN", "PARTIALLY_CLOSED"
]

type ActivityType = Literal["POSITION", "WORKING_ORDER", "SYSTEM"]

type ReasonCode = Literal[
    "ACCOUNT_NOT_ENABLED_TO_TRADING",
    "ATTACHED_ORDER_LEVEL_ERROR",
    "ATTACHED_ORDER_TRAILING_STOP_ERROR",
    "CANNOT_CHANGE_STOP_TYPE",
    "CANNOT_REMOVE_STOP",
    "CLOSING_ONLY_TRADES_ACCEPTED_ON_THIS_MARKET",
    "CLOSINGS_ONLY_ACCOUNT",
    "CONFLICTING_ORDER",
    "CONTACT_SUPPORT_INSTRUMENT_ERROR",
    "CR_SPACING",
    "DUPLICATE_ORDER_ERROR",
    "EXCHANGE_MANUAL_OVERRIDE",
    "EXPIRY_LESS_THAN_SPRINT_MARKET_MIN_EXPIRY",
    "FINANCE_REPEAT_DEALING",
    "FORCE_OPEN_ON_SAME_MARKET_DIFFERENT_CURRENCY",
    "GENERAL_ERROR",
    "GOOD_TILL_DATE_IN_THE_PAST",
    "INSTRUMENT_NOT_FOUND",
    "INSTRUMENT_NOT_TRADEABLE_IN_THIS_CURRENCY",
    "INSUFFICIENT_FUNDS",
    "LEVEL_TOLERANCE_ERROR",
    "LIMIT_ORDER_WRONG_SIDE_OF_MARKET",
    "MANUAL_ORDER_TIMEOUT",
    "MARGIN_ERROR",
    "MARKET_CLOSED",
    "MARKET_CLOSED_WITH_EDITS",
    "MARKET_CLOSING",
    "MARKET_NOT_BORROWABLE",
    "MARKET_OFFLINE",
    "MARKET_ORDERS_NOT_ALLOWED_ON_INSTRUMENT",
    "MARKET_PHONE_ONLY",
    "MARKET_ROLLED",
    "MARKET_UNAVAILABLE_TO_CLIENT",
    "MAX_AUTO_SIZE_EXCEEDED",
    "MINIMUM_ORDER_SIZE_ERROR",
    "MOVE_AWAY_ONLY_LIMIT",
    "MOVE_AWAY_ONLY_STOP",
    "MOVE_AWAY_ONLY_TRIGGER_LEVEL",
    "NCR_POSITIONS_ON_CR_ACCOUNT",
    "OPPOSING_DIRECTION_ORDERS_NOT_ALLOWED",
    "OPPOSING_POSITIONS_NOT_ALLOWED",
    "ORDER_DECLINED",
    "ORDER_LOCKED",
    "ORDER_NOT_FOUND",
    "ORDER_SIZE_CANNOT_BE_FILLED",
    "OVER_NORMAL_MARKET_SIZE",
    "PARTIALY_CLOSED_POSITION_NOT_DELETED",
    "POSITION_ALREADY_EXISTS_IN_OPPOSITE_DIRECTION",
    "POSITION_NOT_AVAILABLE_TO_CANCEL",
    "POSITION_NOT_AVAILABLE_TO_CLOSE",
    "POSITION_NOT_FOUND",
    "REJECT_CFD_ORDER_ON_SPREADBET_ACCOUNT",
    "REJECT_SPREADBET_ORDER_ON_CFD_ACCOUNT",
    "SIZE_INCREMENT",
    "SPRINT_MARKET_EXPIRY_AFTER_MARKET_CLOSE",
    "STOP_OR_LIMIT_NOT_ALLOWED",
    "STOP_REQUIRED_ERROR",
    "STRIKE_LEVEL_TOLERANCE",
    "SUCCESS",
    "TRAILING_STOP_NOT_ALLOWED",
    "UNKNOWN",
    "WRONG_SIDE_OF_MARKET",
]


# Error Response Model
class ErrorResponse(BaseModel):
    status_code: int = Field(..., description="HTTP status code of the error")
    error_code: str = Field(
        ..., description="Error code indicating the type of error", alias="errorCode"
    )


# Account Models
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


# Authentication Models
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


# Activity and History Models
class ActivityAction(BaseModel):
    action_type: ActivityActionType = Field(
        ..., description="Type of the activity action", alias="actionType"
    )
    affected_deal_id: str = Field(
        ..., description="ID of the deal affected by the action", alias="affectedDealId"
    )


class Activity(BaseModel):
    date: NaiveDatetime = Field(..., description="Date and time of the activity")
    epic: str = Field(..., description="Epic identifier for the instrument")
    period: str = Field(..., description="Time period (e.g., DFB)")
    deal_id: str = Field(..., alias="dealId", description="Deal identifier")
    channel: ActivityChannel = Field(
        ..., description="Channel through which the activity occurred"
    )
    type: ActivityType = Field(..., description="Type of activity")
    status: DealStatus = Field(..., description="Status of the activity")
    description: str = Field(..., description="Activity description")
    details: Optional[dict] = Field(None, description="Additional activity details")


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

    class Config:
        populate_by_name = True


class Paging(BaseModel):
    next: Optional[str] = Field(None, description="Token for the next page of results")
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


# Market Data Models (Unified)
class MarketData(BaseModel):
    """Unified market data model used across positions and working orders"""

    bid: Optional[Decimal] = None
    delay_time: Optional[Decimal] = Field(None, alias="delayTime")
    epic: Optional[str] = None
    exchange_id: Optional[str] = Field(None, alias="exchangeId")
    expiry: Optional[str] = None
    high: Optional[Decimal] = None
    instrument_name: Optional[str] = Field(None, alias="instrumentName")
    instrument_type: Optional[InstrumentType] = Field(None, alias="instrumentType")
    lot_size: Optional[Decimal] = Field(None, alias="lotSize")
    low: Optional[Decimal] = None
    market_status: Optional[MarketStatus] = Field(None, alias="marketStatus")
    net_change: Optional[Decimal] = Field(None, alias="netChange")
    offer: Optional[Decimal] = None
    percentage_change: Optional[Decimal] = Field(None, alias="percentageChange")
    scaling_factor: Optional[Decimal] = Field(None, alias="scalingFactor")
    streaming_prices_available: Optional[bool] = Field(
        None, alias="streamingPricesAvailable"
    )
    update_time: Optional[str] = Field(None, alias="updateTime")
    update_time_utc: Optional[str] = Field(None, alias="updateTimeUTC")


# Position Models
class PositionDetail(BaseModel):
    """Details of a trading position"""

    contract_size: float = Field(
        ..., alias="contractSize", description="Size of the contract"
    )
    controlled_risk: bool = Field(
        ..., alias="controlledRisk", description="True if position is risk controlled"
    )
    created_date: str = Field(
        ..., alias="createdDate", description="Local date the position was opened"
    )
    created_date_utc: str = Field(
        ..., alias="createdDateUTC", description="Date the position was opened"
    )
    currency: str = Field(..., description="Position currency ISO code")
    deal_id: str = Field(..., alias="dealId", description="Deal identifier")
    deal_reference: str = Field(
        ..., alias="dealReference", description="Deal reference"
    )
    direction: Direction = Field(..., description="Position direction")
    level: float = Field(..., description="Level at which the position was opened")
    limit_level: Optional[float] = Field(
        None, alias="limitLevel", description="Limit level"
    )
    limited_risk_premium: Optional[float] = Field(
        None, alias="limitedRiskPremium", description="Limited Risk Premium"
    )
    size: float = Field(..., description="Deal size")
    stop_level: Optional[float] = Field(
        None, alias="stopLevel", description="Stop level"
    )
    trailing_step: Optional[float] = Field(
        None, alias="trailingStep", description="Trailing step size"
    )
    trailing_stop_distance: Optional[float] = Field(
        None, alias="trailingStopDistance", description="Trailing stop distance"
    )


class PositionData(BaseModel):
    """Complete position data including market information"""

    market: MarketData = Field(..., description="Market data for the position")
    position: PositionDetail = Field(..., description="Position details")


class PositionsResponse(BaseModel):
    """Response containing list of positions"""

    positions: List[PositionData] = Field(..., description="List of position data")


# Working Order Models
class WorkingOrderDetail(BaseModel):
    """Details of a working order"""

    created_date: Optional[str] = Field(None, alias="createdDate")
    created_date_utc: Optional[str] = Field(None, alias="createdDateUTC")
    currency_code: Optional[str] = Field(None, alias="currencyCode")
    deal_id: Optional[str] = Field(None, alias="dealId")
    direction: Optional[Direction] = None
    dma: Optional[bool] = None
    epic: Optional[str] = None
    good_till_date: Optional[str] = Field(None, alias="goodTillDate")
    good_till_date_iso: Optional[str] = Field(None, alias="goodTillDateISO")
    guaranteed_stop: Optional[bool] = Field(None, alias="guaranteedStop")
    limit_distance: Optional[Decimal] = Field(None, alias="limitDistance")
    limited_risk_premium: Optional[Decimal] = Field(None, alias="limitedRiskPremium")
    order_level: Optional[Decimal] = Field(None, alias="orderLevel")
    order_size: Optional[Decimal] = Field(None, alias="orderSize")
    order_type: Optional[OrderType] = Field(None, alias="orderType")
    stop_distance: Optional[Decimal] = Field(None, alias="stopDistance")
    time_in_force: Optional[TimeInForce] = Field(None, alias="timeInForce")


class WorkingOrderData(BaseModel):
    """Complete working order data including market information"""

    market_data: Optional[MarketData] = Field(None, alias="marketData")
    working_order_data: Optional[WorkingOrderDetail] = Field(
        None, alias="workingOrderData"
    )


class WorkingOrdersResponse(BaseModel):
    """Response containing list of working orders"""

    working_orders: List[WorkingOrderData] = Field(alias="workingOrders")


# Request Models for Creating Orders and Positions
class CreateWorkingOrderRequest(BaseModel):
    """Request to create a working order"""

    currency_code: str = Field(alias="currencyCode")
    deal_reference: Optional[str] = Field(None, alias="dealReference")
    direction: Direction
    epic: str
    expiry: str
    force_open: Optional[bool] = Field(None, alias="forceOpen")
    good_till_date: Optional[str] = Field(None, alias="goodTillDate")
    guaranteed_stop: bool = Field(alias="guaranteedStop")
    level: Decimal
    limit_distance: Optional[Decimal] = Field(None, alias="limitDistance")
    limit_level: Optional[Decimal] = Field(None, alias="limitLevel")
    size: int = Field(..., description="Order size")
    stop_distance: Optional[Decimal] = Field(None, alias="stopDistance")
    stop_level: Optional[Decimal] = Field(None, alias="stopLevel")
    time_in_force: Optional[TimeInForce] = Field(None, alias="timeInForce")
    type: OrderType

    class Config:
        populate_by_name = True


class CreateWorkingOrderResponse(BaseModel):
    """Response after creating a working order"""

    deal_reference: Optional[str] = Field(None, alias="dealReference")


class CreatePositionRequest(BaseModel):
    """Request to create a position"""

    currency_code: str = Field(alias="currencyCode")
    deal_reference: Optional[str] = Field(None, alias="dealReference")
    direction: Direction
    epic: str
    expiry: str
    force_open: bool = Field(alias="forceOpen")
    guaranteed_stop: bool = Field(alias="guaranteedStop")
    level: Optional[Decimal] = None
    limit_distance: Optional[Decimal] = Field(None, alias="limitDistance")
    limit_level: Optional[Decimal] = Field(None, alias="limitLevel")
    order_type: PositionOrderType = Field(alias="orderType")
    quote_id: Optional[str] = Field(None, alias="quoteId")
    size: Decimal
    stop_distance: Optional[Decimal] = Field(None, alias="stopDistance")
    stop_level: Optional[Decimal] = Field(None, alias="stopLevel")
    time_in_force: Optional[PositionTimeInForce] = Field(None, alias="timeInForce")
    trailing_stop: Optional[bool] = Field(None, alias="trailingStop")
    trailing_stop_increment: Optional[Decimal] = Field(
        None, alias="trailingStopIncrement"
    )

    class Config:
        populate_by_name = True


class CreatePositionResponse(BaseModel):
    """Response after creating a position"""

    deal_reference: Optional[str] = Field(None, alias="dealReference")


# Deal Confirmation Models
class ConfirmDealRequest(BaseModel):
    """Request to confirm a deal"""

    deal_reference: str = Field(
        ..., description="Reference of the deal to confirm", alias="dealReference"
    )

    class Config:
        populate_by_name = True


class AffectedDeal(BaseModel):
    """Information about a deal affected by a transaction"""

    deal_id: str = Field(..., alias="dealId", description="Deal identifier")
    status: AffectedDealStatus = Field(..., description="Affected deal status")


class DealConfirmation(BaseModel):
    """Confirmation details of a completed deal"""

    affected_deals: Optional[List[AffectedDeal]] = Field(
        None, alias="affectedDeals", description="List of affected deals"
    )
    date: str = Field(..., description="Transaction date")
    deal_id: str = Field(..., alias="dealId", description="Deal identifier")
    deal_reference: str = Field(
        ..., alias="dealReference", description="Deal reference"
    )
    deal_status: DealStatus = Field(..., alias="dealStatus", description="Deal status")
    direction: Direction = Field(..., description="Deal direction")
    epic: str = Field(..., description="Instrument epic identifier")
    expiry: str = Field(..., description="Instrument expiry")
    guaranteed_stop: bool = Field(
        ..., alias="guaranteedStop", description="True if guaranteed stop"
    )
    level: Decimal = Field(..., description="Level")
    limit_distance: Optional[Decimal] = Field(
        None, alias="limitDistance", description="Limit distance"
    )
    limit_level: Optional[Decimal] = Field(
        None, alias="limitLevel", description="Limit level"
    )
    profit: Decimal = Field(..., description="Profit")
    profit_currency: str = Field(
        ..., alias="profitCurrency", description="Profit currency"
    )
    reason: ReasonCode = Field(
        ...,
        description="Describes the error (or success) condition for the specified trading operation",
    )
    size: Decimal = Field(..., description="Size")
    status: PositionStatus = Field(..., description="Position status")
    stop_distance: Optional[Decimal] = Field(
        None, alias="stopDistance", description="Stop distance"
    )
    stop_level: Optional[Decimal] = Field(
        None, alias="stopLevel", description="Stop level"
    )
    trailing_stop: bool = Field(
        ..., alias="trailingStop", description="True if trailing stop"
    )

    class Config:
        populate_by_name = True


class DeleteWorkingOrderRequest(BaseModel):
    """Request to delete a working order"""

    deal_id: str = Field(..., description="Deal identifier", alias="dealId")

    class Config:
        populate_by_name = True


class DeleteWorkingOrderResponse(BaseModel):
    """Response after deleting a working order"""

    deal_reference: str = Field(
        ..., description="Deal reference", alias="dealReference"
    )


class UserQuickStats(BaseModel):
    """Quick stats summary for a user account"""

    open_positions_count: int = Field(
        ..., description="Number of currently open positions"
    )
    open_orders_count: int = Field(..., description="Number of open working orders")
    recent_activities: List[Activity] = Field(
        ..., description="Recent account activities from the last day"
    )
    stats_timestamp: AwareDatetime = Field(
        ..., description="Timestamp when these stats were generated"
    )
