from datetime import date, datetime, timedelta, timezone
from enum import Enum
from typing import Optional, Tuple

from app.api.schemas.webhook import WebhookPayload
from app.clients.ig.client import IGClient
from app.clients.ig.exceptions import IGAPIError, IGAuthenticationError
from app.db.crud import (
    get_instrument_by_market_and_symbol,
    get_most_recent_order_for_instrument,
    get_open_orders_for_user,
    get_orders_for_user,
    get_user_by_webhook_secret,
)
from app.db.deps import get_db_context
from app.db.enums import UserSettingsMode
from app.db.models import Instrument, Order, User
from app.services.logging import log_message
from app.services.trading.payload_parser import parse_message_fields
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

# Constants
SECONDS_PER_HOUR = 3600


class ValidationError(Enum):
    """Validation error codes for webhook payload validation."""

    INVALID_WEBHOOK_SECRET = "INVALID_WEBHOOK_SECRET"
    MISMATCHED_DEMO_WEBHOOK_SECRET = "MISMATCHED_DEMO_WEBHOOK_SECRET"
    MISMATCHED_LIVE_WEBHOOK_SECRET = "MISMATCHED_LIVE_WEBHOOK_SECRET"
    MAX_ALERT_AGE_EXCEEDED = "MAX_ALERT_AGE_EXCEEDED"
    INSTRUMENT_NOT_FOUND = "INSTRUMENT_NOT_FOUND"
    ORDER_CREATION_TOO_SOON = "ORDER_CREATION_TOO_SOON"
    ALERT_ON_DIVIDEND_DATE = "ALERT_ON_DIVIDEND_DATE"
    POSITION_ALREADY_EXISTS = "POSITION_ALREADY_EXISTS"
    WORKING_ORDER_ALREADY_EXISTS = "WORKING_ORDER_ALREADY_EXISTS"
    MAXIMUM_OPEN_POSITIONS_AND_PENDING_ORDERS_EXCEEDED = (
        "MAXIMUM_OPEN_POSITIONS_AND_PENDING_ORDERS_EXCEEDED"
    )


async def _log_validation_error(
    title: str,
    description: str,
    user_id: int,
    payload: WebhookPayload,
    extra_data: dict = None,
) -> None:
    """Helper function to log validation errors consistently."""
    log_data = {"payload": payload.model_dump(mode="json")}
    if extra_data:
        log_data.update(extra_data)

    await log_message(title, description, "alert", user_id, log_data)


async def _validate_user_exists(
    payload: WebhookPayload, db
) -> Tuple[bool, Optional[str], Optional[User]]:
    """Validate that a user exists for the given webhook secret."""
    user = await get_user_by_webhook_secret(db, payload.secret)

    if not user:
        return False, ValidationError.INVALID_WEBHOOK_SECRET.value, None

    return True, None, user


async def _validate_webhook_secret(
    payload: WebhookPayload, user: User
) -> Tuple[bool, Optional[str]]:
    """Validate webhook secret matches user's configured secret."""
    expected_secret = (
        user.settings.demo_webhook_secret
        if user.settings.mode == UserSettingsMode.DEMO
        else user.settings.live_webhook_secret
    )

    if payload.secret != expected_secret:
        error_code = (
            ValidationError.MISMATCHED_DEMO_WEBHOOK_SECRET.value
            if user.settings.mode == UserSettingsMode.DEMO
            else ValidationError.MISMATCHED_LIVE_WEBHOOK_SECRET.value
        )

        title = f"Mismatched {'demo' if user.settings.mode == UserSettingsMode.DEMO else 'live'} webhook secret"
        description = f"Alert has been rejected due to mismatched {'demo' if user.settings.mode == UserSettingsMode.DEMO else 'live'} webhook secret"

        await _log_validation_error(
            title,
            description,
            user.id,
            payload,
            {
                "expected_secret": expected_secret,
                "received_secret": payload.secret,
            },
        )

        return False, error_code

    return True, None


async def _validate_alert_age(
    payload: WebhookPayload, user: User
) -> Tuple[bool, Optional[str]]:
    """Validate alert is not too old based on user settings."""
    if not user.settings.enforce_maximum_alert_age_in_seconds:
        return True, None

    payload_age = datetime.now(timezone.utc) - payload.timestamp
    payload_age_seconds = int(payload_age.total_seconds())

    if payload_age_seconds > user.settings.maximum_alert_age_in_seconds:
        await _log_validation_error(
            "Maximum alert age exceeded",
            "Alert has been rejected due to exceeding maximum age",
            user.id,
            payload,
            {
                "maximum_alert_age_in_seconds": user.settings.maximum_alert_age_in_seconds,
                "payload_age_seconds": payload_age_seconds,
            },
        )

        return False, ValidationError.MAX_ALERT_AGE_EXCEEDED.value

    return True, None


