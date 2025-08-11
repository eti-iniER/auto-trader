import json

from app.db.models import Log


def format_log_entry(log: Log) -> str:
    lines = []
    timestamp = log.created_at.strftime("%Y-%m-%d %H:%M:%S")
    lines.append(f"[{timestamp}] [{log.type.value}] {log.message}")

    if log.description:
        lines.append(f"    Description : {log.description}")
    if log.extra:
        # Pretty-print JSON but keep indentation
        extra_str = json.dumps(log.extra, ensure_ascii=False)
        lines.append(f"    Extra       : {extra_str}")

    return "\n".join(lines)
