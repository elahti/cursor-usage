"""Unit tests for cursor_usage.renderer module."""

from datetime import datetime

from cursor_usage.aggregator import aggregate_by_month, compute_grand_total
from cursor_usage.renderer import (
    COLUMNS_GROUP_BY_USER,
    COLUMNS_NO_BREAKDOWN,
    COLUMNS_WITH_BREAKDOWN,
    anonymize_email,
    get_columns,
    render_border,
    render_header,
    render_separator,
    render_table,
)
from tests.fixtures.sample_data import make_usage_event


class TestAnonymizeEmail:
    """Tests for anonymize_email function."""

    def test_returns_user_hash_format(self) -> None:
        """Returns User-{hash} format."""
        result = anonymize_email("test@example.com")

        assert result.startswith("User-")
        assert len(result) == 13  # "User-" + 8 hex chars

    def test_consistent_hashing(self) -> None:
        """Same email produces same hash."""
        email = "alice@example.com"

        hash1 = anonymize_email(email)
        hash2 = anonymize_email(email)

        assert hash1 == hash2

    def test_different_emails_different_hashes(self) -> None:
        """Different emails produce different hashes."""
        hash1 = anonymize_email("alice@example.com")
        hash2 = anonymize_email("bob@example.com")

        assert hash1 != hash2


class TestGetColumns:
    """Tests for get_columns function."""

    def test_default_columns(self) -> None:
        """Default (no flags) uses COLUMNS_NO_BREAKDOWN."""
        result = get_columns(show_models=False, group_by_user=False)
        assert result == COLUMNS_NO_BREAKDOWN

    def test_breakdown_columns(self) -> None:
        """show_models=True uses COLUMNS_WITH_BREAKDOWN."""
        result = get_columns(show_models=True, group_by_user=False)
        assert result == COLUMNS_WITH_BREAKDOWN

    def test_user_group_columns(self) -> None:
        """group_by_user=True uses COLUMNS_GROUP_BY_USER."""
        result = get_columns(show_models=False, group_by_user=True)
        assert result == COLUMNS_GROUP_BY_USER

    def test_group_by_user_takes_precedence(self) -> None:
        """group_by_user takes precedence over show_models."""
        result = get_columns(show_models=True, group_by_user=True)
        assert result == COLUMNS_GROUP_BY_USER


class TestRenderBorder:
    """Tests for render_border function."""

    def test_top_border_chars(self) -> None:
        """Top border uses correct box-drawing characters."""
        result = render_border("top", COLUMNS_NO_BREAKDOWN)

        assert result.startswith("┌")
        assert result.endswith("┐")
        assert "┬" in result
        assert "─" in result

    def test_bottom_border_chars(self) -> None:
        """Bottom border uses correct box-drawing characters."""
        result = render_border("bottom", COLUMNS_NO_BREAKDOWN)

        assert result.startswith("└")
        assert result.endswith("┘")
        assert "┴" in result


class TestRenderSeparator:
    """Tests for render_separator function."""

    def test_separator_chars(self) -> None:
        """Separator uses correct box-drawing characters."""
        result = render_separator(COLUMNS_NO_BREAKDOWN)

        assert result.startswith("├")
        assert result.endswith("┤")
        assert "┼" in result


class TestRenderHeader:
    """Tests for render_header function."""

    def test_header_contains_column_names(self) -> None:
        """Header contains all column names."""
        result = render_header(COLUMNS_NO_BREAKDOWN)

        assert "Month" in result
        assert "Models" in result
        assert "Input" in result
        assert "Cost (USD)" in result


