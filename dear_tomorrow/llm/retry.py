"""Retry wrapper for rate-limited model calls.

Groq's free tier has a tight per-minute token budget that a single orchestrator turn
(Orchestrator -> Goal Discovery -> Planner, each with their own tool calls) can exceed.
Rather than crash, wait out the window and retry -- our tools are safe to re-run
(create_goal/create_schedule_item already refuse duplicates/overlaps), so a full retry
just re-derives the same result instead of corrupting state.
"""

import time
from typing import Callable, TypeVar

T = TypeVar("T")


def call_with_retry(fn: Callable[[], T], max_attempts: int = 3, base_delay_seconds: float = 15.0) -> T:
    """Call fn(), retrying with backoff if it fails on a rate-limit error."""
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except Exception as e:
            if "rate_limit" not in str(e).lower() and "429" not in str(e):
                raise
            last_error = e
            if attempt < max_attempts:
                time.sleep(base_delay_seconds * attempt)
    raise last_error
