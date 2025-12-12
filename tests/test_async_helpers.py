"""Tests for _async_helpers module."""
import asyncio

import pytest

from agent_tools._async_helpers import run_async_in_thread


class TestRunAsyncInThread:
    """Tests for run_async_in_thread function."""

    def test_returns_coroutine_result(self):
        """Should return the result of the coroutine."""
        async def coro():
            return 42

        result = run_async_in_thread(coro())
        assert result == 42

    def test_handles_async_sleep(self):
        """Should handle async operations like sleep."""
        async def coro():
            await asyncio.sleep(0.01)
            return "done"

        result = run_async_in_thread(coro())
        assert result == "done"

    def test_propagates_exceptions(self):
        """Should propagate exceptions from the coroutine."""
        async def coro():
            raise ValueError("test error")

        with pytest.raises(ValueError, match="test error"):
            run_async_in_thread(coro())

    def test_timeout_raises_error(self):
        """Should raise TimeoutError if operation exceeds timeout."""
        async def slow_coro():
            await asyncio.sleep(10)
            return "never"

        with pytest.raises(TimeoutError, match="timed out"):
            run_async_in_thread(slow_coro(), timeout=0)

    def test_works_with_existing_event_loop(self):
        """Should work even when called from within an async context."""
        async def inner():
            return "inner result"

        # Simulate being called from sync code that may have a loop
        result = run_async_in_thread(inner())
        assert result == "inner result"

