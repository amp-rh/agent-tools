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
