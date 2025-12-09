"""code.refactor tests."""
from pathlib import Path

from agent_tools.code.refactor import refactor


class TestRefactor:
    """Tests for refactor."""

    def test_refactor_nonexistent_path(self):
        """Returns error for non-existent path."""
        result = refactor("/nonexistent/path")
        assert "Error" in result
        assert "not found" in result

    def test_refactor_no_python_files(self, tmp_path: Path):
        """Handles directory with no Python files."""
        (tmp_path / "readme.txt").write_text("hello")
        result = refactor(str(tmp_path))
        assert "No Python files found" in result

    def test_refactor_finds_duplicate_functions(self, tmp_path: Path):
        """Detects identical function bodies across files."""
        # Create two files with identical function
        file1 = tmp_path / "a.py"
        file2 = tmp_path / "b.py"

        identical_func = '''
def load_data():
    """Load the data."""
    return {"key": "value"}
'''
        file1.write_text(identical_func)
        file2.write_text(identical_func)

        result = refactor(str(tmp_path), focus="duplication")

        assert "Duplicate Function Bodies" in result
        assert "load_data" in result
        assert "a.py" in result
        assert "b.py" in result

    def test_refactor_finds_same_name_different_impl(self, tmp_path: Path):
        """Detects same-name functions with different implementations."""
        file1 = tmp_path / "a.py"
        file2 = tmp_path / "b.py"

        file1.write_text('def helper():\n    return 1\n')
        file2.write_text('def helper():\n    return 2\n')

        result = refactor(str(tmp_path), focus="duplication")

        assert "Same-Name Functions" in result
        assert "helper" in result

    def test_refactor_analyzes_single_file(self, tmp_path: Path):
        """Can analyze a single file."""
        py_file = tmp_path / "single.py"
        py_file.write_text('def foo():\n    pass\n')

        result = refactor(str(py_file))

        assert "Analyzed 1 files" in result
        assert "found 1 functions" in result

    def test_refactor_excludes_pycache(self, tmp_path: Path):
        """Excludes __pycache__ directories."""
        (tmp_path / "good.py").write_text('def x(): pass\n')
        pycache = tmp_path / "__pycache__"
        pycache.mkdir()
        (pycache / "bad.pyc").write_text('def y(): pass\n')

        result = refactor(str(tmp_path))

        assert "Analyzed 1 files" in result
