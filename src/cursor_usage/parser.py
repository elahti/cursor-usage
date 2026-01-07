"""CSV parsing utilities for cursor usage data.

Handles reading and validating CSV exports from Cursor IDE.
"""

import csv
import sys
from collections.abc import Iterator
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import TextIO

from cursor_usage.models import UsageEvent


def parse_csv_file(file_path: Path) -> list[UsageEvent]:
    """Parse a CSV file into a list of UsageEvent objects.

    Args:
        file_path: Path to the CSV file.

    Returns:
        List of parsed UsageEvent objects.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the CSV format is invalid.
    """
    with file_path.open(mode="r", encoding="utf-8") as f:
        return list(parse_csv_stream(f))


def parse_csv_stream(stream: TextIO) -> Iterator[UsageEvent]:
    """Parse a CSV stream into UsageEvent objects.

    Uses csv.DictReader for robust CSV parsing with proper
    handling of quoted fields containing commas.

    Args:
        stream: File-like object containing CSV data.

    Yields:
        UsageEvent objects for each valid row.
    """
    reader = csv.DictReader(stream)

    for row_num, row in enumerate(reader, start=2):
        try:
            event = _parse_row(row)
            yield event
        except (ValueError, KeyError) as e:
            print(f"Warning: Skipping row {row_num}: {e}", file=sys.stderr)


def _parse_row(row: dict[str, str]) -> UsageEvent:
    """Convert a CSV row dict to a UsageEvent.

    Args:
        row: Dictionary from csv.DictReader.

    Returns:
        Parsed UsageEvent.
    """
    date_str = row["Date"].rstrip("Z")
    if "+" in date_str:
        date_str = date_str.split("+")[0]

    return UsageEvent(
        date=datetime.fromisoformat(date_str),
        user=row["User"],
        kind=row["Kind"],
        model=row["Model"],
        max_mode=row["Max Mode"].lower() == "yes",
        cache_write=int(row["Input (w/ Cache Write)"]),
        input_no_cache=int(row["Input (w/o Cache Write)"]),
        cache_read=int(row["Cache Read"]),
        output_tokens=int(row["Output Tokens"]),
        total_tokens=int(row["Total Tokens"]),
        cost=Decimal(row["Cost"]),
    )
