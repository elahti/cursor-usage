"""Command-line interface for cursor usage analysis.

Provides the main entry point and argument handling.
"""

from pathlib import Path
from typing import Annotated

import typer

from cursor_usage.aggregator import aggregate_by_month, compute_grand_total
from cursor_usage.parser import parse_csv_file
from cursor_usage.renderer import render_table

app = typer.Typer(
    name="cursor-usage",
    help="Analyze Cursor IDE usage statistics from CSV exports.",
    add_completion=False,
)


@app.command()
def analyze(
    csv_file: Annotated[
        Path,
        typer.Option(
            "--file",
            "-f",
            help="Path to the CSV file exported from Cursor.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            resolve_path=True,
        ),
    ],
    output_file: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Write output to file instead of stdout.",
        ),
    ] = None,
    breakdown: Annotated[
        bool,
        typer.Option(
            "--breakdown",
            "-b",
            help="Show model-specific breakdown per month.",
        ),
    ] = False,
) -> None:
    """Analyze usage statistics from a Cursor CSV export.

    Parses the CSV file and displays aggregated statistics
    grouped by month with totals for token usage and costs.
    """
    events = parse_csv_file(csv_file)

    if not events:
        typer.echo("No valid usage events found in the CSV file.", err=True)
        raise typer.Exit(code=1)

    monthly_stats = aggregate_by_month(events)
    total = compute_grand_total(monthly_stats)

    table = render_table(monthly_stats, total, show_models=breakdown)

    if output_file:
        output_file.write_text(table + "\n", encoding="utf-8")
        typer.echo(f"Output written to {output_file}")
    else:
        typer.echo(table)


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
