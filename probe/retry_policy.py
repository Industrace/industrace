"""Small retry/backoff utilities for probe workers."""

from __future__ import annotations

import random


def next_backoff_seconds(
    failures: int,
    base_seconds: float = 2.0,
    max_seconds: float = 120.0,
    jitter_ratio: float = 0.2,
) -> float:
    """Compute capped exponential backoff with small jitter."""
    if failures <= 0:
        return float(base_seconds)

    raw = base_seconds * (2 ** max(0, failures - 1))
    capped = min(float(max_seconds), float(raw))
    jitter = capped * max(0.0, float(jitter_ratio)) * random.random()
    return min(float(max_seconds), capped + jitter)
