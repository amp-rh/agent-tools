"""Tests for registry meta-tools."""
from __future__ import annotations

import json
from pathlib import Path

import yaml

from agent_tools.registry import (
    add_tool,
    list_tools,
    remove_tool,
    update_tool,
    validate_registry,
)


class TestAddTool:
    """Tests for registry.add functionality."""

    def test_add_tool_creates_yaml_entry(self, tmp_registry: Path):
        """Verify add_tool creates tool definition file."""
        result = add_tool(
            name="test.example",
            description="A test tool for testing",
            parameters="[]",
        )

        assert "Created tool: test.example" in result

        tool_file = tmp_registry / "tool_defs" / "test" / "example.yaml"
        assert tool_file.exists()

        with tool_file.open() as f:
            tool_def = yaml.safe_load(f)

        assert tool_def["name"] == "test.example"

    def test_add_tool_creates_module_stub(self, tmp_registry: Path):
        """Verify add_tool creates Python module stub."""
        add_tool(
            name="myns.my-tool",
            description="My tool description",
            parameters=(
                '[{"name": "input", "type": "string", '
                '"description": "Input value", "required": true}]'
            ),
        )

        module_file = tmp_registry / "src" / "agent_tools" / "myns" / "my_tool.py"
        assert module_file.exists()

        content = module_file.read_text()
        assert "def my_tool(" in content
        assert "input: str" in content
        assert "NotImplementedError" in content

    def test_add_tool_creates_test_stub(self, tmp_registry: Path):
        """Verify add_tool creates test stub."""
        add_tool(
            name="myns.my-tool",
            description="My tool description",
            parameters="[]",
        )

        test_file = tmp_registry / "tests" / "test_myns" / "test_my_tool.py"
        assert test_file.exists()

        content = test_file.read_text()
        assert "class TestMyTool:" in content
        assert "from agent_tools.myns.my_tool import my_tool" in content

    def test_add_tool_creates_namespace_init(self, tmp_registry: Path):
        """Verify add_tool creates __init__.py for namespace."""
        add_tool(
            name="newns.tool",
            description="Tool in new namespace",
            parameters="[]",
        )

        init_file = tmp_registry / "src" / "agent_tools" / "newns" / "__init__.py"
        assert init_file.exists()

    def test_add_tool_rejects_duplicate(self, tmp_registry: Path):
        """Verify add_tool rejects duplicate tool names."""
        add_tool(name="test.dup", description="First", parameters="[]")
        result = add_tool(name="test.dup", description="Second", parameters="[]")

        assert "Error" in result
        assert "already exists" in result

    def test_add_tool_rejects_invalid_name(self, tmp_registry: Path):
        """Verify add_tool rejects names without namespace."""
        result = add_tool(name="notool", description="No namespace", parameters="[]")

        assert "Error" in result or "namespace" in result.lower()

    def test_add_tool_with_multiple_parameters(self, tmp_registry: Path):
        """Verify add_tool handles multiple parameters correctly."""
        params = json.dumps([
            {"name": "required_param", "type": "string",
             "description": "Required", "required": True},
            {"name": "optional_param", "type": "integer",
             "description": "Optional", "required": False},
        ])

        add_tool(name="test.multi", description="Multi param tool", parameters=params)

        module_file = tmp_registry / "src" / "agent_tools" / "test" / "multi.py"
        content = module_file.read_text()

        assert "required_param: str" in content
        assert "optional_param: int = None" in content


class TestRemoveTool:
    """Tests for registry.remove functionality."""

    def test_remove_tool_deletes_yaml_entry(self, tmp_registry: Path):
        """Verify remove_tool removes tool definition file."""
        add_tool(name="test.removeme", description="To be removed", parameters="[]")
        result = remove_tool(name="test.removeme")

        assert "Removed tool: test.removeme" in result

        tool_file = tmp_registry / "tool_defs" / "test" / "removeme.yaml"
        assert not tool_file.exists()

    def test_remove_tool_keeps_files(self, tmp_registry: Path):
        """Verify remove_tool does NOT delete Python files."""
        add_tool(name="test.keepfiles", description="Keep files", parameters="[]")

        module_file = tmp_registry / "src" / "agent_tools" / "test" / "keepfiles.py"
        assert module_file.exists()

        remove_tool(name="test.keepfiles")

        assert module_file.exists()

    def test_remove_tool_not_found(self, tmp_registry: Path):
        """Verify remove_tool handles missing tool gracefully."""
        result = remove_tool(name="test.nonexistent")

        assert "Error" in result
        assert "not found" in result


