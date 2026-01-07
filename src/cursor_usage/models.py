"""Data models for cursor usage analysis.

This module defines the Pydantic models used for parsing CSV data
and representing aggregated statistics.
"""

from datetime import datetime
from decimal import Decimal
from typing import Self

from pydantic import BaseModel, Field


class UsageEvent(BaseModel):
    """Represents a single usage event from the CSV export.

    Each row in the CSV file maps to one UsageEvent instance,
    capturing token usage and cost for a single API call.
    """

    date: datetime
    user: str
    kind: str
    model: str
    max_mode: bool
    cache_write: int = Field(ge=0, description="Input tokens with cache write")
    input_no_cache: int = Field(ge=0, description="Input tokens without cache write")
    cache_read: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)
    cost: Decimal = Field(ge=0)

    @property
    def month_key(self) -> str:
        """Return YYYY-MM format for grouping."""
        return self.date.strftime("%Y-%m")

    @property
    def normalized_model(self) -> str:
        """Return simplified model name for display.

        Transforms verbose model names to concise display names:
        - claude-4.5-haiku* -> haiku-4-5
        - claude-4.5-sonnet* -> sonnet-4-5
        - claude-4.5-opus* -> opus-4-5
        - gpt-5.2 -> gpt-5-2
        """
        model_lower = self.model.lower()
        if "haiku" in model_lower:
            return "haiku-4-5"
        if "opus" in model_lower:
            return "opus-4-5"
        if "sonnet" in model_lower:
            return "sonnet-4-5"
        # Normalize gpt-5.2 to gpt-5-2 for consistency
        if model_lower == "gpt-5.2":
            return "gpt-5-2"
        return self.model


class ModelStats(BaseModel):
    """Statistics for a single model within a time period."""

    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    cache_create: int = Field(default=0, ge=0)
    cache_read: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    cost: Decimal = Field(default=Decimal("0.00"))


class UserStats(BaseModel):
    """Statistics for a single user within a time period."""

    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    cache_create: int = Field(default=0, ge=0)
    cache_read: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    cost: Decimal = Field(default=Decimal("0.00"))


class AggregatedStats(BaseModel):
    """Aggregated statistics for a month or total.

    Accumulates token counts and costs across multiple UsageEvents,
    supporting incremental updates via the add() method.
    """

    month: str
    user: str | None = None
    models: set[str] = Field(default_factory=set)
    user_stats: dict[str, UserStats] = Field(default_factory=dict)
    model_stats: dict[str, ModelStats] = Field(default_factory=dict)
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    cache_create: int = Field(default=0, ge=0)
    cache_read: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    cost: Decimal = Field(default=Decimal("0.00"))

    def add(self, event: UsageEvent) -> Self:
        """Add a usage event to this aggregation.

        Args:
            event: The usage event to incorporate.

        Returns:
            Self for method chaining.
        """
        model_name = event.normalized_model
        self.models.add(model_name)

        # Track per-model stats
        if model_name not in self.model_stats:
            self.model_stats[model_name] = ModelStats()
        model_stat = self.model_stats[model_name]
        model_stat.input_tokens += event.input_no_cache
        model_stat.output_tokens += event.output_tokens
        model_stat.cache_create += event.cache_write
        model_stat.cache_read += event.cache_read
        model_stat.total_tokens += event.total_tokens
        model_stat.cost += event.cost

        # Track per-user stats
        user = event.user
        if user not in self.user_stats:
            self.user_stats[user] = UserStats()
        user_stat = self.user_stats[user]
        user_stat.input_tokens += event.input_no_cache
        user_stat.output_tokens += event.output_tokens
        user_stat.cache_create += event.cache_write
        user_stat.cache_read += event.cache_read
        user_stat.total_tokens += event.total_tokens
        user_stat.cost += event.cost

        # Track aggregate totals
        self.input_tokens += event.input_no_cache
        self.output_tokens += event.output_tokens
        self.cache_create += event.cache_write
        self.cache_read += event.cache_read
        self.total_tokens += event.total_tokens
        self.cost += event.cost
        return self

    def merge(self, other: "AggregatedStats") -> Self:
        """Merge another AggregatedStats into this one.

        Args:
            other: The stats to merge in.

        Returns:
            Self for method chaining.
        """
        self.models.update(other.models)

        # Merge user stats
        for user, stats in other.user_stats.items():
            if user not in self.user_stats:
                self.user_stats[user] = UserStats()
            self.user_stats[user].input_tokens += stats.input_tokens
            self.user_stats[user].output_tokens += stats.output_tokens
            self.user_stats[user].cache_create += stats.cache_create
            self.user_stats[user].cache_read += stats.cache_read
            self.user_stats[user].total_tokens += stats.total_tokens
            self.user_stats[user].cost += stats.cost

        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens
        self.cache_create += other.cache_create
        self.cache_read += other.cache_read
        self.total_tokens += other.total_tokens
        self.cost += other.cost
        return self
