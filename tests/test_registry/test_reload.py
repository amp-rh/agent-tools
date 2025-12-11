"""registry.reload tests."""
import sys

from agent_tools.registry.reload import reload


class TestReload:
    """Tests for reload."""

    def test_reload_returns_summary(self):
        """Verify reload returns a summary message."""
        result = reload()

        assert "Module Cache Cleared" in result
        assert "modules from cache" in result

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

    def test_reload_reports_cleared_modules(self):
        """Verify reload lists what was cleared."""
        # Import something first
        import agent_tools.agent.begin  # noqa: F401

        result = reload()

        # Should mention clearing happened
        assert "Cleared" in result
        assert "Next tool calls will use fresh code" in result
