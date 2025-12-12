"""code.architecture tests."""
from pathlib import Path

from agent_tools.code.architecture import architecture


class TestArchitecture:
    """Tests for architecture analysis."""

    def test_architecture_nonexistent_path(self):
        """Returns error for non-existent path."""
        result = architecture("/nonexistent/path")
        assert "Error" in result
        assert "not found" in result

    def test_architecture_no_python_files(self, tmp_path: Path):
        """Handles directory with no Python files."""
        (tmp_path / "readme.txt").write_text("hello")
        result = architecture(str(tmp_path))
        assert "No Python files found" in result

    def test_architecture_builds_import_graph(self, tmp_path: Path):
        """Builds a dependency graph from imports."""
        (tmp_path / "a.py").write_text("import b\n")
        (tmp_path / "b.py").write_text("import c\n")
        (tmp_path / "c.py").write_text("# no imports\n")

        result = architecture(str(tmp_path))

        # Should show the dependency structure
        assert "a" in result
        assert "b" in result
        assert "c" in result

    def test_architecture_detects_circular_dependency(self, tmp_path: Path):
        """Detects circular dependencies between modules."""
        (tmp_path / "a.py").write_text("import b\n")
        (tmp_path / "b.py").write_text("import a\n")

        result = architecture(str(tmp_path))

        assert "circular" in result.lower()
        assert "a" in result
        assert "b" in result

    def test_architecture_detects_three_way_cycle(self, tmp_path: Path):
        """Detects circular dependencies involving three or more modules."""
        (tmp_path / "a.py").write_text("import b\n")
        (tmp_path / "b.py").write_text("import c\n")
        (tmp_path / "c.py").write_text("import a\n")

        result = architecture(str(tmp_path))

        assert "circular" in result.lower()

    def test_architecture_from_import(self, tmp_path: Path):
        """Handles from...import statements."""
        (tmp_path / "main.py").write_text("from utils import helper\n")
        (tmp_path / "utils.py").write_text("def helper(): pass\n")

        result = architecture(str(tmp_path))

        assert "main" in result
        assert "utils" in result

    def test_architecture_detects_layer_violation(self, tmp_path: Path):
        """Detects when infrastructure imports from domain (wrong direction)."""
        # Create a layered structure
        domain = tmp_path / "domain"
        domain.mkdir()
        infra = tmp_path / "infrastructure"
        infra.mkdir()

        (domain / "__init__.py").write_text("")
        (infra / "__init__.py").write_text("")

        (domain / "entity.py").write_text("# Pure domain entity\n")
        # Infrastructure incorrectly importing from... wait, that's correct
        # The violation is: domain importing from infrastructure
        (domain / "service.py").write_text("from infrastructure import db\n")
        (infra / "db.py").write_text("# Database stuff\n")

        result = architecture(str(tmp_path))

        # Domain should not depend on infrastructure
        assert "violation" in result.lower() or "layer" in result.lower()

    def test_architecture_single_file(self, tmp_path: Path):
        """Can analyze a single file."""
        py_file = tmp_path / "single.py"
        py_file.write_text("import os\n")

        result = architecture(str(py_file))

        assert "single" in result

    def test_architecture_excludes_pycache(self, tmp_path: Path):
        """Excludes __pycache__ directories."""
        (tmp_path / "good.py").write_text("pass\n")
        pycache = tmp_path / "__pycache__"
        pycache.mkdir()
        (pycache / "bad.cpython-311.pyc").write_text("import evil\n")

        result = architecture(str(tmp_path))

        assert "evil" not in result

    def test_architecture_handles_syntax_error(self, tmp_path: Path):
        """Gracefully handles files with syntax errors."""
        good_file = tmp_path / "good.py"
        bad_file = tmp_path / "bad.py"

        good_file.write_text("import os\n")
        bad_file.write_text("import (\n")  # Syntax error

        result = architecture(str(tmp_path))

        # Should not crash, should report analyzing files
        assert "Analyzed" in result
        assert "2 files" in result  # Both files counted even if one has errors

    def test_architecture_no_issues_found(self, tmp_path: Path):
        """Reports clean when no issues found."""
        (tmp_path / "a.py").write_text("import os\n")
        (tmp_path / "b.py").write_text("import sys\n")

        result = architecture(str(tmp_path))

        result_lower = result.lower()
        assert "no" in result_lower
        assert any(word in result_lower for word in ("issue", "violation", "circular"))

    def test_architecture_relative_import(self, tmp_path: Path):
        """Handles relative imports."""
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        (pkg / "a.py").write_text("from . import b\n")
        (pkg / "b.py").write_text("pass\n")

        result = architecture(str(tmp_path))

        # Should recognize relative imports within package
        assert "pkg" in result or "a" in result

