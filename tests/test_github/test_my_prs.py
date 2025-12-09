"""github.my-prs tests."""

from agent_tools.github.my_prs import my_prs


class TestMyPrs:
    """Tests for my_prs."""

    def test_my_prs_returns_string(self, tmp_registry):
        """Verify my_prs returns a string result."""
        # Note: This will fail without GitHub server configured
        # In real tests, we'd mock call_external_sync
        result = my_prs()
        assert isinstance(result, str)

    def test_my_prs_accepts_state(self, tmp_registry):
        """Verify my_prs accepts state parameter."""
        result = my_prs(state="closed")
        assert isinstance(result, str)

    def test_my_prs_accepts_limit(self, tmp_registry):
        """Verify my_prs accepts limit parameter."""
        result = my_prs(limit=5)
        assert isinstance(result, str)
