from decimal import Decimal, localcontext
from typing import Literal

from app.db.crud import get_instrument_by_market_and_symbol, get_user_by_webhook_secret
from app.db.deps import get_db_context
from app.schemas.alert import TradingViewAlert

type Signal = Literal["UP", "DOWN"]


def calculate_limit_price(
    signal: Signal,
    open_price: Decimal,
    opening_price_multiple_percentage: Decimal,
) -> Decimal:
    if signal == "UP":
        return open_price * opening_price_multiple_percentage
    elif signal == "DOWN":
        return open_price / opening_price_multiple_percentage


def calculate_bet_size(limit_price: Decimal, size: int):
    return size / limit_price


def get_trade_direction(signal: Signal) -> str:
    return "SELL" if signal == "UP" else "BUY"


def calculate_profit_target_price(
    atr_profit_target_period: int, atrs: list[Decimal], atr_profit_multiple_percentage
) -> Decimal:
    atr_to_use = atrs[atr_profit_target_period - 1]
    return atr_to_use * (atr_profit_multiple_percentage / 100)


def calculate_stop_loss_price(
    atr_stop_loss_period: int,
    atrs: list[Decimal],
    atr_stop_loss_multiple_percentage: Decimal,
) -> Decimal:
    atr_to_use = atrs[atr_stop_loss_period - 1]
    return atr_to_use * (atr_stop_loss_multiple_percentage / 100)


async def handle_alert_for_user(alert: TradingViewAlert):
    async with get_db_context() as db:
        user = await get_user_by_webhook_secret(db, alert.secret)
        instrument = await get_instrument_by_market_and_symbol(
            db, alert.market_and_symbol
        )

    user
