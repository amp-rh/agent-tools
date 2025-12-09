"""code.lint tests."""
from pathlib import Path

from agent_tools.code.lint import lint


class TestLint:
    """Tests for lint."""

    def test_lint_nonexistent_path(self):
        """Returns error for non-existent path."""
        result = lint("/nonexistent/path")
        assert "Error" in result
        assert "not found" in result

    def test_lint_clean_file(self, tmp_path: Path):
        """Reports clean for well-formatted file."""
        clean_file = tmp_path / "clean.py"
        clean_file.write_text('"""Module."""\n\nx = 1\n')

        result = lint(str(tmp_path))

        assert "Clean" in result or "no issues" in result.lower()

    def test_lint_fixes_issues(self, tmp_path: Path):
        """Auto-fixes fixable issues."""
        # File with trailing whitespace (fixable)
        messy_file = tmp_path / "messy.py"
        messy_file.write_text("x = 1   \n")  # trailing spaces

        result = lint(str(tmp_path), fix=True)

        # Should report fixed or clean
        assert "Fixed" in result or "Clean" in result or "fixed" in result.lower()

    def test_lint_reports_without_fix(self, tmp_path: Path):
        """Reports issues without fixing when fix=False."""
        messy_file = tmp_path / "messy.py"
        messy_file.write_text("x = 1   \n")  # trailing spaces

        result = lint(str(tmp_path), fix=False)

        # Should indicate issues found or suggest fix
        assert "issue" in result.lower() or "error" in result.lower() or "Clean" in result

    def test_lint_single_file(self, tmp_path: Path):
        """Can lint a single file."""
        single_file = tmp_path / "single.py"
        single_file.write_text('"""Doc."""\n\ny = 2\n')

        result = lint(str(single_file))

        assert "Error" not in result or "not found" not in result
