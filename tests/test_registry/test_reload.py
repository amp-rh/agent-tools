"""registry.reload tests."""
import sys

from agent_tools.registry.reload import reload


class TestReload:
    """Tests for reload."""

    def test_reload_returns_summary(self):
        """Verify reload returns a summary message."""
        result = reload()

        assert "Cache Cleared" in result
        assert "Local tools" in result
        assert "External servers" in result

    def test_reload_clears_tool_modules(self):
        """Verify reload clears agent_tools submodules."""
        # Import a tool module to ensure it's cached
        import agent_tools.agent.extract  # noqa: F401

        assert "agent_tools.agent.extract" in sys.modules

        reload()

        # Module should be cleared
        assert "agent_tools.agent.extract" not in sys.modules

    def test_reload_preserves_core_modules(self):
        """Verify reload preserves core infrastructure modules."""
        import agent_tools._core  # noqa: F401

        reload()

        # Core module should still be present
        assert "agent_tools._core" in sys.modules

    def test_reload_reports_both_local_and_external(self):
        """Verify reload reports on both local and external."""
        # Import something first
        import agent_tools.agent.begin  # noqa: F401

        result = reload()

        # Should mention both
        assert "Local tools" in result
        assert "External servers" in result
        assert "Next tool calls will use fresh code" in result

    def test_reload_notes_external_reconnect(self):
        """Verify reload mentions external servers need reconnect for code changes."""
        result = reload()

        assert "mcp.disconnect" in result or "mcp.connect" in result
