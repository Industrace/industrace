"""Unit tests for retry backoff policy."""

from __future__ import annotations

from retry_policy import next_backoff_seconds


def test_backoff_grows_with_failures():
    first = next_backoff_seconds(1, base_seconds=2.0, max_seconds=120.0, jitter_ratio=0.0)
    second = next_backoff_seconds(2, base_seconds=2.0, max_seconds=120.0, jitter_ratio=0.0)
    third = next_backoff_seconds(3, base_seconds=2.0, max_seconds=120.0, jitter_ratio=0.0)

    assert first == 2.0
    assert second == 4.0
    assert third == 8.0


def test_backoff_respects_max_seconds():
    value = next_backoff_seconds(10, base_seconds=2.0, max_seconds=30.0, jitter_ratio=0.0)
    assert value == 30.0


def test_backoff_non_positive_failures_uses_base():
    assert next_backoff_seconds(0, base_seconds=5.0, max_seconds=60.0, jitter_ratio=0.0) == 5.0
