"""code.complexity tests."""
from pathlib import Path

from agent_tools.code.complexity import complexity


class TestComplexity:
    """Tests for complexity analysis."""

    def test_complexity_nonexistent_path(self):
        """Returns error for non-existent path."""
        result = complexity("/nonexistent/path")
        assert "Error" in result
        assert "not found" in result

    def test_complexity_no_python_files(self, tmp_path: Path):
        """Handles directory with no Python files."""
        (tmp_path / "readme.txt").write_text("hello")
        result = complexity(str(tmp_path))
        assert "No Python files found" in result

    def test_complexity_simple_function(self, tmp_path: Path):
        """Analyzes a simple function with low complexity."""
        py_file = tmp_path / "simple.py"
        py_file.write_text('''
def greet(name):
    return f"Hello, {name}"
''')
        result = complexity(str(tmp_path))

        assert "greet" in result
        assert "simple.py" in result

    def test_complexity_detects_high_cyclomatic(self, tmp_path: Path):
        """Detects functions with high cyclomatic complexity."""
        py_file = tmp_path / "branchy.py"
        py_file.write_text('''
def process(a, b, c, d):
    if a:
        if b:
            return 1
        elif c:
            return 2
        else:
            return 3
    elif d:
        for i in range(10):
            if i > 5:
                return 4
    else:
        while True:
            if a or b:
                break
    return 0
''')
        result = complexity(str(tmp_path))

        assert "process" in result
        assert "cyclomatic" in result.lower() or "complexity" in result.lower()

    def test_complexity_detects_long_function(self, tmp_path: Path):
        """Detects functions that are too long."""
        py_file = tmp_path / "long.py"
        # Create a function with 30+ lines
        lines = ["def long_function():"]
        for i in range(35):
            lines.append(f"    x{i} = {i}")
        lines.append("    return x0")
        py_file.write_text("\n".join(lines))

        result = complexity(str(tmp_path))

        assert "long_function" in result
        assert "lines" in result.lower() or "length" in result.lower()

    def test_complexity_detects_deep_nesting(self, tmp_path: Path):
        """Detects deeply nested code."""
        py_file = tmp_path / "nested.py"
        py_file.write_text('''
def deeply_nested(x):
    if x > 0:
        if x > 1:
            if x > 2:
                if x > 3:
                    if x > 4:
                        return "deep"
    return "shallow"
''')
        result = complexity(str(tmp_path))

        assert "deeply_nested" in result
        assert "nest" in result.lower() or "depth" in result.lower()

    def test_complexity_detects_many_parameters(self, tmp_path: Path):
        """Detects functions with too many parameters."""
        py_file = tmp_path / "params.py"
        py_file.write_text('''
def too_many_params(a, b, c, d, e, f, g, h):
    return a + b + c + d + e + f + g + h
''')
        result = complexity(str(tmp_path))

        assert "too_many_params" in result
        assert "param" in result.lower()

    def test_complexity_ranks_functions(self, tmp_path: Path):
        """Ranks functions by complexity, worst first."""
        py_file = tmp_path / "mixed.py"
        py_file.write_text('''
def simple():
    return 1

def medium(x):
    if x:
        return 2
    return 3

def complex_one(a, b, c):
    if a:
        if b:
            for i in range(10):
                if c:
                    return i
    return 0
''')
        result = complexity(str(tmp_path))

        # complex_one should appear before simple in the output
        complex_pos = result.find("complex_one")
        simple_pos = result.find("simple")
        assert complex_pos < simple_pos, "Functions should be ranked by complexity"

    def test_complexity_single_file(self, tmp_path: Path):
        """Can analyze a single file."""
        py_file = tmp_path / "single.py"
        py_file.write_text("def foo():\n    pass\n")

        result = complexity(str(py_file))

        assert "foo" in result
        assert "1 file" in result.lower()

    def test_complexity_excludes_pycache(self, tmp_path: Path):
        """Excludes __pycache__ directories."""
        (tmp_path / "good.py").write_text("def x(): pass\n")
        pycache = tmp_path / "__pycache__"
        pycache.mkdir()
        (pycache / "bad.cpython-311.pyc").write_text("def y(): pass\n")

        result = complexity(str(tmp_path))

        assert "1 file" in result.lower()

    def test_complexity_threshold_filter(self, tmp_path: Path):
        """Can filter by minimum complexity threshold."""
        py_file = tmp_path / "mixed.py"
        py_file.write_text('''
def simple():
    return 1

def complex_one(a, b):
    if a:
        if b:
            return 2
    return 0
''')
        # Only show functions above threshold
        result = complexity(str(tmp_path), threshold=3)

        assert "complex_one" in result
        # simple should be filtered out (complexity 1)
        assert "simple" not in result or "below threshold" in result.lower()

    def test_complexity_handles_syntax_error(self, tmp_path: Path):
        """Gracefully handles files with syntax errors."""
        good_file = tmp_path / "good.py"
        bad_file = tmp_path / "bad.py"

        good_file.write_text("def valid(): pass\n")
        bad_file.write_text("def invalid( pass\n")  # Syntax error

        result = complexity(str(tmp_path))

        assert "valid" in result
        # Should not crash, may mention skipped file

