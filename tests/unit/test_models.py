"""Unit tests for cursor_usage.models module."""

from datetime import datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from cursor_usage.models import AggregatedStats, ModelStats, UsageEvent, UserStats
from tests.fixtures.sample_data import make_usage_event


class TestUsageEvent:
    """Tests for UsageEvent model."""

    def test_create_valid_event(self) -> None:
        """Create UsageEvent with valid data."""
        event = make_usage_event()

        assert event.user == "alice@example.com"
        assert event.cost == Decimal("0.05")

    def test_month_key_property(self) -> None:
        """month_key returns YYYY-MM format."""
        event = make_usage_event(date=datetime(2026, 3, 15))
        assert event.month_key == "2026-03"

    def test_month_key_padding(self) -> None:
        """month_key pads single-digit months with zero."""
        event = make_usage_event(date=datetime(2026, 1, 5))
        assert event.month_key == "2026-01"

    def test_normalized_model_sonnet(self) -> None:
        """normalized_model returns 'sonnet-4-5' for sonnet models."""
        event = make_usage_event(model="claude-4.5-sonnet-high-thinking")
        assert event.normalized_model == "sonnet-4-5"

    def test_normalized_model_haiku(self) -> None:
        """normalized_model returns 'haiku-4-5' for haiku models."""
        event = make_usage_event(model="claude-4.5-haiku")
        assert event.normalized_model == "haiku-4-5"

    def test_normalized_model_opus(self) -> None:
        """normalized_model returns 'opus-4-5' for opus models."""
        event = make_usage_event(model="claude-4.5-opus-high-thinking")
        assert event.normalized_model == "opus-4-5"

    def test_normalized_model_gpt(self) -> None:
        """normalized_model normalizes gpt-5.2 to gpt-5-2."""
        event = make_usage_event(model="gpt-5.2")
        assert event.normalized_model == "gpt-5-2"

    def test_normalized_model_unknown(self) -> None:
        """normalized_model returns original for unknown models."""
        event = make_usage_event(model="custom-model-v1")
        assert event.normalized_model == "custom-model-v1"

    def test_normalized_model_case_insensitive(self) -> None:
        """normalized_model is case-insensitive for known models."""
        event = make_usage_event(model="Claude-4.5-SONNET")
        assert event.normalized_model == "sonnet-4-5"

    def test_negative_tokens_rejected(self) -> None:
        """Negative token counts are rejected by validation."""
        with pytest.raises(ValidationError):
            make_usage_event(total_tokens=-100)

    def test_negative_cost_rejected(self) -> None:
        """Negative cost is rejected by validation."""
        with pytest.raises(ValidationError):
            make_usage_event(cost="-0.05")


class TestModelStats:
    """Tests for ModelStats model."""

    def test_default_values(self) -> None:
        """ModelStats initializes with zero defaults."""
        stats = ModelStats()

        assert stats.input_tokens == 0
        assert stats.output_tokens == 0
        assert stats.cost == Decimal("0.00")

    def test_create_with_values(self) -> None:
        """Create ModelStats with explicit values."""
        stats = ModelStats(
            input_tokens=1000,
            output_tokens=500,
            cost=Decimal("0.25"),
        )

        assert stats.input_tokens == 1000
        assert stats.cost == Decimal("0.25")


class TestUserStats:
    """Tests for UserStats model."""

    def test_default_values(self) -> None:
        """UserStats initializes with zero defaults."""
        stats = UserStats()

        assert stats.input_tokens == 0
        assert stats.total_tokens == 0
        assert stats.cost == Decimal("0.00")


class TestAggregatedStats:
    """Tests for AggregatedStats model."""

    def test_create_empty(self) -> None:
        """Create empty AggregatedStats."""
        stats = AggregatedStats(month="2026-01")

        assert stats.month == "2026-01"
        assert stats.total_tokens == 0
        assert stats.cost == Decimal("0.00")
        assert len(stats.models) == 0
        assert len(stats.model_stats) == 0
        assert len(stats.user_stats) == 0

    def test_add_single_event(self, single_event: UsageEvent) -> None:
        """Adding event updates all counters."""
        stats = AggregatedStats(month="2026-01")
        stats.add(single_event)

        assert stats.input_tokens == single_event.input_no_cache
        assert stats.output_tokens == single_event.output_tokens
        assert stats.cost == single_event.cost
        assert single_event.normalized_model in stats.models

    def test_add_tracks_model_stats(self, single_event: UsageEvent) -> None:
        """Adding event populates model_stats."""
        stats = AggregatedStats(month="2026-01")
        stats.add(single_event)

        model_name = single_event.normalized_model
        assert model_name in stats.model_stats
        assert stats.model_stats[model_name].cost == single_event.cost

    def test_add_tracks_user_stats(self, single_event: UsageEvent) -> None:
        """Adding event populates user_stats."""
        stats = AggregatedStats(month="2026-01")
        stats.add(single_event)

        user = single_event.user
        assert user in stats.user_stats
        assert stats.user_stats[user].cost == single_event.cost

    def test_add_multiple_events(self, multi_user_events: list[UsageEvent]) -> None:
        """Adding multiple events accumulates totals."""
        stats = AggregatedStats(month="2026-01")
        for event in multi_user_events:
            stats.add(event)

        expected_cost = sum(e.cost for e in multi_user_events)
        assert stats.cost == expected_cost

    def test_add_returns_self(self, single_event: UsageEvent) -> None:
        """add() returns self for method chaining."""
        stats = AggregatedStats(month="2026-01")
        result = stats.add(single_event)

        assert result is stats

    def test_merge_combines_stats(self) -> None:
        """merge() combines two AggregatedStats."""
        stats1 = AggregatedStats(month="2026-01")
        stats1.add(make_usage_event(user="alice@example.com", cost="0.10"))

        stats2 = AggregatedStats(month="2026-01")
        stats2.add(make_usage_event(user="bob@example.com", cost="0.20"))

        stats1.merge(stats2)

        assert stats1.cost == Decimal("0.30")
        assert "alice@example.com" in stats1.user_stats
        assert "bob@example.com" in stats1.user_stats

    def test_merge_returns_self(self) -> None:
        """merge() returns self for method chaining."""
        stats1 = AggregatedStats(month="2026-01")
        stats2 = AggregatedStats(month="2026-01")

        result = stats1.merge(stats2)
        assert result is stats1
