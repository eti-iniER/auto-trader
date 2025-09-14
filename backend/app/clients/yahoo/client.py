import logging
from datetime import datetime
from typing import Optional

import yfinance as yf
from pandas import Timestamp

from .types import DividendInfo, StockInfo

logger = logging.getLogger(__name__)


class YahooFinanceClient:
    """Client for Yahoo Finance API using yfinance library."""

    def __init__(self):
        """Initialize the Yahoo Finance client."""
        pass

    def get_next_dividend_date(self, symbol: str) -> Optional[datetime]:
        """
        Get the next dividend date for a given ticker symbol.

        Args:
            symbol: The ticker symbol (e.g., 'AAPL', 'MSFT')

        Returns:
            The next dividend date as a datetime object, or None if not available

        Raises:
            ValueError: If the symbol is invalid or not found
        """
        try:
            logger.debug(f"Fetching dividend date for symbol: {symbol}")

            # Create ticker object
            ticker = yf.Ticker(symbol)

            # Get dividend data
            dividends = ticker.dividends

            if dividends.empty:
                logger.info(f"No dividend data found for symbol: {symbol}")
                return None

            dividends.index[-1]

            info = ticker.info

            next_dividend_date = None

            if "exDividendDate" in info and info["exDividendDate"]:
                ex_div_timestamp = info["exDividendDate"]
                if isinstance(ex_div_timestamp, (int, float)):
                    next_dividend_date = datetime.fromtimestamp(ex_div_timestamp)
                elif isinstance(ex_div_timestamp, Timestamp):
                    next_dividend_date = ex_div_timestamp.to_pydatetime()

            return next_dividend_date

        except Exception as e:
            logger.error(f"Error fetching dividend date for {symbol}: {str(e)}")
            raise ValueError(
                f"Failed to get dividend data for symbol {symbol}: {str(e)}"
            )

    def get_dividend_info(self, symbol: str) -> DividendInfo:
        """
        Get comprehensive dividend information for a ticker symbol.

        Args:
            symbol: The ticker symbol (e.g., 'AAPL', 'MSFT')

        Returns:
            DividendInfo object with dividend details

        Raises:
            ValueError: If the symbol is invalid or not found
        """
        try:
            logger.debug(f"Fetching dividend info for symbol: {symbol}")

            ticker = yf.Ticker(symbol)
            info = ticker.info

            # Get next dividend date
            next_dividend_date = self.get_next_dividend_date(symbol)

            # Extract dividend information from ticker info
            dividend_rate = info.get("dividendRate")
            dividend_yield = info.get("dividendYield")

            # Get ex-dividend date
            ex_dividend_date = None
            if "exDividendDate" in info and info["exDividendDate"]:
                ex_div_timestamp = info["exDividendDate"]
                if isinstance(ex_div_timestamp, (int, float)):
                    ex_dividend_date = datetime.fromtimestamp(ex_div_timestamp)
                elif isinstance(ex_div_timestamp, Timestamp):
                    ex_dividend_date = ex_div_timestamp.to_pydatetime()

            # Get pay date (if available)
            pay_date = None
            if "payoutDate" in info and info["payoutDate"]:
                payout_timestamp = info["payoutDate"]
                if isinstance(payout_timestamp, (int, float)):
                    pay_date = datetime.fromtimestamp(payout_timestamp)
                elif isinstance(payout_timestamp, Timestamp):
                    pay_date = payout_timestamp.to_pydatetime()

            return DividendInfo(
                symbol=symbol,
                next_dividend_date=next_dividend_date,
                dividend_rate=dividend_rate,
                dividend_yield=dividend_yield,
                ex_dividend_date=ex_dividend_date,
                pay_date=pay_date,
            )

        except Exception as e:
            logger.error(f"Error fetching dividend info for {symbol}: {str(e)}")
            raise ValueError(
                f"Failed to get dividend info for symbol {symbol}: {str(e)}"
            )

    def get_stock_info(self, symbol: str) -> StockInfo:
        """
        Get basic stock information for a ticker symbol.

        Args:
            symbol: The ticker symbol (e.g., 'AAPL', 'MSFT')

        Returns:
            StockInfo object with basic stock details

        Raises:
            ValueError: If the symbol is invalid or not found
        """
        try:
            logger.debug(f"Fetching stock info for symbol: {symbol}")

            ticker = yf.Ticker(symbol)
            info = ticker.info

            return StockInfo(
                symbol=symbol,
                name=info.get("longName") or info.get("shortName"),
                sector=info.get("sector"),
                industry=info.get("industry"),
                market_cap=info.get("marketCap"),
                current_price=info.get("currentPrice")
                or info.get("regularMarketPrice"),
            )

        except Exception as e:
            logger.error(f"Error fetching stock info for {symbol}: {str(e)}")
            raise ValueError(f"Failed to get stock info for symbol {symbol}: {str(e)}")
