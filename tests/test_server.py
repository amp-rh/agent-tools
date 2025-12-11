"""Tests for MCP server functionality."""
from __future__ import annotations

from pathlib import Path

import pytest

from agent_tools.server import WORKFLOW_PROMPT, AgentToolsServer, ServerConfig


@pytest.fixture
def server(tmp_path: Path) -> AgentToolsServer:
    """Create a server instance with temporary config."""
    tool_defs = tmp_path / "tool_defs"
    tool_defs.mkdir()
    config = ServerConfig(tool_defs_path=tool_defs, project_root=tmp_path)
    return AgentToolsServer(config)


class TestPrompts:
    """Tests for MCP prompt functionality."""

    @pytest.mark.asyncio
    async def test_list_prompts_returns_workflow(self, server: AgentToolsServer):
        """Verify list_prompts includes the workflow prompt."""
        prompts = await server._list_prompts()

        assert len(prompts) == 1
        assert prompts[0].name == "agent-tools-workflow"
        assert "check tools first" in prompts[0].description

    @pytest.mark.asyncio
    async def test_get_prompt_returns_workflow_content(self, server: AgentToolsServer):
        """Verify get_prompt returns the workflow as agent thought."""
        result = await server._get_prompt("agent-tools-workflow", None)

        assert result.messages
        assert len(result.messages) == 1
        assert result.messages[0].role == "assistant"
        assert "registry-list" in result.messages[0].content.text

    @pytest.mark.asyncio
    async def test_get_prompt_unknown_raises(self, server: AgentToolsServer):
        """Verify get_prompt raises for unknown prompt names."""
        with pytest.raises(ValueError, match="Unknown prompt"):
            await server._get_prompt("nonexistent-prompt", None)

    def test_workflow_prompt_content(self):
        """Verify workflow prompt is framed as agent's own thought."""
        assert "registry-list" in WORKFLOW_PROMPT
        assert "registry-add" in WORKFLOW_PROMPT
        assert "I should" in WORKFLOW_PROMPT
        assert "My job" in WORKFLOW_PROMPT


class TestResources:
    """Tests for MCP resource functionality."""

    @pytest.mark.asyncio
    async def test_list_resources_returns_registry(self, server: AgentToolsServer):
        """Verify list_resources includes the registry resource."""
        resources = await server._list_resources()

        assert len(resources) == 1
        assert str(resources[0].uri) == "agent-tools://registry"
        assert resources[0].name == "Tool Registry"
        assert resources[0].mimeType == "text/yaml"

    @pytest.mark.asyncio
    async def test_read_resource_registry(self, server: AgentToolsServer):
        """Verify read_resource returns registry content."""
        result = await server._read_resource("agent-tools://registry")

        assert len(result) == 1
        assert str(result[0].uri) == "agent-tools://registry"
        assert result[0].mimeType == "text/yaml"
        # Empty server has no tools, but should still return valid YAML
        assert isinstance(result[0].text, str)

    @pytest.mark.asyncio
    async def test_read_resource_unknown_raises(self, server: AgentToolsServer):
        """Verify read_resource raises for unknown URIs."""
        with pytest.raises(ValueError, match="Unknown resource"):
            await server._read_resource("agent-tools://unknown")
