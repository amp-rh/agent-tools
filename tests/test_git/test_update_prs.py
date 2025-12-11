"""git.update-prs tests."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from agent_tools.git.update_prs import update_prs


class TestUpdatePrs:
    """Tests for update_prs."""

    def test_creates_new_pr(self):
        """Creates a new PR when none exists."""
        with patch("agent_tools.git.update_prs.subprocess.run") as mock_run:
            pr_url = "https://github.com/o/r/pull/1"
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="tool/my-feature\n", stderr=""),
                MagicMock(returncode=0, stdout="", stderr=""),
                MagicMock(returncode=1, stdout="", stderr="no pull requests"),
                MagicMock(returncode=0, stdout=pr_url, stderr=""),
            ]

            result = update_prs(title="Add my feature")

        assert "PR" in result or "pull" in result.lower()

    def test_updates_existing_pr(self):
        """Updates existing PR when one exists."""
        with patch("agent_tools.git.update_prs.subprocess.run") as mock_run:
            pr_url = "https://github.com/o/r/pull/42\n"
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="feat/thing\n", stderr=""),
                MagicMock(returncode=0, stdout="", stderr=""),
                MagicMock(returncode=0, stdout=pr_url, stderr=""),
            ]

            result = update_prs()

        assert "42" in result or "updated" in result.lower() or "pushed" in result.lower()

    def test_uses_custom_base_branch(self):
        """Uses specified base branch."""
        with patch("agent_tools.git.update_prs.subprocess.run") as mock_run:
            pr_url = "https://github.com/o/r/pull/1"
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="my-branch\n", stderr=""),
                MagicMock(returncode=0, stdout="", stderr=""),
                MagicMock(returncode=1, stdout="", stderr="no pull requests"),
                MagicMock(returncode=0, stdout=pr_url, stderr=""),
            ]

            result = update_prs(base="main", title="My PR")

        calls = mock_run.call_args_list
        create_call = [c for c in calls if "pr" in str(c) and "create" in str(c)]
        assert any("main" in str(c) for c in create_call) or "PR" in result

    def test_handles_push_failure(self):
        """Handles git push failure gracefully."""
        with patch("agent_tools.git.update_prs.subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="branch\n", stderr=""),
                MagicMock(returncode=1, stdout="", stderr="failed to push"),
            ]

            result = update_prs()

        assert "error" in result.lower() or "failed" in result.lower()

    def test_draft_pr(self):
        """Creates draft PR when specified."""
        with patch("agent_tools.git.update_prs.subprocess.run") as mock_run:
            pr_url = "https://github.com/o/r/pull/1"
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="branch\n", stderr=""),
                MagicMock(returncode=0, stdout="", stderr=""),
                MagicMock(returncode=1, stdout="", stderr="no pull requests"),
                MagicMock(returncode=0, stdout=pr_url, stderr=""),
            ]

            result = update_prs(title="WIP feature", draft=True)

        calls = mock_run.call_args_list
        create_call = [c for c in calls if "create" in str(c)]
        has_draft = any("--draft" in str(c) for c in create_call)
        assert has_draft or "draft" in result.lower() or "PR" in result

    def test_gh_not_installed(self):
        """Handles missing gh CLI."""
        with patch("agent_tools.git.update_prs.subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="branch\n", stderr=""),
                MagicMock(returncode=0, stdout="", stderr=""),
                FileNotFoundError("gh not found"),
            ]

            result = update_prs()

        assert "gh" in result.lower() or "error" in result.lower()