async def _validate_instrument_exists(
    payload: WebhookPayload, user: User, db
) -> Tuple[bool, Optional[str], Optional[Instrument]]:
    """Validate that the instrument exists in the database."""

    market_and_symbol = parse_message_fields(payload.message).get(
        "market_and_symbol", payload.market_and_symbol
    )
    instrument = await get_instrument_by_market_and_symbol(db, market_and_symbol, user)

    if not instrument:
        await _log_validation_error(
            "Instrument not found",
            "Alert has been rejected due to missing or incorrect instrument",
            user.id,
            payload,
            {"market_and_symbol": market_and_symbol},
        )

        return False, ValidationError.INSTRUMENT_NOT_FOUND.value, None

    return True, None, instrument


async def _validate_trade_cooldown_timing(
    payload: WebhookPayload, user: User, instrument: Instrument, db
) -> Tuple[bool, Optional[str]]:
    """Validate that enough time has passed since the last trade for this instrument."""

    existing_order = await get_most_recent_order_for_instrument(db, instrument.id)

    if not existing_order:
        return True, None

    time_since_order = datetime.now(timezone.utc) - existing_order.created_at
    required_timedelta = timedelta(
        hours=user.settings.instrument_trade_cooldown_period_in_hours
    )

    if time_since_order < required_timedelta:
        hours_since_order = time_since_order.total_seconds() / SECONDS_PER_HOUR

        await _log_validation_error(
            "Order creation too soon after previous order",
            "Alert has been ignored due to insufficient cooldown period since last order for this instrument",
            user.id,
            payload,
            {
                "instrument_id": str(instrument.id),
                "existing_order_id": str(existing_order.id),
                "existing_order_created_at": existing_order.created_at.isoformat(),
                "hours_since_order": hours_since_order,
                "minimum_hours_required": user.settings.instrument_trade_cooldown_period_in_hours,
            },
        )

        return False, ValidationError.ORDER_CREATION_TOO_SOON.value

    return True, None


async def _validate_dividend_date(
    payload: WebhookPayload, user: User, instrument: Instrument
) -> Tuple[bool, Optional[str]]:
    """Validate that trading is allowed on dividend dates."""
    if not user.settings.avoid_dividend_dates:
        return True, None

    if not instrument.next_dividend_date:
        return True, None

    if instrument.next_dividend_date.date() == date.today():
        await _log_validation_error(
            "Alert received on dividend date",
            "Alert has been ignored due to being received on the dividend date",
            user.id,
            payload,
            {"dividend_date": instrument.next_dividend_date.isoformat()},
        )

        return False, ValidationError.ALERT_ON_DIVIDEND_DATE.value

    return True, None


