import uuid
from typing import Literal, Optional

from app.db.crud import log_message as log_message_to_db
from app.db.enums import LogType

LOG_TYPE = Literal[
    "unspecified", "authentication", "alert", "trade", "order", "error", "admin"
]


async def log_message(
    message: str,
    description: Optional[str] = None,
    log_type: LOG_TYPE = "unspecified",
    user_id: Optional[uuid.UUID] = None,
    extra: Optional[dict] = None,
    identifier: Optional[str] = None,
) -> None:
    """
    Logs a message to the database.

    Args:
        message (str): The log message.
        log_type (str): The type of log.
        extra (Optional[dict]): Additional information to log.
    """
    try:
        enum_type = LogType(log_type.upper())
    except ValueError:
        enum_type = LogType.UNSPECIFIED

    await log_message_to_db(message, description, enum_type, user_id, extra, identifier)
