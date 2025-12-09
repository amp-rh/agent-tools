"""Tests for README.md content."""
from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

import pytest

PROJECT_ROOT = Path(__file__).parent.parent


@dataclass
class CursorInstallLink:
    """Parsed Cursor MCP install link."""

    url: str
    scheme: str
    host: str
    path: str
    name: str
    config_b64: str
    config: dict

    @classmethod
    def from_readme(cls, readme_path: Path) -> "CursorInstallLink":
        """Extract and parse the Cursor install link from README."""
        content = readme_path.read_text()
        match = re.search(r'\]\((https://cursor\.com/[^)]+install-mcp\?[^)]+)\)', content)
        if not match:
            raise ValueError("No Cursor install URL found in README")

        url = match.group(1)
        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        config_b64 = unquote(params["config"][0])
        config = json.loads(base64.b64decode(config_b64))

        return cls(
            url=url,
            scheme=parsed.scheme,
            host=parsed.netloc,
            path=parsed.path,
            name=params["name"][0],
            config_b64=config_b64,
            config=config,
        )


class TestCursorInstallButton:
    """Tests for the Cursor MCP install button in README."""

    @pytest.fixture
    def cursor_link(self) -> CursorInstallLink:
        """Parse the Cursor install link from README."""
        return CursorInstallLink.from_readme(PROJECT_ROOT / "README.md")

    def test_uses_https(self, cursor_link: CursorInstallLink):
        """Verify the install URL uses HTTPS."""
        assert cursor_link.scheme == "https"

    def test_points_to_cursor_com(self, cursor_link: CursorInstallLink):
        """Verify the URL points to cursor.com."""
        assert cursor_link.host == "cursor.com"

    def test_uses_install_mcp_endpoint(self, cursor_link: CursorInstallLink):
        """Verify the URL uses the install-mcp endpoint."""
        assert "install-mcp" in cursor_link.path

    def test_name_is_agent_tools(self, cursor_link: CursorInstallLink):
        """Verify the name parameter is agent-tools."""
        assert cursor_link.name == "agent-tools"

    def test_config_is_valid(self, cursor_link: CursorInstallLink):
        """Verify the config is valid JSON with expected fields."""
        assert isinstance(cursor_link.config, dict)
        assert "command" in cursor_link.config

    def test_command_uses_uvx(self, cursor_link: CursorInstallLink):
        """Verify the command uses uvx with correct arguments."""
        command = cursor_link.config["command"]
        assert "uvx" in command
        assert "github.com/amp-rh/agent-tools" in command
        assert "server" in command
