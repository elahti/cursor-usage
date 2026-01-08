"""Unit tests for cursor_usage.parser module."""

from datetime import datetime
from decimal import Decimal
from io import StringIO
from pathlib import Path

import pytest

from cursor_usage.parser import parse_csv_file, parse_csv_stream, parse_row
from tests.fixtures.sample_data import make_csv_content, make_csv_row


class TestParseRow:
    """Tests for parse_row function."""

    def test_parse_valid_row(self) -> None:
        """Parse a valid CSV row dict into UsageEvent."""
        row = make_csv_row()
        event = parse_row(row)

        assert event.user == "alice@example.com"
        assert event.model == "claude-4.5-sonnet"
        assert event.cost == Decimal("0.05")
        assert event.total_tokens == 3800

    def test_parse_date_with_z_suffix(self) -> None:
        """Handle ISO dates ending with Z (UTC indicator)."""
        row = make_csv_row(date="2026-01-15T10:30:00.000Z")
        event = parse_row(row)
        assert event.date == datetime(2026, 1, 15, 10, 30, 0)

    def test_parse_date_with_timezone_offset(self) -> None:
        """Handle ISO dates with timezone offset."""
        row = make_csv_row(date="2026-01-15T10:30:00+02:00")
        event = parse_row(row)
        assert event.date == datetime(2026, 1, 15, 10, 30, 0)

    def test_parse_max_mode_yes(self) -> None:
        """Parse Max Mode = 'Yes' as True."""
        row = make_csv_row(max_mode="Yes")
        event = parse_row(row)
        assert event.max_mode is True

    def test_parse_max_mode_no(self) -> None:
        """Parse Max Mode = 'No' as False."""
        row = make_csv_row(max_mode="No")
        event = parse_row(row)
        assert event.max_mode is False

    def test_parse_max_mode_case_insensitive(self) -> None:
        """Max Mode parsing should be case-insensitive."""
        row = make_csv_row(max_mode="YES")
        event = parse_row(row)
        assert event.max_mode is True

    def test_parse_integer_fields(self) -> None:
        """Verify all integer fields are parsed correctly."""
        row = make_csv_row(
            cache_write="1000",
            input_no_cache="500",
            cache_read="2000",
            output_tokens="300",
            total_tokens="3800",
        )
        event = parse_row(row)

        assert event.cache_write == 1000
        assert event.input_no_cache == 500
        assert event.cache_read == 2000
        assert event.output_tokens == 300
        assert event.total_tokens == 3800

    def test_parse_decimal_cost(self) -> None:
        """Verify cost is parsed as Decimal for precision."""
        row = make_csv_row(cost="123.45")
        event = parse_row(row)
        assert event.cost == Decimal("123.45")
        assert isinstance(event.cost, Decimal)

    def test_missing_required_field_raises_keyerror(self) -> None:
        """Raise KeyError when required field is missing."""
        row = make_csv_row()
        del row["User"]

        with pytest.raises(KeyError):
            parse_row(row)

    def test_invalid_integer_raises_valueerror(self) -> None:
        """Raise ValueError for non-integer token count."""
        row = make_csv_row(total_tokens="not_a_number")

        with pytest.raises(ValueError):
            parse_row(row)


class TestParseCsvStream:
    """Tests for parse_csv_stream function."""

    def test_parse_valid_stream(self, sample_csv_content: str) -> None:
        """Parse valid CSV stream returns UsageEvents."""
        stream = StringIO(sample_csv_content)
        events = list(parse_csv_stream(stream))

        assert len(events) == 2
        assert events[0].user == "alice@example.com"
        assert events[1].user == "bob@example.com"

    def test_parse_empty_stream(self) -> None:
        """Empty CSV (header only) returns no events."""
        header_only = "Date,User,Kind,Model,Max Mode,Input (w/ Cache Write),Input (w/o Cache Write),Cache Read,Output Tokens,Total Tokens,Cost\n"
        stream = StringIO(header_only)
        events = list(parse_csv_stream(stream))

        assert len(events) == 0

    def test_skip_invalid_rows_with_warning(
        self, sample_csv_content: str, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Invalid rows are skipped with warning to stderr."""
        csv_with_bad_row = sample_csv_content + '\n"bad","data","incomplete"\n'

        stream = StringIO(csv_with_bad_row)
        events = list(parse_csv_stream(stream))

        assert len(events) == 2  # Only valid rows
        captured = capsys.readouterr()
        assert "Warning" in captured.err

    def test_yields_events_incrementally(self, sample_csv_content: str) -> None:
        """Verify generator yields events one at a time."""
        stream = StringIO(sample_csv_content)
        generator = parse_csv_stream(stream)

        first = next(generator)
        assert first.user == "alice@example.com"

        second = next(generator)
        assert second.user == "bob@example.com"


class TestParseCsvFile:
    """Tests for parse_csv_file function."""

    def test_parse_file(self, temp_csv_file: Path) -> None:
        """Parse CSV file returns list of UsageEvents."""
        events = parse_csv_file(temp_csv_file)

        assert len(events) == 2
        assert isinstance(events, list)

    def test_file_not_found(self, tmp_path: Path) -> None:
        """Raise FileNotFoundError for missing file."""
        missing_file = tmp_path / "nonexistent.csv"

        with pytest.raises(FileNotFoundError):
            parse_csv_file(missing_file)


class TestCsvQuotedFields:
    """Tests for CSV fields with special characters."""

    def test_quoted_fields_with_commas(self) -> None:
        """CSV fields with commas are handled correctly."""
        csv_content = make_csv_content(
            [
                make_csv_row(model="model, with comma"),
            ]
        )
        stream = StringIO(csv_content)
        events = list(parse_csv_stream(stream))

        assert len(events) == 1
        assert events[0].model == "model, with comma"
