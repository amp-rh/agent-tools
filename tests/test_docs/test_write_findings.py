"""docs.write-findings tests."""
import json

from agent_tools.docs.write_findings import write_findings


class TestWriteFindings:
    """Tests for write_findings."""

    def test_creates_file(self, tmp_path):
        """Verify write_findings creates the output file."""
        output = tmp_path / "findings.md"

        result = write_findings(
            path=str(output),
            topic="Test Topic",
            problem="Test problem statement",
            attempts=json.dumps([{"name": "Attempt 1", "result": "Failed"}]),
            insights=json.dumps(["Insight 1"]),
            recommendations=json.dumps(["Recommendation 1"]),
        )

        assert output.exists()
        assert "Created:" in result

    def test_contains_all_sections(self, tmp_path):
        """Verify output contains all required sections."""
        output = tmp_path / "findings.md"

        write_findings(
            path=str(output),
            topic="My Topic",
            problem="The problem",
            attempts=json.dumps([{"name": "Try 1", "result": "Worked"}]),
            insights=json.dumps(["We learned X"]),
            recommendations=json.dumps(["Do Y"]),
        )

        content = output.read_text()
        assert "# My Topic" in content
        assert "## Problem" in content
        assert "## What We Tried" in content
        assert "## Key Insights" in content
        assert "## Recommendations" in content

    def test_multiple_attempts(self, tmp_path):
        """Verify multiple attempts are rendered."""
        output = tmp_path / "findings.md"

        write_findings(
            path=str(output),
            topic="Topic",
            problem="Problem",
            attempts=json.dumps([
                {"name": "First", "result": "Failed"},
                {"name": "Second", "result": "Partial"},
                {"name": "Third", "result": "Success"},
            ]),
            insights=json.dumps(["Insight"]),
            recommendations=json.dumps(["Rec"]),
        )

        content = output.read_text()
        assert "### First" in content
        assert "### Second" in content
        assert "### Third" in content

    def test_creates_parent_directories(self, tmp_path):
        """Verify parent directories are created if needed."""
        output = tmp_path / "nested" / "deep" / "findings.md"

        write_findings(
            path=str(output),
            topic="Topic",
            problem="Problem",
            attempts=json.dumps([{"name": "A", "result": "B"}]),
            insights=json.dumps(["I"]),
            recommendations=json.dumps(["R"]),
        )

        assert output.exists()
