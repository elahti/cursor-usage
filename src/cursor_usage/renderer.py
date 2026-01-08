"""ASCII table rendering with box-drawing characters.

Renders AggregatedStats into formatted tables matching
the expected output format.
"""

import hashlib

from cursor_usage.formatter import format_currency, format_number
from cursor_usage.models import AggregatedStats

# Box-drawing characters
BOX_TL = "┌"
BOX_TR = "┐"
BOX_BL = "└"
BOX_BR = "┘"
BOX_H = "─"
BOX_V = "│"
BOX_LJ = "├"
BOX_RJ = "┤"
BOX_TJ = "┬"
BOX_BJ = "┴"
BOX_X = "┼"

# Column definitions: (name, width, is_numeric)
# Without -b flag
COLUMNS_NO_BREAKDOWN: list[tuple[str, int, bool]] = [
    ("Month", 10, False),
    ("Models", 35, False),
    ("Input", 12, True),
    ("Output", 11, True),
    ("Cache Create", 15, True),
    ("Cache Read", 14, True),
    ("Total Tokens", 15, True),
    ("Cost (USD)", 13, True),
]

# With -b flag (wider Month column for model breakdown rows)
COLUMNS_WITH_BREAKDOWN: list[tuple[str, int, bool]] = [
    ("Month", 24, False),
    ("Models", 35, False),
    ("Input", 12, True),
    ("Output", 11, True),
    ("Cache Create", 15, True),
    ("Cache Read", 14, True),
    ("Total Tokens", 15, True),
    ("Cost (USD)", 13, True),
]

# With -g flag (wider Month column for user breakdown rows, no Models column)
COLUMNS_GROUP_BY_USER: list[tuple[str, int, bool]] = [
    ("Month", 33, False),
    ("Input", 12, True),
    ("Output", 11, True),
    ("Cache Create", 15, True),
    ("Cache Read", 14, True),
    ("Total Tokens", 15, True),
    ("Cost (USD)", 13, True),
]


def _get_columns(
    show_models: bool, group_by_user: bool = False
) -> list[tuple[str, int, bool]]:
    """Get column definitions based on display options."""
    if group_by_user:
        return COLUMNS_GROUP_BY_USER
    if show_models:
        return COLUMNS_WITH_BREAKDOWN
    return COLUMNS_NO_BREAKDOWN


def _anonymize_email(email: str) -> str:
    """Anonymize an email address using a hash-based approach.

    Args:
        email: The email address to anonymize.

    Returns:
        An anonymized identifier in the format 'User-{hash}'.
    """
    hash_prefix = hashlib.sha256(email.encode()).hexdigest()[:8]
    return f"User-{hash_prefix}"


def render_table(
    monthly_stats: list[AggregatedStats],
    total: AggregatedStats,
    *,
    show_models: bool = False,
    group_by_user: bool = False,
    anonymize: bool = False,
) -> str:
    """Render statistics as an ASCII table.

    Args:
        monthly_stats: List of monthly aggregations.
        total: Grand total aggregation.
        show_models: Whether to include per-model breakdown rows.
        group_by_user: Whether to include per-user breakdown rows.
        anonymize: Whether to anonymize user emails in output.

    Returns:
        Complete table as a string.
    """
    columns = _get_columns(show_models, group_by_user)
    lines: list[str] = []

    lines.append(_render_border("top", columns))
    lines.append(_render_header(columns))

    for stats in monthly_stats:
        lines.append(_render_separator(columns))
        if group_by_user:
            lines.extend(_render_data_row_grouped(stats, columns))
            lines.extend(_render_user_breakdown_rows(stats, columns, anonymize))
        else:
            lines.extend(_render_data_row(stats, columns))
            if show_models:
                lines.extend(_render_model_breakdown_rows(stats, columns))

    lines.append(_render_separator(columns))
    lines.append(_render_total_row(total, columns, group_by_user))
    lines.append(_render_border("bottom", columns))

    return "\n".join(lines)


def _render_border(position: str, columns: list[tuple[str, int, bool]]) -> str:
    """Render top or bottom border line."""
    if position == "top":
        left, mid, right = BOX_TL, BOX_TJ, BOX_TR
    else:
        left, mid, right = BOX_BL, BOX_BJ, BOX_BR

    segments = [BOX_H * width for _, width, _ in columns]
    return left + mid.join(segments) + right


def _render_separator(columns: list[tuple[str, int, bool]]) -> str:
    """Render horizontal separator between rows."""
    segments = [BOX_H * width for _, width, _ in columns]
    return BOX_LJ + BOX_X.join(segments) + BOX_RJ


def _render_header(columns: list[tuple[str, int, bool]]) -> str:
    """Render the header row."""
    cells: list[str] = []
    for name, width, is_numeric in columns:
        if is_numeric:
            cells.append(f" {name:>{width - 2}} ")
        else:
            cells.append(f" {name:<{width - 2}} ")
    return BOX_V + BOX_V.join(cells) + BOX_V


