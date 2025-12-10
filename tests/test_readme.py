"""Tests for README.md content."""
from __future__ import annotations

import base64
import json
import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

PROJECT_ROOT = Path(__file__).parent.parent


class TestCursorInstallButton:
    """Tests for the Cursor MCP install button in README."""

    @pytest.fixture
    def readme_content(self) -> str:
        """Read README.md content."""
        readme_path = PROJECT_ROOT / "README.md"
        return readme_path.read_text()

    @pytest.fixture
    def cursor_install_url(self, readme_content: str) -> str:
        """Extract the Cursor install URL from README."""
        # Match the cursor.com/install-mcp URL in markdown link format
        match = re.search(r'\]\((https://cursor\.com/install-mcp\?[^)]+)\)', readme_content)
        assert match, "No Cursor install URL found in README"
        return match.group(1)

    def test_cursor_url_uses_https(self, cursor_install_url: str):
        """Verify the install URL uses HTTPS."""
        parsed = urlparse(cursor_install_url)
        assert parsed.scheme == "https"

    def test_cursor_url_has_correct_host(self, cursor_install_url: str):
        """Verify the URL points to cursor.com."""
        parsed = urlparse(cursor_install_url)
        assert parsed.netloc == "cursor.com"

    def test_cursor_url_has_correct_path(self, cursor_install_url: str):
        """Verify the URL uses the install-mcp endpoint."""
        parsed = urlparse(cursor_install_url)
        assert parsed.path == "/install-mcp"

    def test_cursor_url_has_name_param(self, cursor_install_url: str):
        """Verify the URL includes the name parameter."""
        parsed = urlparse(cursor_install_url)
        params = parse_qs(parsed.query)
        assert "name" in params
        assert params["name"][0] == "agent-tools"

    def test_cursor_url_has_valid_base64_config(self, cursor_install_url: str):
        """Verify the config parameter is valid base64."""
        parsed = urlparse(cursor_install_url)
        params = parse_qs(parsed.query)
        assert "config" in params

        config_b64 = params["config"][0]
        # Should not raise on valid base64
        decoded = base64.b64decode(config_b64)
        assert decoded  # Non-empty

    def test_cursor_url_config_is_valid_json(self, cursor_install_url: str):
        """Verify the decoded config is valid JSON."""
        parsed = urlparse(cursor_install_url)
        params = parse_qs(parsed.query)
        config_b64 = params["config"][0]

        decoded = base64.b64decode(config_b64)
        config = json.loads(decoded)
        assert isinstance(config, dict)

    def test_cursor_url_config_has_server_entry(self, cursor_install_url: str):
        """Verify the config has agent-tools server entry."""
        parsed = urlparse(cursor_install_url)
        params = parse_qs(parsed.query)
        config_b64 = params["config"][0]

        config = json.loads(base64.b64decode(config_b64))
        assert "agent-tools" in config
        server_config = config["agent-tools"]
        assert "command" in server_config
        assert server_config["command"] == "uvx"

    def test_cursor_url_config_has_args(self, cursor_install_url: str):
        """Verify the config includes args with proper structure."""
        parsed = urlparse(cursor_install_url)
        params = parse_qs(parsed.query)
        config_b64 = params["config"][0]

        config = json.loads(base64.b64decode(config_b64))
        server_config = config["agent-tools"]
        assert "args" in server_config
        assert isinstance(server_config["args"], list)

        # Should include git URL and server subcommand
        args = server_config["args"]
        assert any("github.com/amp-rh/agent-tools" in arg for arg in args)
        assert "server" in args
