"""Unit tests for cursor_usage.formatter module."""

from decimal import Decimal

from cursor_usage.formatter import format_currency, format_number


class TestFormatNumber:
    """Tests for format_number function."""

    def test_zero(self) -> None:
        """Zero is formatted without comma."""
        assert format_number(0) == "0"

    def test_small_number(self) -> None:
        """Small numbers have no comma."""
        assert format_number(1) == "1"
        assert format_number(999) == "999"

    def test_thousands_separator(self) -> None:
        """Numbers >= 1000 have comma separator."""
        assert format_number(1000) == "1,000"
        assert format_number(1234) == "1,234"

    def test_millions(self) -> None:
        """Millions have two comma separators."""
        assert format_number(1000000) == "1,000,000"
        assert format_number(1234567) == "1,234,567"

    def test_large_numbers(self) -> None:
        """Very large numbers are formatted correctly."""
        assert format_number(1234567890) == "1,234,567,890"


class TestFormatCurrency:
    """Tests for format_currency function."""

    def test_adds_dollar_sign(self) -> None:
        """Currency starts with dollar sign."""
        result = format_currency(Decimal("0"))
        assert result.startswith("$")

    def test_zero(self) -> None:
        """Zero shows as $0.00."""
        assert format_currency(Decimal("0")) == "$0.00"

    def test_two_decimal_places(self) -> None:
        """Currency shows exactly two decimal places."""
        assert format_currency(Decimal("1")) == "$1.00"
        assert format_currency(Decimal("1.5")) == "$1.50"
        assert format_currency(Decimal("1.234")) == "$1.23"

    def test_thousands_separator(self) -> None:
        """Large currency values have comma separators."""
        assert format_currency(Decimal("1000")) == "$1,000.00"
        assert format_currency(Decimal("1234.56")) == "$1,234.56"

    def test_rounding(self) -> None:
        """Values are rounded to 2 decimal places."""
        assert format_currency(Decimal("1.999")) == "$2.00"
        assert format_currency(Decimal("1.994")) == "$1.99"
