"""Shared async utilities for running coroutines from synchronous code."""
from __future__ import annotations

import asyncio
import threading
from typing import Any, Coroutine

__all__ = ["run_async_in_thread"]


def run_async_in_thread(coro: Coroutine[Any, Any, Any], timeout: int = 120) -> Any:
    """Run an async coroutine in a separate thread with its own event loop.

    This is useful when you need to call async code from a synchronous context,
    especially when there may already be an event loop running in the current thread.

    Args:
        coro: The coroutine to execute
        timeout: Maximum seconds to wait (default: 120)

    Returns:
        The result of the coroutine

    Raises:
        TimeoutError: If the operation exceeds the timeout
        Exception: Any exception raised by the coroutine
    """
    result: list[Any] = [None]
    error: list[Exception | None] = [None]

    def execute() -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result[0] = loop.run_until_complete(coro)
        except Exception as e:
            error[0] = e
        finally:
            loop.close()

    thread = threading.Thread(target=execute)
    thread.start()
    thread.join(timeout=timeout)

    if thread.is_alive():
        raise TimeoutError("Operation timed out")
    if error[0]:
        raise error[0]
    return result[0]

