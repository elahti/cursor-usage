"""Shared pytest fixtures for cursor-usage tests."""

import tempfile
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

import pytest

from cursor_usage.models import UsageEvent
from tests.fixtures.sample_data import make_csv_content, make_csv_row, make_usage_event


@pytest.fixture
def single_event() -> UsageEvent:
    """A single usage event with default values."""
    return make_usage_event()


@pytest.fixture
def multi_user_events() -> list[UsageEvent]:
    """Events from multiple users for testing user grouping."""
    return [
        make_usage_event(user="alice@example.com", cost="0.10"),
        make_usage_event(user="bob@example.com", cost="0.20"),
        make_usage_event(user="alice@example.com", cost="0.15"),
    ]


@pytest.fixture
def multi_month_events() -> list[UsageEvent]:
    """Events spanning multiple months for aggregation testing."""
    return [
        make_usage_event(date=datetime(2026, 1, 10), cost="0.10"),
        make_usage_event(date=datetime(2026, 1, 20), cost="0.15"),
        make_usage_event(date=datetime(2026, 2, 5), cost="0.20"),
        make_usage_event(date=datetime(2026, 2, 15), cost="0.25"),
    ]


@pytest.fixture
def multi_model_events() -> list[UsageEvent]:
    """Events with different models for breakdown testing."""
    return [
        make_usage_event(model="claude-4.5-sonnet", cost="0.10"),
        make_usage_event(model="claude-4.5-haiku", cost="0.05"),
        make_usage_event(model="claude-4.5-opus", cost="0.30"),
        make_usage_event(model="gpt-5.2", cost="0.15"),
    ]


@pytest.fixture
def sample_csv_content() -> str:
    """Valid CSV content for parser testing."""
    return make_csv_content(
        [
            make_csv_row(date="2026-01-15T10:30:00.000Z", user="alice@example.com"),
            make_csv_row(date="2026-01-16T14:00:00.000Z", user="bob@example.com"),
        ]
    )


@pytest.fixture
def temp_csv_file(sample_csv_content: str) -> Iterator[Path]:
    """Create a temporary CSV file for file-based tests."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, encoding="utf-8"
    ) as f:
        f.write(sample_csv_content)
        f.flush()
        yield Path(f.name)