async def _validate_position_or_working_order_does_not_exist(
    payload: WebhookPayload, user: User, instrument: Instrument
) -> Tuple[bool, Optional[str]]:
    """Validate that a position or working order does not already exist for the instrument's IG epic"""
    if not instrument.ig_epic:
        # If there's no IG epic, we can't check positions, so allow the trade
        return True, None

    try:
        with IGClient.create_for_user(user) as ig_client:
            positions_response = ig_client.get_positions()

            # Check if any existing position matches the instrument's IG epic
            for position_data in positions_response.positions:
                if position_data.market.epic == instrument.ig_epic:
                    await _log_validation_error(
                        "Position already exists for instrument",
                        "Alert has been rejected because a position already exists for this instrument",
                        user.id,
                        payload,
                        {
                            "instrument_id": str(instrument.id),
                            "ig_epic": instrument.ig_epic,
                            "existing_deal_id": position_data.position.deal_id,
                            "existing_position_size": str(position_data.position.size),
                            "existing_position_direction": position_data.position.direction,
                        },
                    )

                    return False, ValidationError.POSITION_ALREADY_EXISTS.value

            # Check if any working order exists for the same instrument
            working_orders_response = ig_client.get_working_orders()

            for working_order in working_orders_response.working_orders:
                if (
                    working_order.working_order_data
                    and working_order.working_order_data.epic == instrument.ig_epic
                ):
                    await _log_validation_error(
                        "Working order already exists for instrument",
                        "Alert has been rejected because a working order already exists for this instrument",
                        user.id,
                        payload,
                        {
                            "instrument_id": str(instrument.id),
                            "ig_epic": instrument.ig_epic,
                            "existing_deal_id": working_order.working_order_data.deal_id,
                            "existing_order_size": str(
                                working_order.working_order_data.order_size
                            ),
                            "existing_order_direction": working_order.working_order_data.direction,
                            "existing_order_type": working_order.working_order_data.order_type,
                        },
                    )

                    return False, ValidationError.WORKING_ORDER_ALREADY_EXISTS.value

    except (IGAPIError, IGAuthenticationError) as e:
        # If we can't connect to IG API, log the error but allow the trade to proceed
        # This prevents IG API issues from blocking all trades
        await _log_validation_error(
            "Unable to check existing positions and working orders",
            f"Failed to check existing positions and working orders due to IG API error: {str(e)}. Trade will proceed.",
            user.id,
            payload,
            {
                "instrument_id": str(instrument.id),
                "ig_epic": instrument.ig_epic,
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
        )

    return True, None


async def _validate_maximum_pending_orders(
    user: User, payload: WebhookPayload, db
) -> Tuple[bool, Optional[str]]:
    """Validate that the user has not exceeded their maximum pending orders."""
    if not user.settings.enforce_maximum_open_positions:
        return True, None

    pending_orders_count = len(await get_open_orders_for_user(db, user.id))

    if pending_orders_count >= user.settings.maximum_open_positions:
        await _log_validation_error(
            "Maximum open positions exceeded",
            "Alert has been ignored due to exceeding maximum open positions",
            user.id,
            payload,
            {"maximum_open_positions": user.settings.maximum_open_positions},
        )

        return False, "MAXIMUM_PENDING_ORDERS_EXCEEDED"

    return True, None


async def _validate_maximum_open_positions_and_pending_orders(
    payload: WebhookPayload, user: User, db
) -> Tuple[bool, Optional[str]]:
    """Validate that the user has not exceeded their maximum open positions and pending orders combined."""
    if not user.settings.enforce_maximum_open_positions_and_pending_orders:
        return True, None

    # Get all orders for the user
    all_orders = await get_orders_for_user(db, user.id)
    pending_orders_count = len([order for order in all_orders if order.is_open == True])
    open_positions_count = len(all_orders) - pending_orders_count

    total_count = pending_orders_count + open_positions_count

    if total_count >= user.settings.maximum_open_positions_and_pending_orders:
        await _log_validation_error(
            "Maximum open positions and pending orders exceeded",
            "Alert has been ignored due to exceeding maximum open positions and pending orders",
            user.id,
            payload,
            {
                "maximum_open_positions_and_pending_orders": user.settings.maximum_open_positions_and_pending_orders,
                "current_pending_orders": pending_orders_count,
                "current_open_positions": open_positions_count,
                "total_count": total_count,
            },
        )

        return (
            False,
            ValidationError.MAXIMUM_OPEN_POSITIONS_AND_PENDING_ORDERS_EXCEEDED.value,
        )

    return True, None


async def validate_webhook_payload(
    payload: WebhookPayload,
) -> Tuple[bool, Optional[str]]:
    """
    Validate incoming webhook payload against various business rules.

    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_code)
    """
    async with get_db_context() as db:
        # Validate user exists
        is_valid, error_code, user = await _validate_user_exists(payload, db)
        if not is_valid:
            return is_valid, error_code

        # Validate webhook secret
        is_valid, error_code = await _validate_webhook_secret(payload, user)
        if not is_valid:
            return is_valid, error_code

        # Validate alert age
        is_valid, error_code = await _validate_alert_age(payload, user)
        if not is_valid:
            return is_valid, error_code

        # Validate instrument exists
        is_valid, error_code, instrument = await _validate_instrument_exists(
            payload, user, db
        )
        if not is_valid:
            return is_valid, error_code

        # Validate maximum open positions
        is_valid, error_code = await _validate_maximum_pending_orders(user, payload, db)
        if not is_valid:
            return is_valid, error_code

        # Validate maximum open positions and pending orders combined
        (
            is_valid,
            error_code,
        ) = await _validate_maximum_open_positions_and_pending_orders(payload, user, db)
        if not is_valid:
            return is_valid, error_code

        # Validate trade cooldown timing
        is_valid, error_code = await _validate_trade_cooldown_timing(
            payload, user, instrument, db
        )
        if not is_valid:
            return is_valid, error_code

        # Validate position does not already exist
        is_valid, error_code = await _validate_position_or_working_order_does_not_exist(
            payload, user, instrument
        )
        if not is_valid:
            return is_valid, error_code

        # Validate dividend date constraints
        is_valid, error_code = await _validate_dividend_date(payload, user, instrument)
        if not is_valid:
            return is_valid, error_code

    return True, None
