"""Usage caps for shared mode, so one visitor cannot exhaust the host's free tier.

Three independent guards, all in-memory (Streamlit Cloud runs a single process):

* a per-session call budget (``DEMO_SESSION_LIMIT``)
* a process-wide sliding-window rate limit (``DEMO_RPM``)
* a prompt-size cap (``DEMO_MAX_WORDS``)

The pure pieces (:class:`SlidingWindowLimiter`, :func:`prompt_words`) have no Streamlit
dependency; :func:`demo_guard` wires them to session state.
"""

from __future__ import annotations

import threading
import time
from collections import deque
from collections.abc import Callable

from ai_alchemy.config import LLMSettings
from ai_alchemy.llm import LLMError, Message


class SlidingWindowLimiter:
    """Allow at most ``limit`` events per ``window`` seconds. Thread-safe."""

    def __init__(
        self, limit: int, window: float = 60.0, clock: Callable[[], float] = time.monotonic
    ):
        self.limit = limit
        self.window = window
        self._clock = clock
        self._events: deque[float] = deque()
        self._lock = threading.Lock()

    def try_acquire(self) -> bool:
        now = self._clock()
        with self._lock:
            while self._events and now - self._events[0] >= self.window:
                self._events.popleft()
            if len(self._events) >= self.limit:
                return False
            self._events.append(now)
            return True


_global_limiter: SlidingWindowLimiter | None = None
_global_lock = threading.Lock()


def global_limiter(rpm: int) -> SlidingWindowLimiter:
    """Process-wide limiter, re-created if the host changes the RPM setting."""
    global _global_limiter
    with _global_lock:
        if _global_limiter is None or _global_limiter.limit != rpm:
            _global_limiter = SlidingWindowLimiter(rpm)
        return _global_limiter


def prompt_words(messages: list[Message]) -> int:
    """Rough size of a request: whitespace-separated words across all text parts."""
    total = 0
    for message in messages:
        content = message.get("content", "")
        if isinstance(content, str):
            total += len(content.split())
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    total += len(str(part.get("text", "")).split())
    return total


BYO_HINT = "Paste your own free API key in **⚙️ Model settings** to lift this limit."


def demo_guard(settings: LLMSettings) -> Callable[[list[Message]], None]:
    """Return a hook for :class:`~ai_alchemy.llm.LLMClient` that enforces the shared-mode caps."""
    import streamlit as st

    session_limit = settings.demo_limit("DEMO_SESSION_LIMIT")
    rpm = settings.demo_limit("DEMO_RPM")
    max_words = settings.demo_limit("DEMO_MAX_WORDS")

    def check(messages: list[Message]) -> None:
        words = prompt_words(messages)
        if words > max_words:
            raise LLMError(
                f"The shared demo model accepts up to {max_words:,} words per request "
                f"(this one is {words:,}). {BYO_HINT}"
            )
        used = int(st.session_state.get("demo_calls", 0))
        if used >= session_limit:
            raise LLMError(
                f"You have used the {session_limit} free demo calls for this session. {BYO_HINT}"
            )
        if not global_limiter(rpm).try_acquire():
            raise LLMError(
                "The shared demo model is busy right now - try again in a few seconds. " + BYO_HINT
            )
        st.session_state["demo_calls"] = used + 1

    return check
