"""code.analyze tests."""
from pathlib import Path

from agent_tools.code.analyze import analyze


class TestAnalyze:
    """Tests for the analyze orchestrator."""

    def test_analyze_nonexistent_path(self):
        """Returns error for non-existent path."""
        result = analyze("/nonexistent/path")
        assert "Error" in result
        assert "not found" in result

    def test_analyze_no_python_files(self, tmp_path: Path):
        """Handles directory with no Python files."""
        (tmp_path / "readme.txt").write_text("hello")
        result = analyze(str(tmp_path))
        assert "No Python files found" in result

    def test_analyze_all_focus(self, tmp_path: Path):
        """Default focus=all runs all analyzers and finds issues."""
        # Create files with both complexity and architecture issues
        (tmp_path / "a.py").write_text('''
import b

def complex_one(a, b, c, d, e):
    if a:
        if b:
            for i in range(10):
                if c:
                    return i
    return 0
''')
        (tmp_path / "b.py").write_text("import a\n")  # Circular dependency

        result = analyze(str(tmp_path))

        # Should include complexity analysis
        assert "complexity" in result.lower()
        # Should include architecture issues (circular dependency)
        assert "circular" in result.lower()

    def test_analyze_complexity_focus(self, tmp_path: Path):
        """focus=complexity only runs complexity analysis."""
        py_file = tmp_path / "example.py"
        py_file.write_text('''
def complex_one(a, b, c, d, e):
    if a:
        if b:
            return 2
    return 0
''')
        result = analyze(str(tmp_path), focus="complexity")

        # Should include complexity analysis
        assert "complexity" in result.lower()
        # Should NOT include detailed architecture analysis
        assert "circular" not in result.lower()

    def test_analyze_architecture_focus(self, tmp_path: Path):
        """focus=architecture only runs architecture analysis."""
        (tmp_path / "a.py").write_text("import b\n")
        (tmp_path / "b.py").write_text("import a\n")  # Circular

        result = analyze(str(tmp_path), focus="architecture")

        # Should include architecture analysis
        assert "circular" in result.lower()

    def test_analyze_naming_focus(self, tmp_path: Path):
        """focus=naming analyzes naming conventions."""
        py_file = tmp_path / "example.py"
        py_file.write_text('''
def x():
    return 1

def calculateSomethingVeryImportant():
    return 2

def _private_helper():
    return 3
''')
        result = analyze(str(tmp_path), focus="naming")

        # Should mention naming issues
        assert "naming" in result.lower() or "name" in result.lower()

    def test_analyze_single_file(self, tmp_path: Path):
        """Can analyze a single file."""
        py_file = tmp_path / "single.py"
        py_file.write_text("def foo():\n    pass\n")

        result = analyze(str(py_file))

        assert "single" in result or "1 file" in result.lower()

    def test_analyze_includes_recommendations(self, tmp_path: Path):
        """Includes actionable recommendations."""
        py_file = tmp_path / "problematic.py"
        py_file.write_text('''
def very_complex(a, b, c, d, e, f):
    if a:
        if b:
            if c:
                if d:
                    if e:
                        return f
    return 0
''')
        result = analyze(str(tmp_path))

        # Should include recommendations
        assert "recommend" in result.lower()

    def test_analyze_clean_codebase(self, tmp_path: Path):
        """Reports clean for well-structured code."""
        py_file = tmp_path / "clean.py"
        py_file.write_text('''
def greet(name):
    """Greet a person by name."""
    return f"Hello, {name}"

def add(a, b):
    """Add two numbers."""
    return a + b
''')
        result = analyze(str(tmp_path))

        # Should indicate no major issues
        assert "clean" in result.lower() or "no" in result.lower()

    def test_analyze_summary_section(self, tmp_path: Path):
        """Output includes a summary section."""
        py_file = tmp_path / "example.py"
        py_file.write_text("def foo(): pass\n")

        result = analyze(str(tmp_path))

        # Should have a summary
        assert "summary" in result.lower() or "analyzed" in result.lower()

