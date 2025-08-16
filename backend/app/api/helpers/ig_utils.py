"""
Common utilities for parsing IG API data.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


def parse_ig_datetime(date_str: Optional[str]) -> datetime:
    """
    Parse datetime string from IG API into timezone-aware datetime.

    Args:
        date_str: DateTime string from IG API

    Returns:
        Timezone-aware datetime object
    """
    try:
        if date_str:
            # Handle ISO format with Z suffix or UTC datetime
            if date_str.endswith("Z"):
                return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            else:
                # Handle UTC datetime without timezone info
                naive_dt = datetime.fromisoformat(date_str)
                return naive_dt.replace(tzinfo=timezone.utc)
        else:
            return datetime.now(timezone.utc)
    except (ValueError, AttributeError):
        logger.warning(f"Failed to parse date string: {date_str}")
        return datetime.now(timezone.utc)
