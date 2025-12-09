"""agent.start-here tests."""
from agent_tools.agent.start_here import start_here


class TestStartHere:
    """Tests for start_here."""

    def test_start_here_returns_workflow(self, tmp_registry):
        """Verify start_here includes workflow guidance."""
        result = start_here()
        assert "Workflow" in result
        assert "registry-execute" in result

    def test_start_here_lists_tools(self, tmp_registry):
        """Verify start_here includes available tools."""
        result = start_here()
        assert "Available Tools" in result

    def test_start_here_shows_how_to_call(self, tmp_registry):
        """Verify start_here explains how to invoke tools."""
        result = start_here()
        assert "How to Call" in result
        assert "registry-execute" in result
