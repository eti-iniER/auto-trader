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
    limit_price = None
    if direction == "SELL":
        limit_price = open_price * (opening_price_multiple_percentage / 100)
    else:  # direction == "BUY"
        limit_price = open_price / (opening_price_multiple_percentage / 100)
    return limit_price.quantize(TWO_DECIMAL_PLACES, rounding="ROUND_HALF_DOWN")


def calculate_bet_size(limit_price: Decimal, max_position_size: int):
    return Decimal(
        max(
            1,
            (max_position_size / limit_price).quantize(
                TWO_DECIMAL_PLACES, rounding="ROUND_HALF_DOWN"
            ),
        )
    )


def calculate_profit_target_price(
    atr_profit_target_period: int, atrs: list[Decimal], atr_profit_multiple_percentage
) -> Decimal:
    atr_to_use = atrs[atr_profit_target_period - 1]
    profit_target_price = atr_to_use * (atr_profit_multiple_percentage / 100)
    return profit_target_price.quantize(TWO_DECIMAL_PLACES, rounding="ROUND_HALF_DOWN")


def calculate_stop_loss_distance(
    atr_stop_loss_period: int,
    atrs: list[Decimal],
    atr_stop_loss_multiple_percentage: Decimal,
) -> Decimal:
    atr_to_use = atrs[atr_stop_loss_period - 1]
    stop_loss_distance = atr_to_use * (atr_stop_loss_multiple_percentage / 100)
    return stop_loss_distance.quantize(TWO_DECIMAL_PLACES, rounding="ROUND_HALF_DOWN")
