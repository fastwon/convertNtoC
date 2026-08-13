"""Rough USD cost estimation for LLM usage. Prices are the user's own API
rates (they pay), so this is a transparency aid — clearly an estimate.

Per 1M tokens: (input, output, cache_read, cache_write). This project sends the
global memory as a cached prefix with ttl "1h", so cache writes are 2x input.
Gemini (free tier) and Pollinations images cost $0 and are simply absent here.
"""
from __future__ import annotations

# USD per 1,000,000 tokens
_PRICING: dict[str, tuple[float, float, float, float]] = {
    "claude-opus-4-8": (5.0, 25.0, 0.5, 10.0),
    "claude-sonnet-4-6": (3.0, 15.0, 0.3, 6.0),
    "claude-haiku-4-5": (1.0, 5.0, 0.1, 2.0),
}


def token_cost(model: str | None, input: int, output: int, cache_read: int, cache_write: int) -> float:
    """Estimated USD for one model's aggregated token counts. Unknown/free
    models (Gemini, Pollinations) return 0."""
    p = _PRICING.get(model or "")
    if p is None:
        return 0.0
    pi, po, pcr, pcw = p
    return (input * pi + output * po + cache_read * pcr + cache_write * pcw) / 1_000_000


def is_priced(model: str | None) -> bool:
    return (model or "") in _PRICING
