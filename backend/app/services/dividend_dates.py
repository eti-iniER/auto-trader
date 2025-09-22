import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from app.clients.yahoo.client import YahooFinanceClient
from app.db.models import Instrument

from app.services.logging.helper import log_message
from sqlalchemy import case, select, update
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def fetch_dividend_date_for_symbol(
    yahoo_client: YahooFinanceClient, symbol: str, instrument_id: uuid.UUID
) -> Tuple[uuid.UUID, Optional[datetime]]:
    """Return (instrument_id, next_dividend_date) or (id, None) on failure."""
    try:
        dt = yahoo_client.get_next_dividend_date(symbol)
        if dt and dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        logger.info(f"Fetched dividend date for {symbol}: {dt}")
        return instrument_id, dt
    except Exception as e:  # external API may throw many kinds
        logger.error(f"Failed to fetch dividend date for symbol {symbol}: {e}")
        return instrument_id, None


async def bulk_update_dividend_dates(
    db: AsyncSession, updates: List[Tuple[uuid.UUID, Optional[datetime]]]
) -> int:
    """Bulk update dividend dates; returns number of rows updated."""
    valid = [(i, d) for i, d in updates if d]
    if not valid:
        return 0
    try:
        updated = 0
        batch_size = 200
        for i in range(0, len(valid), batch_size):
            batch = valid[i : i + batch_size]
            ids = [bid for bid, _ in batch]
            case_stmt = case(
                *[(Instrument.id == bid, dt) for bid, dt in batch],
                else_=Instrument.next_dividend_date,
            )
            stmt = (
                update(Instrument)
                .where(Instrument.id.in_(ids))
                .values(next_dividend_date=case_stmt)
            )
            result = await db.execute(stmt)
            updated += result.rowcount
        await db.commit()
        logger.info(f"Updated dividend dates for {updated} instruments")
        return updated
    except Exception:
        await db.rollback()
        logger.exception("Error in bulk update")
        raise


async def fetch_instruments_with_yahoo_symbols(
    db: AsyncSession, user_id: Optional[uuid.UUID] = None
) -> List[Tuple[uuid.UUID, str, uuid.UUID, str]]:
    """Return stale instruments (id, yahoo_symbol, user_id, market_and_symbol)."""
    stmt = select(
        Instrument.id,
        Instrument.yahoo_symbol,
        Instrument.user_id,
        Instrument.market_and_symbol,
    ).where(Instrument.yahoo_symbol.isnot(None), Instrument.yahoo_symbol != "")
    if user_id:
        stmt = stmt.where(Instrument.user_id == user_id)
    return (await db.execute(stmt)).all()


def fetch_dividend_dates_in_batches(
    instruments: List[Tuple[uuid.UUID, str, uuid.UUID, str]],
    max_workers: int = 500,
) -> List[Tuple[uuid.UUID, Optional[datetime]]]:
    """
    Fetch dividend dates concurrently using ThreadPoolExecutor.

    :param instruments: List of instruments (id, yahoo_symbol, user_id, market_and_symbol)
    :param max_workers: Number of threads to run in parallel
    :return: List of (instrument_id, dividend_date) tuples
    """
    if not instruments:
        return []

    base_client = YahooFinanceClient()
    results: List[Tuple[uuid.UUID, Optional[datetime]]] = []

    # Blocking function that fetches one instrument
    def fetch_sync(
        inst_id: uuid.UUID, symbol: str
    ) -> Tuple[uuid.UUID, Optional[datetime]]:
        try:
            dt = base_client.get_next_dividend_date(symbol)
            if dt and dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            logger.info(f"Fetched dividend date for {symbol}: {dt}")
            return inst_id, dt
        except Exception as exc:
            logger.error(f"Failed to fetch dividend date for {symbol}: {exc}")
            return inst_id, None

    # Use ThreadPoolExecutor to fetch in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(fetch_sync, inst_id, symbol): inst_id
            for inst_id, symbol, *_ in instruments
        }
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as exc:
                inst_id = futures[future]
                logger.error(f"Future failed for instrument {inst_id}: {exc}")
                results.append((inst_id, None))

    return results


