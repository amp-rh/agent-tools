"""agent.extract tests."""
from agent_tools.agent.extract import extract


class TestExtract:
    """Tests for extract."""

    def test_extract_returns_prompts(self):
        """Verify extract returns structured prompts."""
        result = extract("Created a script to format JSON files")

        assert "Extract Reusable Pattern" in result
        assert "Created a script to format JSON files" in result

    def test_extract_includes_all_sections(self):
        """Verify extract includes all guidance sections."""
        result = extract("Automated report generation")

        assert "What's Repeatable?" in result
        assert "Option A: Create a Tool" in result
        assert "Option B: Create an MCP Prompt" in result
        assert "Registry Command" in result

    def test_extract_shows_registry_add_format(self):
        """Verify extract shows registry.add command format."""
        result = extract("Built a linter wrapper")

        assert "registry.add" in result
        assert '"name":' in result
        assert '"description":' in result
        assert '"parameters":' in result

    def test_extract_includes_context_when_provided(self):
        """Verify context is included when provided."""
        result = extract(
            summary="Created file processing logic",
            context="def process_file(path): ..."
        )

        assert "Provided Context" in result
        assert "def process_file(path):" in result

    def test_extract_omits_context_section_when_empty(self):
        """Verify context section is omitted when not provided."""
        result = extract("Simple task without context")

        assert "Provided Context" not in result

    def test_extract_guides_parameter_identification(self):
        """Verify extract prompts for parameter identification."""
        result = extract("Converted data between formats")

        assert "inputs vary" in result.lower()
        assert "parameters" in result.lower()

    def test_extract_explains_tool_vs_prompt(self):
        """Verify extract helps decide between tool and prompt."""
        result = extract("Created a reusable workflow")

        assert "Tool or Prompt?" in result
        assert "code execution" in result.lower()
        assert "guides thinking" in result.lower()
