from datetime import datetime, timezone
from typing import Optional


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def format_datetime(dt: datetime) -> str:
    return dt.isoformat()


def parse_datetime(dt_str: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    except ValueError:
        return None
