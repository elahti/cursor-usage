"""Factory functions for creating test data without real emails."""

from datetime import datetime
from decimal import Decimal

from cursor_usage.models import UsageEvent


def make_usage_event(
    date: datetime | None = None,
    user: str = "alice@example.com",
    kind: str = "Included",
    model: str = "claude-4.5-sonnet",
    max_mode: bool = False,
    cache_write: int = 1000,
    input_no_cache: int = 500,
    cache_read: int = 2000,
    output_tokens: int = 300,
    total_tokens: int = 3800,
    cost: Decimal | str = "0.05",
) -> UsageEvent:
    """Create a UsageEvent with sensible defaults for testing."""
    return UsageEvent(
        date=date or datetime(2026, 1, 15, 10, 30, 0),
        user=user,
        kind=kind,
        model=model,
        max_mode=max_mode,
        cache_write=cache_write,
        input_no_cache=input_no_cache,
        cache_read=cache_read,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        cost=Decimal(cost) if isinstance(cost, str) else cost,
    )


def make_csv_row(
    date: str = "2026-01-15T10:30:00.000Z",
    user: str = "alice@example.com",
    kind: str = "Included",
    model: str = "claude-4.5-sonnet",
    max_mode: str = "No",
    cache_write: str = "1000",
    input_no_cache: str = "500",
    cache_read: str = "2000",
    output_tokens: str = "300",
    total_tokens: str = "3800",
    cost: str = "0.05",
) -> dict[str, str]:
    """Create a CSV row dict as returned by csv.DictReader."""
    return {
        "Date": date,
        "User": user,
        "Kind": kind,
        "Model": model,
        "Max Mode": max_mode,
        "Input (w/ Cache Write)": cache_write,
        "Input (w/o Cache Write)": input_no_cache,
        "Cache Read": cache_read,
        "Output Tokens": output_tokens,
        "Total Tokens": total_tokens,
        "Cost": cost,
    }


def make_csv_content(rows: list[dict[str, str]] | None = None) -> str:
    """Generate CSV content string from rows."""
    header = "Date,User,Kind,Model,Max Mode,Input (w/ Cache Write),Input (w/o Cache Write),Cache Read,Output Tokens,Total Tokens,Cost"
    if rows is None:
        rows = [make_csv_row()]

    lines = [header]
    for row in rows:
        line = ",".join(
            [
                f'"{row["Date"]}"',
                f'"{row["User"]}"',
                f'"{row["Kind"]}"',
                f'"{row["Model"]}"',
                f'"{row["Max Mode"]}"',
                row["Input (w/ Cache Write)"],
                row["Input (w/o Cache Write)"],
                row["Cache Read"],
                row["Output Tokens"],
                row["Total Tokens"],
                row["Cost"],
            ]
        )
        lines.append(line)
    return "\n".join(lines)
