"""Integration tests for cursor_usage.cli module."""

import re
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest
from typer.testing import CliRunner

from cursor_usage.cli import app
from tests.fixtures.sample_data import make_csv_content, make_csv_row

runner = CliRunner(env={"NO_COLOR": "1"})


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


@pytest.fixture
def csv_file_path() -> Iterator[Path]:
    """Create a temporary CSV file for CLI testing."""
    content = make_csv_content(
        [
            make_csv_row(
                date="2026-01-15T10:00:00.000Z",
                user="alice@example.com",
                model="claude-4.5-sonnet",
                cost="0.25",
            ),
            make_csv_row(
                date="2026-01-16T11:00:00.000Z",
                user="bob@example.com",
                model="claude-4.5-haiku",
                cost="0.10",
            ),
        ]
    )

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, encoding="utf-8"
    ) as f:
        f.write(content)
        f.flush()
        yield Path(f.name)


class TestAnalyzeCommand:
    """Tests for the analyze command."""

    def test_basic_analyze(self, csv_file_path: Path) -> None:
        """Basic analyze command outputs table."""
        result = runner.invoke(app, ["-f", str(csv_file_path)])

        assert result.exit_code == 0
        assert "2026-01" in result.output
        assert "Total" in result.output

    def test_file_not_found(self, tmp_path: Path) -> None:
        """Missing file returns error."""
        missing = tmp_path / "nonexistent.csv"
        result = runner.invoke(app, ["-f", str(missing)])

        assert result.exit_code != 0

    def test_output_file_option(self, csv_file_path: Path, tmp_path: Path) -> None:
        """--output/-o writes to file."""
        output = tmp_path / "result.txt"
        result = runner.invoke(app, ["-f", str(csv_file_path), "-o", str(output)])

        assert result.exit_code == 0
        assert output.exists()
        content = output.read_text()
        assert "2026-01" in content

    def test_breakdown_flag(self, csv_file_path: Path) -> None:
        """-b flag shows model breakdown."""
        result = runner.invoke(app, ["-f", str(csv_file_path), "-b"])

        assert result.exit_code == 0
        assert "sonnet-4-5" in result.output
        assert "haiku-4-5" in result.output

    def test_group_by_user_flag(self, csv_file_path: Path) -> None:
        """-g flag shows per-user breakdown."""
        result = runner.invoke(app, ["-f", str(csv_file_path), "-g"])

        assert result.exit_code == 0
        assert "alice@example.com" in result.output
        assert "bob@example.com" in result.output

    def test_anonymize_flag(self, csv_file_path: Path) -> None:
        """-a flag anonymizes emails (requires -g)."""
        result = runner.invoke(app, ["-f", str(csv_file_path), "-g", "-a"])

        assert result.exit_code == 0
        assert "alice@example.com" not in result.output
        assert "bob@example.com" not in result.output
        assert "User-" in result.output

    def test_breakdown_and_user_group_mutually_exclusive(
        self, csv_file_path: Path
    ) -> None:
        """-b and -g flags cannot be used together."""
        result = runner.invoke(app, ["-f", str(csv_file_path), "-b", "-g"])

        assert result.exit_code != 0
        assert "Cannot use both" in result.output

    def test_anonymize_requires_group_by_user(self, csv_file_path: Path) -> None:
        """-a flag requires -g flag."""
        result = runner.invoke(app, ["-f", str(csv_file_path), "-a"])

        assert result.exit_code != 0
        assert "requires" in result.output


class TestEmptyCsv:
    """Tests for empty/invalid CSV handling."""

    def test_empty_csv_header_only(self, tmp_path: Path) -> None:
        """CSV with only header shows error message."""
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text(
            "Date,User,Kind,Model,Max Mode,Input (w/ Cache Write),"
            "Input (w/o Cache Write),Cache Read,Output Tokens,Total Tokens,Cost\n"
        )

        result = runner.invoke(app, ["-f", str(csv_file)])

        assert result.exit_code == 1
        assert "No valid usage events" in result.output


class TestHelp:
    """Tests for help output."""

    def test_app_help(self) -> None:
        """--help shows usage information."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "Analyze" in result.output
        assert "Cursor" in result.output

    def test_analyze_help(self) -> None:
        """--help shows command options."""
        result = runner.invoke(app, ["--help"])
        output = strip_ansi(result.output)

        assert result.exit_code == 0
        assert "--file" in output
        assert "--breakdown" in output
        assert "--group-by-user" in output
        assert "--anonymize" in output
