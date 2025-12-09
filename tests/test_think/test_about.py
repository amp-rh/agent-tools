"""think.about tests."""
from agent_tools.think.about import about


class TestAbout:
    """Tests for about."""

    def test_about_returns_structured_prompts(self):
        """Verify about returns thinking structure."""
        result = about("How to design a good API")

        assert "Thinking About:" in result
        assert "How to design a good API" in result

    def test_about_includes_key_sections(self):
        """Verify about includes all thinking sections."""
        result = about("test problem")

        assert "Clarify the Problem" in result
        assert "What Do I Know" in result
        assert "What Are the Options" in result
        assert "What Could Go Wrong" in result
        assert "Next Step" in result

    def test_about_prompts_for_assumptions(self):
        """Verify about asks about assumptions."""
        result = about("anything")

        assert "assumed" in result.lower() or "assumption" in result.lower()
