"""agent.begin tests."""
from agent_tools.agent.begin import analyze_repeatability, begin


class TestBegin:
    """Tests for begin."""

    def test_begin_returns_analysis(self, tmp_registry):
        """Verify begin returns task analysis."""
        result = begin("write documentation for the API")

        assert "Task Analysis" in result
        assert "write documentation" in result
        assert "Recommendation" in result

    def test_begin_shows_available_tools(self, tmp_registry):
        """Verify begin includes available tools by tier."""
        result = begin("do something")

        assert "Available Tools" in result
        assert "Tier 1" in result or "Tier 2" in result

    def test_begin_detects_repeatable_task(self, tmp_registry):
        """Verify begin identifies repeatable tasks."""
        result = begin("create a test file for the module")

        assert "repeatable" in result.lower()
        assert "registry-add" in result

    def test_begin_detects_one_off_task(self, tmp_registry):
        """Verify begin identifies one-off tasks."""
        result = begin("fix this specific bug in the login")

        assert "one-off" in result.lower()
        assert "manually" in result.lower()


class TestAnalyzeRepeatability:
    """Tests for repeatability analysis."""

    def test_repeatable_signals(self):
        """Verify repeatable signals are detected."""
        result, _ = analyze_repeatability("generate a report")
        assert result == "repeatable"

        result, _ = analyze_repeatability("create new user")
        assert result == "repeatable"

    def test_one_off_signals(self):
        """Verify one-off signals are detected."""
        result, _ = analyze_repeatability("fix this specific issue")
        assert result == "one-off"

        result, _ = analyze_repeatability("debug this problem")
        assert result == "one-off"

    def test_unclear_when_no_signals(self):
        """Verify unclear when no strong signals."""
        result, _ = analyze_repeatability("do the thing")
        assert result == "unclear"
