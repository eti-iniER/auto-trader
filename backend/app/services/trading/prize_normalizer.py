from app.db.models import Instrument
from app.api.schemas.alert import TradingViewAlert


async def normalize_prices(
    alert: TradingViewAlert, instrument: Instrument
) -> TradingViewAlert:
    """Normalize prices in the alert based on the trading view price multiplier."""

    normalized_open_price = alert.open_price * instrument.trading_view_price_multiplier
    normalized_atrs = [
        atr * instrument.trading_view_price_multiplier for atr in alert.atrs
    ]

    return TradingViewAlert(
        market_and_symbol=alert.market_and_symbol,
        direction=alert.direction,
        message=alert.message,
        secret=alert.secret,
        timestamp=alert.timestamp,
        open_price=normalized_open_price,
        atrs=normalized_atrs,
    )
