"""Tests for code/_formatters module."""
import pytest

from agent_tools.code._formatters import (
    format_header,
    format_issue_list,
    format_section,
    group_by_severity,
)


class TestFormatHeader:
    """Tests for format_header function."""

    def test_formats_title_with_path(self):
        """Should format title with path."""
        result = format_header("Complexity Analysis", "/path/to/code")
        assert "# Complexity Analysis: /path/to/code" in result

    def test_includes_file_count(self):
        """Should include file count."""
        result = format_header("Analysis", "/path", file_count=5)
        assert "5 files" in result

    def test_includes_function_count(self):
        """Should include function count."""
        result = format_header("Analysis", "/path", file_count=3, func_count=10)
        assert "10 functions" in result

    def test_singular_file(self):
        """Should use singular 'file' for count of 1."""
        result = format_header("Analysis", "/path", file_count=1)
        assert "1 file" in result
        assert "1 files" not in result


class TestGroupBySeverity:
    """Tests for group_by_severity function."""

    def test_groups_by_score(self):
        """Should group items by score thresholds."""
        items = [
            {"name": "high", "score": 15},
            {"name": "medium", "score": 7},
            {"name": "low", "score": 3},
        ]
        result = group_by_severity(items, score_key="score")
        assert len(result["high"]) == 1
        assert len(result["medium"]) == 1
        assert len(result["low"]) == 1

    def test_custom_thresholds(self):
        """Should respect custom thresholds."""
        items = [{"score": 5}, {"score": 10}, {"score": 20}]
        result = group_by_severity(
            items, score_key="score", high_threshold=15, medium_threshold=8
        )
        assert len(result["high"]) == 1
        assert len(result["medium"]) == 1
        assert len(result["low"]) == 1

    def test_empty_input(self):
        """Should handle empty input."""
        result = group_by_severity([], score_key="score")
        assert result == {"high": [], "medium": [], "low": []}


class TestFormatSection:
    """Tests for format_section function."""

    def test_formats_section_with_heading(self):
        """Should format section with heading."""
        result = format_section("Issues", ["- item 1", "- item 2"])
        assert "## Issues" in result
        assert "- item 1" in result
        assert "- item 2" in result

    def test_empty_items_returns_empty(self):
        """Should return empty string for no items."""
        result = format_section("Empty", [])
        assert result == ""

    def test_with_description(self):
        """Should include description if provided."""
        result = format_section("Title", ["item"], description="Some context")
        assert "Some context" in result


class TestFormatIssueList:
    """Tests for format_issue_list function."""

    def test_formats_simple_issues(self):
        """Should format list of issue strings."""
        issues = ["Too complex", "Too long"]
        result = format_issue_list(issues)
        assert "- Too complex" in result
        assert "- Too long" in result

    def test_empty_issues(self):
        """Should handle empty issues list."""
        result = format_issue_list([])
        assert result == ""

    def test_with_prefix(self):
        """Should support custom prefix."""
        issues = ["item"]
        result = format_issue_list(issues, prefix="* ")
        assert "* item" in result

