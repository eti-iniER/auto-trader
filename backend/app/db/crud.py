from typing import Optional

from app.db.deps import get_db_context
from app.db.enums import LogType
from app.db.models import Log


async def log_message(
    message: str, log_type: LogType, extra: Optional[dict] = None
) -> Log:
    """
    Logs a message to the database.

    Args:
        message (str): The log message.
        log_type (LogType): The type of log.
        extra (Optional[dict]): Additional information to log.

    Returns:
        Log: The created log entry.
    """

    async with get_db_context() as db:
        log_entry = Log(message=message, type=log_type, extra=extra)
        db.add(log_entry)
        await db.commit()
        await db.refresh(log_entry)
        return log_entry
