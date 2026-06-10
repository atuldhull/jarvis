"""The multi-key pool — load-balancing, health tracking and failover for API keys.

Each cloud provider (gemini, groq, openrouter) can hold several FREE keys. This
module loads them, hands out the least-used healthy key on demand, and benches a
key the moment it rate-limits, runs out of quota, or errors — automatically
returning it to the pool once its cooldown passes.

There are no background threads: a benched key is simply re-tested the next time
one is needed and its cooldown has expired (lazy recovery). Keys are read from
keys.json (git-ignored) and/or numbered environment variables, so secrets never
touch the source tree.
"""

import json
import os
import threading
import time

import config


class KeyState:
    """Live health for a single API key."""

    def __init__(self, provider, value, index):
        self.provider = provider
        self.value = value
        self.index = index          # 1-based, for human-readable labels
        self.requests = 0           # successful calls served
        self.tokens = 0             # tokens billed, when the API reports them
        self.errors = 0             # consecutive errors (reset on success)
        self.total_errors = 0       # lifetime errors, for the dashboard
        self.latency_ms = 0.0       # exponential moving average
        self.last_used = 0.0
        self.cooldown_until = 0.0   # benched until this wall-clock time
        self.reason = ""            # why it was last benched
        self.inflight = 0           # calls picked but not yet finished (parallel-safe balancing)

    @property
    def label(self):
        return f"{self.provider}#{self.index}"

    def healthy(self, now):
        return now >= self.cooldown_until

    def bench(self, seconds, reason):
        """Take this key out of rotation for a while."""
        self.inflight = max(0, self.inflight - 1)
        self.cooldown_until = time.time() + seconds
        self.reason = reason
        self.errors += 1
        self.total_errors += 1

    def record_success(self, latency_ms, tokens=0):
        self.inflight = max(0, self.inflight - 1)
        self.requests += 1
        self.tokens += tokens
        self.errors = 0
        self.reason = ""
        # Smooth the latency so one slow call doesn't dominate the average.
        self.latency_ms = latency_ms if self.latency_ms == 0 else (
            0.7 * self.latency_ms + 0.3 * latency_ms
        )
        self.last_used = time.time()


class KeyStore:
    def __init__(self):
        self._keys = {}  # provider -> [KeyState]
        self._lock = threading.Lock()  # parallel orchestrator steps share one pool
        self._load()

    def _load(self):
        data = {}
        path = getattr(config, "KEYS_FILE", "keys.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}

        for provider in ("gemini", "groq", "openrouter"):
            # From keys.json …
            from_file = list(data.get(provider, []))
            # … plus env vars GEMINI_KEY_1, GEMINI_KEY_2, …
            from_env, i = [], 1
            while True:
                v = os.environ.get(f"{provider.upper()}_KEY_{i}")
                if not v:
                    break
                from_env.append(v)
                i += 1

            # Drop blanks + the template placeholders, de-dup, keep order.
            seen, clean = set(), []
            for k in from_file + from_env:
                k = (k or "").strip()
                if not k or "PASTE_" in k or k in seen:
                    continue
                seen.add(k)
                clean.append(k)

            if clean:
                self._keys[provider] = [
                    KeyState(provider, k, n + 1) for n, k in enumerate(clean)
                ]

    def has(self, provider):
        return bool(self._keys.get(provider))

    def providers_with_keys(self):
        return [p for p, keys in self._keys.items() if keys]

    def pick(self, provider, now=None):
        """Reserve and return the least-used healthy key, or None if all are benched.

        Counts in-flight reservations so that two threads picking at the same moment
        fan out to different keys instead of stampeding one (the load-balancer is
        otherwise read-then-write across a blocking network call).
        """
        now = now or time.time()
        with self._lock:
            healthy = [k for k in self._keys.get(provider, []) if k.healthy(now)]
            if not healthy:
                return None
            # Fewest (done + in-flight) first; oldest last_used breaks ties → round-robin.
            healthy.sort(key=lambda k: (k.requests + k.inflight, k.last_used))
            chosen = healthy[0]
            chosen.inflight += 1
            return chosen

    def note_success(self, key, latency_ms, tokens=0):
        with self._lock:
            key.record_success(latency_ms, tokens)

    def note_failure(self, key, seconds, reason):
        with self._lock:
            key.bench(seconds, reason)

    def release(self, key):
        """Drop a reservation without penalty (e.g. provider was simply offline)."""
        with self._lock:
            key.inflight = max(0, key.inflight - 1)

    def snapshot(self):
        """A plain-dict view of pool health for the dashboard / debugging."""
        now = time.time()
        out = {}
        for provider, keys in self._keys.items():
            out[provider] = [
                {
                    "key": k.label,
                    "requests": k.requests,
                    "tokens": k.tokens,
                    "errors": k.total_errors,
                    "latency_ms": round(k.latency_ms),
                    "healthy": k.healthy(now),
                    "cooldown_s": max(0, round(k.cooldown_until - now)),
                    "reason": k.reason,
                }
                for k in keys
            ]
        return out
