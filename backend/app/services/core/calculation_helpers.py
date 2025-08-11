from decimal import Decimal
from typing import Literal

type SignalDirection = Literal["BUY", "SELL"]
TWO_DECIMAL_PLACES = Decimal("0.01")
INTEGER = Decimal("1")


def calculate_limit_price(
    direction: SignalDirection,
    open_price: Decimal,
    opening_price_multiple_percentage: Decimal,
) -> Decimal:
    if direction == "SELL":
        return open_price * opening_price_multiple_percentage
    elif direction == "BUY":
        return open_price / opening_price_multiple_percentage


def calculate_bet_size(limit_price: Decimal, size: int):
    return max(1, int((size / limit_price).quantize(INTEGER, rounding="ROUND_HALF_UP")))


def calculate_profit_target_price(
    atr_profit_target_period: int, atrs: list[Decimal], atr_profit_multiple_percentage
) -> Decimal:
    atr_to_use = atrs[atr_profit_target_period - 1]
    profit_target_price = atr_to_use * (atr_profit_multiple_percentage / 100)
    return profit_target_price.quantize(TWO_DECIMAL_PLACES, rounding="ROUND_HALF_UP")


def calculate_stop_loss_price(
    atr_stop_loss_period: int,
    atrs: list[Decimal],
    atr_stop_loss_multiple_percentage: Decimal,
) -> Decimal:
    atr_to_use = atrs[atr_stop_loss_period - 1]
    stop_loss_price = atr_to_use * (atr_stop_loss_multiple_percentage / 100)
    return stop_loss_price.quantize(TWO_DECIMAL_PLACES, rounding="ROUND_HALF_UP")
