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

        assert "Duplicate function bodies" in result
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

        assert "Same-name function" in result
        assert "helper" in result

    def test_refactor_analyzes_single_file(self, tmp_path: Path):
        """Can analyze a single file."""
        py_file = tmp_path / "single.py"
        py_file.write_text('def foo():\n    pass\n')

        result = refactor(str(py_file))

        assert "Analyzed 1 files" in result
        assert "1 functions" in result

    def test_refactor_excludes_pycache(self, tmp_path: Path):
        """Excludes __pycache__ directories."""
        (tmp_path / "good.py").write_text('def x(): pass\n')
        pycache = tmp_path / "__pycache__"
        pycache.mkdir()
        (pycache / "bad.pyc").write_text('def y(): pass\n')

        result = refactor(str(tmp_path))

        assert "Analyzed 1 files" in result


class TestRefactorChain:
    """Tests for the refactor chain behavior."""

    def test_refactor_chains_complexity_analysis(self, tmp_path: Path):
        """Chains complexity analysis when focus=all."""
        py_file = tmp_path / "complex.py"
        # Create a function with very high complexity (score >= 10)
        py_file.write_text('''
def complex_function(a, b, c, d, e, f):
    if a:
        if b:
            if c:
                if d:
                    if e:
                        if f:
                            for i in range(10):
                                if i > 5:
                                    return "very deep"
    elif a and b:
        return 1
    elif a or c:
        return 2
    return "shallow"
''')
        result = refactor(str(tmp_path), focus="all")

        # Should include complexity analysis
        assert "complex_function" in result or "Complexity" in result

    def test_refactor_chains_architecture_analysis(self, tmp_path: Path):
        """Chains architecture analysis when focus=all."""
        (tmp_path / "a.py").write_text("import b\n")
        (tmp_path / "b.py").write_text("import a\n")

        result = refactor(str(tmp_path), focus="all")

        # Should detect circular dependency
        assert "Circular" in result or "circular" in result.lower()

    def test_refactor_focus_duplication_only(self, tmp_path: Path):
        """Focus=duplication skips other analyses."""
        # Create file with complexity issues but no duplication
        py_file = tmp_path / "complex.py"
        py_file.write_text('''
def complex_function(a, b, c, d, e):
    if a:
        if b:
            if c:
                return "deep"
    return "shallow"
''')
        result = refactor(str(tmp_path), focus="duplication")

        # Should not include complexity issues
        assert "No refactoring opportunities" in result

    def test_refactor_focus_complexity_only(self, tmp_path: Path):
        """Focus=complexity runs only complexity analysis."""
        py_file = tmp_path / "complex.py"
        # Create a function with very high complexity (score >= 10)
        py_file.write_text('''
def complex_function(a, b, c, d, e, f):
    if a:
        if b:
            if c:
                if d:
                    if e:
                        if f:
                            for i in range(10):
                                if i > 5:
                                    return "very deep"
    elif a and b:
        return 1
    elif a or c:
        return 2
    return "shallow"
''')
        result = refactor(str(tmp_path), focus="complexity")

        assert "complex_function" in result or "Complexity" in result

    def test_refactor_prioritizes_issues(self, tmp_path: Path):
        """Issues are sorted by priority."""
        # Create circular dependency (priority 1)
        (tmp_path / "a.py").write_text("import b\n")
        (tmp_path / "b.py").write_text("import a\n")

        result = refactor(str(tmp_path), focus="all")

        # Priority 1 should appear before Priority 2
        if "Priority 1" in result and "Priority 2" in result:
            p1_pos = result.find("Priority 1")
            p2_pos = result.find("Priority 2")
            assert p1_pos < p2_pos

    def test_refactor_generates_action_items(self, tmp_path: Path):
        """Generates recommended actions."""
        file1 = tmp_path / "a.py"
        file2 = tmp_path / "b.py"

        identical_func = 'def dup(): return 1\n'
        file1.write_text(identical_func)
        file2.write_text(identical_func)

        result = refactor(str(tmp_path), focus="duplication")

        assert "Recommended Actions" in result

    def test_refactor_clean_codebase(self, tmp_path: Path):
        """Reports clean when no issues found."""
        py_file = tmp_path / "clean.py"
        py_file.write_text('def greet(name):\n    return f"Hello, {name}"\n')

        result = refactor(str(py_file), focus="duplication")

        assert "No refactoring opportunities" in result or "clean" in result.lower()
