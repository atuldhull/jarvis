"""Text embeddings via Ollama — the local, free engine for semantic memory.

`embed(text)` returns a vector (list of floats) using config.EMBED_MODEL, or None if
Ollama/the model isn't available — in which case the memory store quietly falls back
to keyword search. Stdlib HTTP only, so the core stays dependency-free.

Resilience: this runs on the interactive recall path, so the timeout is short and a
failure backs off for a while (returning None instantly) instead of re-paying a slow
round-trip every turn. It re-probes automatically after the backoff.
"""

import json
import math
import time
import urllib.error
import urllib.request

import config

_unavailable_until = 0.0  # while time < this, skip the network and fall back immediately
_BACKOFF = 30.0           # seconds to stay in keyword-only mode after a failure


def embed(text, timeout=6):
    """Embedding vector for `text`, or None if embeddings aren't available right now."""
    global _unavailable_until
    if time.time() < _unavailable_until:
        return None  # known-degraded → instant keyword fallback, no slow round-trip
    model = getattr(config, "EMBED_MODEL", "nomic-embed-text")
    req = urllib.request.Request(
        config.OLLAMA_HOST + "/api/embeddings",
        data=json.dumps({"model": model, "prompt": text}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            vec = json.loads(resp.read()).get("embedding")
        _unavailable_until = 0.0  # healthy again
        return vec or None
    except Exception:
        _unavailable_until = time.time() + _BACKOFF  # back off, re-probe later
        return None


def cosine(a, b):
    """Cosine similarity of two vectors (0 if either is missing/empty)."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0
