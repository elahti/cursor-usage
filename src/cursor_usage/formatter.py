"""Number and currency formatting utilities."""

from decimal import Decimal


def format_number(value: int) -> str:
    """Format an integer with comma separators.

    Args:
        value: Integer to format.

    Returns:
        Formatted string like "1,234,567".
    """
    return f"{value:,}"


def format_currency(value: Decimal) -> str:
    """Format a decimal as USD currency.

    Args:
        value: Decimal value to format.

    Returns:
        Formatted string like "$1,234.56".
    """
    return f"${value:,.2f}"