class TestUpdateTool:
    """Tests for registry.update functionality."""

    def test_update_tool_changes_description(self, tmp_registry: Path):
        """Verify update_tool updates description."""
        add_tool(name="test.update", description="Original", parameters="[]")
        result = update_tool(name="test.update", description="Updated description")

        assert "Updated tool: test.update" in result

        tool_file = tmp_registry / "tool_defs" / "test" / "update.yaml"
        with tool_file.open() as f:
            tool_def = yaml.safe_load(f)

        assert tool_def["description"] == "Updated description"

    def test_update_tool_not_found(self, tmp_registry: Path):
        """Verify update_tool handles missing tool gracefully."""
        result = update_tool(name="test.nonexistent", description="New desc")

        assert "Error" in result
        assert "not found" in result

    def test_update_tool_no_changes(self, tmp_registry: Path):
        """Verify update_tool handles no fields provided."""
        add_tool(name="test.nochange", description="Original", parameters="[]")
        result = update_tool(name="test.nochange")

        assert "No fields to update" in result


class TestListTools:
    """Tests for registry.list functionality."""

    def test_list_tools_shows_all(self, tmp_registry: Path):
        """Verify list_tools shows all registered tools."""
        add_tool(name="ns1.tool1", description="Tool 1", parameters="[]")
        add_tool(name="ns1.tool2", description="Tool 2", parameters="[]")
        add_tool(name="ns2.tool3", description="Tool 3", parameters="[]")

        result = list_tools()

        assert "ns1:" in result
        assert "tool1:" in result
        assert "tool2:" in result
        assert "ns2:" in result
        assert "tool3:" in result

    def test_list_tools_empty_registry(self, tmp_registry: Path):
        """Verify list_tools handles empty registry."""
        result = list_tools()

        assert "tools:" in result


class TestValidateRegistry:
    """Tests for registry.validate functionality."""

    def test_validate_finds_no_errors(self, tmp_registry: Path):
        """Verify validate passes for valid registry."""
        add_tool(name="test.valid", description="Valid tool", parameters="[]")
        result = validate_registry()

        assert "Validated" in result

    def test_validate_detects_missing_module(self, tmp_registry: Path):
        """Verify validate detects missing Python modules."""
        from agent_tools import _core

        tool_def = {
            "name": "test.missing",
            "description": "Missing module",
            "module": "agent_tools.test.missing",
            "function": "missing",
            "parameters": [],
        }
        _core.save_tool("test.missing", tool_def)

        result = validate_registry()

        assert "Module not found" in result or "Warning" in result


class TestExecuteTool:
    """Tests for registry.execute functionality."""

    def test_execute_tool_calls_function(self, tmp_registry: Path):
        """Verify execute_tool invokes the target function."""
        from agent_tools import _core
        from agent_tools.registry import execute_tool

        tool_def = {
            "name": "registry.list",
            "description": "List tools",
            "module": "agent_tools.registry",
            "function": "list_tools",
            "parameters": [],
        }
        _core.save_tool("registry.list", tool_def)

        result = execute_tool(name="registry.list", params="{}")

        assert "tools:" in result

    def test_execute_tool_not_found(self, tmp_registry: Path):
        """Verify execute_tool handles missing tool."""
        from agent_tools.registry import execute_tool

        result = execute_tool(name="nonexistent.tool", params="{}")

        assert "Error" in result
        assert "not found" in result

    def test_execute_tool_invalid_params(self, tmp_registry: Path):
        """Verify execute_tool handles invalid JSON params."""
        from agent_tools import _core
        from agent_tools.registry import execute_tool

        tool_def = {
            "name": "registry.list",
            "description": "List tools",
            "module": "agent_tools.registry",
            "function": "list_tools",
            "parameters": [],
        }
        _core.save_tool("registry.list", tool_def)

        result = execute_tool(name="registry.list", params="not valid json")

        assert "Error" in result
        assert "JSON" in result