def _render_data_row(
    stats: AggregatedStats,
    columns: list[tuple[str, int, bool]],
) -> list[str]:
    """Render a data row with multi-line model support.

    Returns list of lines to support multi-line model display.
    """
    sorted_models = sorted(stats.models)

    # Main row with month totals and model list
    first_model = f"- {sorted_models[0]}" if sorted_models else ""
    values: list[str] = [
        stats.month,
        first_model,
        format_number(stats.input_tokens),
        format_number(stats.output_tokens),
        format_number(stats.cache_create),
        format_number(stats.cache_read),
        format_number(stats.total_tokens),
        format_currency(stats.cost),
    ]

    lines = [_format_row(values, columns)]

    # Additional rows for remaining model names
    for model in sorted_models[1:]:
        empty_row: list[str] = [""] * len(columns)
        empty_row[1] = f"- {model}"
        lines.append(_format_row(empty_row, columns))

    return lines


def _render_model_breakdown_rows(
    stats: AggregatedStats,
    columns: list[tuple[str, int, bool]],
) -> list[str]:
    """Render per-model breakdown rows with separators.

    Returns list of lines including separators before each model row.
    """
    lines: list[str] = []

    # Sort models by cost (highest first) for breakdown display
    sorted_models = sorted(
        stats.model_stats.keys(),
        key=lambda m: stats.model_stats[m].cost,
        reverse=True,
    )

    for model in sorted_models:
        model_stat = stats.model_stats[model]
        lines.append(_render_separator(columns))
        values: list[str] = [
            f"  └─ {model}",
            "",
            format_number(model_stat.input_tokens),
            format_number(model_stat.output_tokens),
            format_number(model_stat.cache_create),
            format_number(model_stat.cache_read),
            format_number(model_stat.total_tokens),
            format_currency(model_stat.cost),
        ]
        lines.append(_format_row(values, columns))

    return lines


def _render_data_row_grouped(
    stats: AggregatedStats,
    columns: list[tuple[str, int, bool]],
) -> list[str]:
    """Render a data row for grouped-by-user output (no Models column).

    Returns list of lines.
    """
    values: list[str] = [
        stats.month,
        format_number(stats.input_tokens),
        format_number(stats.output_tokens),
        format_number(stats.cache_create),
        format_number(stats.cache_read),
        format_number(stats.total_tokens),
        format_currency(stats.cost),
    ]

    return [_format_row(values, columns)]


def _render_user_breakdown_rows(
    stats: AggregatedStats,
    columns: list[tuple[str, int, bool]],
    anonymize: bool = False,
) -> list[str]:
    """Render per-user breakdown rows with separators.

    Args:
        stats: Aggregated statistics containing user data.
        columns: Column definitions for formatting.
        anonymize: Whether to anonymize user emails in output.

    Returns:
        List of lines including separators before each user row.
    """
    lines: list[str] = []

    # Sort users by cost (highest first) for breakdown display
    sorted_users = sorted(
        stats.user_stats.keys(),
        key=lambda u: stats.user_stats[u].cost,
        reverse=True,
    )

    for user in sorted_users:
        user_stat = stats.user_stats[user]
        display_name = _anonymize_email(user) if anonymize else user
        lines.append(_render_separator(columns))
        values: list[str] = [
            f"  └─ {display_name}",
            format_number(user_stat.input_tokens),
            format_number(user_stat.output_tokens),
            format_number(user_stat.cache_create),
            format_number(user_stat.cache_read),
            format_number(user_stat.total_tokens),
            format_currency(user_stat.cost),
        ]
        lines.append(_format_row(values, columns))

    return lines


def _render_total_row(
    total: AggregatedStats,
    columns: list[tuple[str, int, bool]],
    group_by_user: bool = False,
) -> str:
    """Render the grand total row."""
    if group_by_user:
        values: list[str] = [
            "Total",
            format_number(total.input_tokens),
            format_number(total.output_tokens),
            format_number(total.cache_create),
            format_number(total.cache_read),
            format_number(total.total_tokens),
            format_currency(total.cost),
        ]
    else:
        values = [
            "Total",
            "",
            format_number(total.input_tokens),
            format_number(total.output_tokens),
            format_number(total.cache_create),
            format_number(total.cache_read),
            format_number(total.total_tokens),
            format_currency(total.cost),
        ]
    return _format_row(values, columns)


def _format_row(values: list[str], columns: list[tuple[str, int, bool]]) -> str:
    """Format a list of values into a table row."""
    cells: list[str] = []
    for (_, width, is_numeric), value in zip(columns, values, strict=True):
        if is_numeric and value:
            cells.append(f" {value:>{width - 2}} ")
        else:
            cells.append(f" {value:<{width - 2}} ")
    return BOX_V + BOX_V.join(cells) + BOX_V