class TestRenderTable:
    """Tests for render_table function."""

    def test_renders_complete_table(self) -> None:
        """render_table produces complete table structure."""
        events = [
            make_usage_event(
                date=datetime(2026, 1, 15),
                model="claude-4.5-sonnet",
                cost="0.25",
                input_no_cache=1000,
                output_tokens=500,
            )
        ]
        monthly = aggregate_by_month(events)
        total = compute_grand_total(monthly)

        result = render_table(monthly, total)

        # Check structure
        lines = result.split("\n")
        assert lines[0].startswith("┌")  # Top border
        assert lines[-1].startswith("└")  # Bottom border

        # Check content
        assert "2026-01" in result
        assert "Total" in result

    def test_table_contains_formatted_numbers(self) -> None:
        """Numbers are formatted with commas."""
        events = [
            make_usage_event(
                input_no_cache=1000,
                cost="0.25",
            )
        ]
        monthly = aggregate_by_month(events)
        total = compute_grand_total(monthly)

        result = render_table(monthly, total)

        assert "1,000" in result  # Input tokens
        assert "$0.25" in result  # Cost

    def test_show_models_breakdown(self) -> None:
        """show_models=True includes per-model rows."""
        events = [
            make_usage_event(model="claude-4.5-sonnet", cost="0.10"),
            make_usage_event(model="claude-4.5-haiku", cost="0.05"),
        ]
        monthly = aggregate_by_month(events)
        total = compute_grand_total(monthly)

        result = render_table(monthly, total, show_models=True)

        assert "sonnet-4-5" in result
        assert "haiku-4-5" in result
        assert "└─" in result  # Breakdown row indicator

    def test_group_by_user(self) -> None:
        """group_by_user=True shows per-user breakdown."""
        events = [
            make_usage_event(user="alice@example.com", cost="0.10"),
            make_usage_event(user="bob@example.com", cost="0.20"),
        ]
        monthly = aggregate_by_month(events)
        total = compute_grand_total(monthly)

        result = render_table(monthly, total, group_by_user=True)

        assert "alice@example.com" in result
        assert "bob@example.com" in result

    def test_group_by_user_no_models_column(self) -> None:
        """group_by_user=True excludes Models column."""
        events = [make_usage_event()]
        monthly = aggregate_by_month(events)
        total = compute_grand_total(monthly)

        result = render_table(monthly, total, group_by_user=True)
        header_line = result.split("\n")[1]

        assert "Models" not in header_line

    def test_anonymize_hides_emails(self) -> None:
        """anonymize=True replaces emails with User-{hash}."""
        events = [
            make_usage_event(user="alice@example.com"),
            make_usage_event(user="bob@example.com"),
        ]
        monthly = aggregate_by_month(events)
        total = compute_grand_total(monthly)

        result = render_table(monthly, total, group_by_user=True, anonymize=True)

        assert "alice@example.com" not in result
        assert "bob@example.com" not in result
        assert "User-" in result

    def test_users_sorted_by_cost_descending(self) -> None:
        """Users in breakdown are sorted by cost (highest first)."""
        events = [
            make_usage_event(user="low-spender@example.com", cost="0.05"),
            make_usage_event(user="high-spender@example.com", cost="0.50"),
            make_usage_event(user="mid-spender@example.com", cost="0.25"),
        ]
        monthly = aggregate_by_month(events)
        total = compute_grand_total(monthly)

        result = render_table(monthly, total, group_by_user=True)
        lines = result.split("\n")

        # Find user lines and verify order
        user_lines = [line for line in lines if "└─" in line and "@" in line]
        assert "high-spender" in user_lines[0]
        assert "low-spender" in user_lines[-1]

    def test_models_sorted_by_cost_descending(self) -> None:
        """Models in breakdown are sorted by cost (highest first)."""
        events = [
            make_usage_event(model="claude-4.5-haiku", cost="0.05"),
            make_usage_event(model="claude-4.5-opus", cost="0.50"),
            make_usage_event(model="claude-4.5-sonnet", cost="0.25"),
        ]
        monthly = aggregate_by_month(events)
        total = compute_grand_total(monthly)

        result = render_table(monthly, total, show_models=True)
        lines = result.split("\n")

        # Find model breakdown lines (contain "└─" and a model name)
        model_lines = [
            line
            for line in lines
            if "└─" in line and any(m in line for m in ["opus", "sonnet", "haiku"])
        ]
        assert len(model_lines) == 3
        assert "opus" in model_lines[0]
        assert "sonnet" in model_lines[1]
        assert "haiku" in model_lines[2]

    def test_multiple_months(self) -> None:
        """Render table with multiple months."""
        events = [
            make_usage_event(date=datetime(2026, 1, 10), cost="0.10"),
            make_usage_event(date=datetime(2026, 2, 10), cost="0.20"),
        ]
        monthly = aggregate_by_month(events)
        total = compute_grand_total(monthly)

        result = render_table(monthly, total)

        assert "2026-01" in result
        assert "2026-02" in result
        assert "Total" in result
