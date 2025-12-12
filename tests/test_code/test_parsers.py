"""Tests for code/_parsers module."""
import ast
import tempfile
from pathlib import Path

import pytest

from agent_tools.code._parsers import analyze_with_visitor, collect_py_files, parse_file


class TestCollectPyFiles:
    """Tests for collect_py_files function."""

    def test_collects_single_file(self, tmp_path: Path):
        """Should return single file when given a .py file."""
        py_file = tmp_path / "test.py"
        py_file.write_text("x = 1")

        result = collect_py_files(py_file)
        assert result == [py_file]

    def test_returns_empty_for_non_py_file(self, tmp_path: Path):
        """Should return empty list for non-Python files."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("hello")

        result = collect_py_files(txt_file)
        assert result == []

    def test_collects_from_directory(self, tmp_path: Path):
        """Should collect all .py files from directory."""
        (tmp_path / "a.py").write_text("x = 1")
        (tmp_path / "b.py").write_text("y = 2")
        (tmp_path / "c.txt").write_text("not python")

        result = collect_py_files(tmp_path)
        assert len(result) == 2
        assert all(f.suffix == ".py" for f in result)

    def test_excludes_pycache(self, tmp_path: Path):
        """Should exclude __pycache__ directories."""
        (tmp_path / "main.py").write_text("x = 1")
        pycache = tmp_path / "__pycache__"
        pycache.mkdir()
        (pycache / "cached.py").write_text("cached")

        result = collect_py_files(tmp_path)
        assert len(result) == 1
        assert "__pycache__" not in str(result[0])

    def test_excludes_hidden_dirs(self, tmp_path: Path):
        """Should exclude hidden directories."""
        (tmp_path / "visible.py").write_text("x = 1")
        hidden = tmp_path / ".hidden"
        hidden.mkdir()
        (hidden / "secret.py").write_text("secret")

        result = collect_py_files(tmp_path)
        assert len(result) == 1
        assert ".hidden" not in str(result[0])

    def test_returns_sorted_list(self, tmp_path: Path):
        """Should return files in sorted order."""
        (tmp_path / "z.py").write_text("z")
        (tmp_path / "a.py").write_text("a")
        (tmp_path / "m.py").write_text("m")

        result = collect_py_files(tmp_path)
        names = [f.name for f in result]
        assert names == ["a.py", "m.py", "z.py"]


class TestParseFile:
    """Tests for parse_file function."""

    def test_parses_valid_python(self, tmp_path: Path):
        """Should parse valid Python code."""
        py_file = tmp_path / "valid.py"
        py_file.write_text("def foo(): pass")

        result = parse_file(py_file)
        assert result is not None
        assert isinstance(result, ast.Module)

    def test_returns_none_for_syntax_error(self, tmp_path: Path):
        """Should return None for files with syntax errors."""
        py_file = tmp_path / "invalid.py"
        py_file.write_text("def foo(: pass")  # syntax error

        result = parse_file(py_file)
        assert result is None

    def test_returns_none_for_encoding_error(self, tmp_path: Path):
        """Should return None for files with encoding issues."""
        py_file = tmp_path / "bad_encoding.py"
        py_file.write_bytes(b"\xff\xfe invalid utf-8")

        result = parse_file(py_file)
        assert result is None


class TestAnalyzeWithVisitor:
    """Tests for analyze_with_visitor function."""

    def test_collects_visitor_results(self, tmp_path: Path):
        """Should collect results from visitor."""
        py_file = tmp_path / "funcs.py"
        py_file.write_text("def foo(): pass\ndef bar(): pass")

        class FuncCollector(ast.NodeVisitor):
            def __init__(self):
                self.results = []

            def visit_FunctionDef(self, node):
                self.results.append(node.name)
                self.generic_visit(node)

        visitor = FuncCollector()
        result = analyze_with_visitor(py_file, visitor, "results")
        assert result == ["foo", "bar"]

    def test_returns_empty_for_invalid_file(self, tmp_path: Path):
        """Should return empty list for unparseable files."""
        py_file = tmp_path / "invalid.py"
        py_file.write_text("def (: pass")

        class DummyVisitor(ast.NodeVisitor):
            results = []

        result = analyze_with_visitor(py_file, DummyVisitor(), "results")
        assert result == []

    def test_uses_custom_results_attr(self, tmp_path: Path):
        """Should use custom attribute name for results."""
        py_file = tmp_path / "test.py"
        py_file.write_text("x = 1")

        class CustomVisitor(ast.NodeVisitor):
            def __init__(self):
                self.findings = ["found"]

        visitor = CustomVisitor()
        result = analyze_with_visitor(py_file, visitor, "findings")
        assert result == ["found"]

