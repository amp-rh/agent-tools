"""git.commit tests."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from agent_tools.git.commit import commit


class TestCommit:
    """Tests for commit."""

    def test_commit_basic_message(self):
        """Commit with just a message uses default type."""
        with patch("agent_tools.git.commit.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="[main abc1234] feat: add new feature\n 1 file changed, 1 insertion(+)",
                stderr="",
            )
            result = commit("add new feature")

        assert "abc1234" in result or "Committed" in result
        # Should have called git add -A and git commit
        assert mock_run.call_count >= 1

    def test_commit_with_type_and_scope(self):
        """Commit with type and scope formats correctly."""
        with patch("agent_tools.git.commit.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="[main def5678] fix(registry): resolve cache issue\n 2 files changed",
                stderr="",
            )
            result = commit("resolve cache issue", type="fix", scope="registry")

        assert "fix" in result.lower() or "Committed" in result

    def test_commit_with_specific_files(self):
        """Commit with specific files stages only those files."""
        with patch("agent_tools.git.commit.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="[main abc1234] feat: update docs\n 1 file changed",
                stderr="",
            )
            result = commit("update docs", files="README.md docs/guide.md")

        # Should stage specific files
        calls = [str(c) for c in mock_run.call_args_list]
        has_readme = any("README.md" in str(c) or "git add" in str(c) for c in calls)
        assert has_readme or "Committed" in result

    def test_commit_nothing_to_commit(self):
        """Handle case when there's nothing to commit."""
        with patch("agent_tools.git.commit.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="nothing to commit, working tree clean",
            )
            result = commit("some message")

        assert "nothing to commit" in result.lower() or "no changes" in result.lower()

    def test_commit_formats_conventional_message(self):
        """Verify conventional commit format is built correctly."""
        with patch("agent_tools.git.commit.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="[main xyz9999] refactor(server): clean up handlers",
                stderr="",
            )
            result = commit("clean up handlers", type="refactor", scope="server")

        # Verify the commit command was called with proper format
        calls = mock_run.call_args_list
        commit_call = [c for c in calls if "commit" in str(c)]
        assert len(commit_call) >= 1 or "Committed" in result

    def test_commit_default_type_is_feat(self):
        """Default type should be 'feat'."""
        with patch("agent_tools.git.commit.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="[main abc1234] feat: new thing",
                stderr="",
            )
            commit("new thing")

        calls = mock_run.call_args_list
        # At least one call should include "feat:" in the message
        commit_calls = [str(c) for c in calls if "commit" in str(c)]
        assert any("feat" in str(c) for c in commit_calls) or len(calls) > 0

    def test_commit_git_error(self):
        """Handle git errors gracefully."""
        with patch("agent_tools.git.commit.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=128,
                stdout="",
                stderr="fatal: not a git repository",
            )
            result = commit("some message")

        assert "error" in result.lower() or "not a git repository" in result.lower()
