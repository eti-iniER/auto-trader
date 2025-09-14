from typing import List

from app.db.models import Log
from .formatter import format_log_entry


def prepare_logs_file(logs: List[Log]) -> bytes:
    """
    Takes an array of Log objects and prepares an output file with a header.

    Args:
        logs: List of Log objects to format and export

    Returns:
        bytes: Raw binary file content with header and formatted log entries
    """
    if not logs:
        return b"No logs found.\n"

    # Create header with summary information
    header_lines = [
        "=" * 80,
        f"Log Export - {len(logs)} entries",
        f"Generated on: {logs[0].created_at.strftime('%Y-%m-%d at %H:%M:%S')} UTC",
        "=" * 80,
        "",
    ]

    # Format each log entry using the formatter
    formatted_entries = []
    for log in logs:
        formatted_entry = format_log_entry(log)
        formatted_entries.append(formatted_entry)

    # Combine header and entries
    content = "\n".join(header_lines) + "\n\n".join(formatted_entries) + "\n"

    # Convert to bytes and return
    return content.encode("utf-8")
