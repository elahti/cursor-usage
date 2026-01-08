"""Unit tests for cursor_usage.aggregator module."""

from datetime import datetime
from decimal import Decimal

from cursor_usage.aggregator import aggregate_by_month, compute_grand_total
from cursor_usage.models import UsageEvent
from tests.fixtures.sample_data import make_usage_event


class TestAggregateByMonth:
    """Tests for aggregate_by_month function."""

    def test_empty_events_returns_empty_list(self) -> None:
        """Empty input returns empty list."""
        result = aggregate_by_month([])
        assert result == []

    def test_single_event_single_month(self, single_event: UsageEvent) -> None:
        """Single event returns single monthly aggregation."""
        result = aggregate_by_month([single_event])

        assert len(result) == 1
        assert result[0].month == single_event.month_key
        assert result[0].cost == single_event.cost

    def test_multiple_events_same_month(self) -> None:
        """Multiple events in same month are aggregated together."""
        events = [
            make_usage_event(date=datetime(2026, 1, 10), cost="0.10"),
            make_usage_event(date=datetime(2026, 1, 20), cost="0.15"),
            make_usage_event(date=datetime(2026, 1, 25), cost="0.20"),
        ]

        result = aggregate_by_month(events)

        assert len(result) == 1
        assert result[0].month == "2026-01"
        assert result[0].cost == Decimal("0.45")

    def test_events_across_months(self, multi_month_events: list[UsageEvent]) -> None:
        """Events are grouped by month correctly."""
        result = aggregate_by_month(multi_month_events)

        assert len(result) == 2
        assert result[0].month == "2026-01"
        assert result[1].month == "2026-02"

    def test_results_sorted_ascending(self) -> None:
        """Results are sorted by month ascending."""
        events = [
            make_usage_event(date=datetime(2026, 3, 1)),
            make_usage_event(date=datetime(2026, 1, 1)),
            make_usage_event(date=datetime(2026, 2, 1)),
        ]

        result = aggregate_by_month(events)

        months = [s.month for s in result]
        assert months == ["2026-01", "2026-02", "2026-03"]

    def test_model_stats_populated(self, multi_model_events: list[UsageEvent]) -> None:
        """Each month's model_stats contains per-model data."""
        result = aggregate_by_month(multi_model_events)

        assert len(result) == 1
        assert len(result[0].model_stats) == 4  # 4 different models

    def test_user_stats_populated(self, multi_user_events: list[UsageEvent]) -> None:
        """Each month's user_stats contains per-user data."""
        result = aggregate_by_month(multi_user_events)

        assert len(result) == 1
        assert "alice@example.com" in result[0].user_stats
        assert "bob@example.com" in result[0].user_stats


class TestComputeGrandTotal:
    """Tests for compute_grand_total function."""

    def test_empty_monthly_stats(self) -> None:
        """Empty input returns zeroed total."""
        result = compute_grand_total([])

        assert result.month == "Total"
        assert result.cost == Decimal("0.00")
        assert result.total_tokens == 0

    def test_single_month_total(self) -> None:
        """Single month total equals that month's values."""
        events = [make_usage_event(cost="0.50", total_tokens=1000)]
        monthly = aggregate_by_month(events)

        total = compute_grand_total(monthly)

        assert total.month == "Total"
        assert total.cost == Decimal("0.50")
        assert total.total_tokens == 1000

    def test_multiple_months_summed(self) -> None:
        """Multiple months are summed together."""
        events = [
            make_usage_event(date=datetime(2026, 1, 1), cost="0.10", total_tokens=100),
            make_usage_event(date=datetime(2026, 2, 1), cost="0.20", total_tokens=200),
            make_usage_event(date=datetime(2026, 3, 1), cost="0.30", total_tokens=300),
        ]
        monthly = aggregate_by_month(events)

        total = compute_grand_total(monthly)

        assert total.cost == Decimal("0.60")
        assert total.total_tokens == 600

    def test_user_stats_merged(self) -> None:
        """user_stats from all months are merged."""
        events = [
            make_usage_event(
                date=datetime(2026, 1, 1), user="alice@example.com", cost="0.10"
            ),
            make_usage_event(
                date=datetime(2026, 2, 1), user="alice@example.com", cost="0.15"
            ),
            make_usage_event(
                date=datetime(2026, 1, 1), user="bob@example.com", cost="0.20"
            ),
        ]
        monthly = aggregate_by_month(events)

        total = compute_grand_total(monthly)

        assert "alice@example.com" in total.user_stats
        assert "bob@example.com" in total.user_stats
        assert total.user_stats["alice@example.com"].cost == Decimal("0.25")
