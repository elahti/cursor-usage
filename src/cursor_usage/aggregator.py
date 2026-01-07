"""Aggregation logic for grouping usage events.

Provides functions to group events by month and compute
aggregated statistics.
"""

from collections import defaultdict

from cursor_usage.models import AggregatedStats, UsageEvent


def aggregate_by_month(events: list[UsageEvent]) -> list[AggregatedStats]:
    """Aggregate usage events by month.

    Groups events by their YYYY-MM month key and computes
    totals for each group.

    Args:
        events: List of usage events to aggregate.

    Returns:
        List of AggregatedStats sorted by month (ascending).
    """
    by_month: dict[str, AggregatedStats] = defaultdict(
        lambda: AggregatedStats(month="")
    )

    for event in events:
        month_key = event.month_key
        if by_month[month_key].month == "":
            by_month[month_key].month = month_key
        by_month[month_key].add(event)

    return sorted(by_month.values(), key=lambda s: s.month)


def compute_grand_total(monthly_stats: list[AggregatedStats]) -> AggregatedStats:
    """Compute grand total from monthly aggregations.

    Args:
        monthly_stats: List of monthly AggregatedStats.

    Returns:
        AggregatedStats with month="Total" containing sums.
    """
    total = AggregatedStats(month="Total")
    for stats in monthly_stats:
        total.merge(stats)
    return total
