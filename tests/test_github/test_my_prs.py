"""github.my-prs tests."""

from agent_tools.github.my_prs import my_prs


class TestMyPrs:
    """Tests for my_prs."""

    def test_my_prs_requires_username(self, tmp_registry, monkeypatch):
        """Verify my_prs requires GITHUB_USERNAME environment variable."""
        monkeypatch.delenv("GITHUB_USERNAME", raising=False)
        result = my_prs()
        assert "GITHUB_USERNAME" in result
        assert "not set" in result

    def test_my_prs_returns_string(self, tmp_registry, monkeypatch):
        """Verify my_prs returns a string result."""
        monkeypatch.setenv("GITHUB_USERNAME", "testuser")
        result = my_prs()
        assert isinstance(result, str)

    def test_my_prs_accepts_state(self, tmp_registry, monkeypatch):
        """Verify my_prs accepts state parameter."""
        monkeypatch.setenv("GITHUB_USERNAME", "testuser")
        result = my_prs(state="closed")
        assert isinstance(result, str)

    def test_my_prs_accepts_limit(self, tmp_registry, monkeypatch):
        """Verify my_prs accepts limit parameter."""
        monkeypatch.setenv("GITHUB_USERNAME", "testuser")
        result = my_prs(limit=5)
        assert isinstance(result, str)
