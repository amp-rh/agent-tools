"""Pytest configuration and fixtures."""
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create a temporary project structure for testing."""
    src_dir = tmp_path / "src" / "agent_tools"
    src_dir.mkdir(parents=True)
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    tool_defs_dir = tmp_path / "tool_defs"
    tool_defs_dir.mkdir()

    (src_dir / "__init__.py").write_text('"""Test package."""\n')

    return tmp_path


@pytest.fixture
def tmp_registry(tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Fixture that patches core module to use temporary files."""
    from agent_tools import _core, registry

    registry._reset_manager()

    monkeypatch.setattr(_core, "PROJECT_ROOT", tmp_project)
    monkeypatch.setattr(_core, "TOOL_DEFS_DIR", tmp_project / "tool_defs")
    monkeypatch.setattr(_core, "SRC_DIR", tmp_project / "src" / "agent_tools")
    monkeypatch.setattr(_core, "TESTS_DIR", tmp_project / "tests")

    return tmp_project