async def log_dividend_updates_by_user(
    instruments: List[Tuple[uuid.UUID, str, uuid.UUID, str]],
    successful_updates: List[Tuple[uuid.UUID, Optional[datetime]]],
    target_user_id: Optional[uuid.UUID] = None,
) -> None:
    """Log per-user summaries for successful dividend updates."""
    user_lookup = {iid: uid for iid, _, uid, _ in instruments}
    symbol_lookup = {iid: ms for iid, _, _, ms in instruments}
    per_user: defaultdict[uuid.UUID, List[str]] = defaultdict(list)
    for inst_id, _ in successful_updates:
        uid = user_lookup.get(inst_id)
        if not uid:
            continue
        if target_user_id and uid != target_user_id:
            continue
        ms = symbol_lookup.get(inst_id)
        if ms:
            per_user[uid].append(ms)
    for uid, symbols in per_user.items():
        await log_message(
            message=f"Dividend dates updated for {len(symbols)} instruments",
            description=(
                f"Updated dividend dates for your instruments. {len(symbols)} instruments refreshed from Yahoo Finance."
            ),
            log_type="unspecified",
            user_id=uid,
            extra={
                "action": "dividend_dates_update",
                "instruments_updated": len(symbols),
                "updated_instruments": symbols,
            },
        )
        logger.info(
            f"Logged dividend date update for user {uid}: {len(symbols)} instruments"
        )


async def _process_dividend_updates(
    db: AsyncSession,
    instruments: List[Tuple[uuid.UUID, str, uuid.UUID, str]],
    target_user_id: Optional[uuid.UUID] = None,
) -> int:
    """Internal helper performing fetch, persist, and logging steps."""
    if not instruments:
        logger.info("No instruments with Yahoo symbols found")
        return 0
    logger.info(f"Fetching dividend dates for {len(instruments)} instruments")
    # fetch_dividend_dates_in_batches is a synchronous, CPU/blocking style helper
    # that returns a plain list. Previously we did `await fetch_dividend_dates_in_batches(...)`
    # which raised: "TypeError: object list can't be used in 'await' expression".
    # Run it in a default executor so the event loop isn't blocked.
    loop = asyncio.get_running_loop()
    updates = await loop.run_in_executor(
        None, fetch_dividend_dates_in_batches, instruments
    )
    successful = [(i, d) for i, d in updates if d]
    updated = await bulk_update_dividend_dates(db, updates)
    await log_dividend_updates_by_user(instruments, successful, target_user_id)
    logger.info(f"Dividend dates updated for {updated} instruments")
    return updated


async def fetch_and_update_dividend_dates_for_user(
    db: AsyncSession, user_id: uuid.UUID
) -> int:
    """Public API: update dividend dates for one user."""
    instruments = await fetch_instruments_with_yahoo_symbols(db, user_id)
    return await _process_dividend_updates(db, instruments, user_id)


async def fetch_and_update_all_dividend_dates(db: AsyncSession) -> int:
    """Public API: update dividend dates for all users."""
    instruments = await fetch_instruments_with_yahoo_symbols(db)
    return await _process_dividend_updates(db, instruments)


async def fetch_and_update_single_dividend_date(
    db: AsyncSession, instrument_id: uuid.UUID
) -> bool:
    """Update dividend date for one instrument; True if changed."""
    stmt = select(
        Instrument.id,
        Instrument.yahoo_symbol,
        Instrument.user_id,
        Instrument.market_and_symbol,
    ).where(
        Instrument.id == instrument_id,
        Instrument.yahoo_symbol.isnot(None),
        Instrument.yahoo_symbol != "",
    )
    instrument = (await db.execute(stmt)).first()

    if not instrument:
        logger.warning("Instrument %s not found or has no Yahoo symbol", instrument_id)
        return False

    client = YahooFinanceClient()
    _, dt = await fetch_dividend_date_for_symbol(
        client, instrument.yahoo_symbol, instrument.id
    )
    if not dt:
        logger.info("No dividend date found for instrument %s", instrument_id)
        return False
    updated = await bulk_update_dividend_dates(db, [(instrument.id, dt)])
    if updated:
        await log_message(
            message="Dividend date updated for instrument",
            description=(
                f"Dividend date for instrument {instrument.market_and_symbol} updated to {dt.strftime('%Y-%m-%d')} from Yahoo Finance."
            ),
            log_type="unspecified",
            user_id=instrument.user_id,
            extra={
                "action": "single_dividend_date_update",
                "instrument": instrument.market_and_symbol,
                "yahoo_symbol": instrument.yahoo_symbol,
                "dividend_date": dt.isoformat(),
            },
        )
        logger.info(
            "Logged dividend date update for user %s, instrument %s",
            instrument.user_id,
            instrument_id,
        )
    logger.info("Dividend date update result for instrument %s: %s", instrument_id, dt)
    return bool(updated)
