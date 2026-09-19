"""Shared-mode usage caps."""

from __future__ import annotations

from ai_alchemy.quota import SlidingWindowLimiter, prompt_words


def test_sliding_window_limiter_refills_after_window():
    now = [100.0]
    limiter = SlidingWindowLimiter(limit=2, window=10, clock=lambda: now[0])
    assert limiter.try_acquire()
    assert limiter.try_acquire()
    assert not limiter.try_acquire()
    now[0] += 9
    assert not limiter.try_acquire()
    now[0] += 1.5  # first event is now older than the window
    assert limiter.try_acquire()


def test_prompt_words_counts_text_and_multimodal_parts():
    messages = [
        {"role": "system", "content": "one two three"},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "four five"},
                {"type": "image_url", "image_url": {"url": "data:..."}},
            ],
        },
    ]
    assert prompt_words(messages) == 5
