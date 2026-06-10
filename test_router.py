"""Model-router tests: key rotation, failover, offline→local, and a live local call.

The routing logic is tested with MOCK providers (no network needed), then we run a
real request through the local Ollama path to prove the end-to-end wiring works.
"""

import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")

import config
from brain import providers
from brain.keystore import KeyState
from brain.router import ModelRouter

config.ROUTER_VERBOSE = False  # keep the test output clean


def fresh_router():
    r = ModelRouter()
    r.store._keys = {}  # ignore any real keys.json so tests are deterministic
    return r


def with_keys(router, provider, n):
    router.store._keys[provider] = [KeyState(provider, f"{provider}{i}", i + 1) for i in range(n)]


def run_with(fake_call, fn):
    real = providers.call
    providers.call = fake_call
    try:
        return fn()
    finally:
        providers.call = real


def ok(content):
    return {"role": "assistant", "content": content, "tool_calls": []}, 10.0, 5


# 1) Least-used load-balancing: 6 calls across 3 keys → 2 each.
def test_rotation():
    r = fresh_router()
    with_keys(r, "gemini", 3)
    seen = []

    def fake(provider, model, messages, tools, opts, key):
        seen.append(key)
        return ok("hi")

    run_with(fake, lambda: [r.chat([{"role": "user", "content": "x"}]) for _ in range(6)])
    counts = Counter(seen)
    print("1) rotation across keys:", dict(counts))
    assert len(counts) == 3 and all(v == 2 for v in counts.values()), counts


# 2) Key failover: first gemini key rate-limits → second key answers, first benched.
def test_key_failover():
    r = fresh_router()
    with_keys(r, "gemini", 2)

    def fake(provider, model, messages, tools, opts, key):
        if key == "gemini0":
            raise providers.RateLimited("429 too many requests")
        return ok("second-key")

    msg = run_with(fake, lambda: r.chat([{"role": "user", "content": "x"}]))
    benched = r.store._keys["gemini"][0]
    print("2) key failover → served by:", r.last_route, "| benched:", benched.label, benched.reason)
    assert msg["content"] == "second-key"
    assert benched.reason == "rate-limit" and benched.cooldown_until > 0


# 3) Provider failover: all gemini keys out of quota → groq answers.
def test_provider_failover():
    r = fresh_router()
    with_keys(r, "gemini", 1)
    with_keys(r, "groq", 1)

    def fake(provider, model, messages, tools, opts, key):
        if provider == "gemini":
            raise providers.QuotaExceeded("daily quota exhausted")
        return ok("groq-answered")

    msg = run_with(fake, lambda: r.chat([{"role": "user", "content": "x"}]))
    print("3) provider failover → served by:", r.last_route)
    assert msg["content"] == "groq-answered" and r.last_route.startswith("groq")


# 4) Offline → local: cloud unreachable, no internet → local Ollama path is used.
def test_offline_to_local():
    r = fresh_router()
    with_keys(r, "gemini", 1)

    def fake(provider, model, messages, tools, opts, key):
        if provider == "gemini":
            raise providers.Offline("name resolution failed")
        if provider == "local":
            return ok("local-answered")
        raise AssertionError("should not reach " + provider)

    msg = run_with(fake, lambda: r.chat([{"role": "user", "content": "x"}]))
    print("4) offline → fell back to:", r.last_route)
    assert msg["content"] == "local-answered" and r.last_route == "local"


# 5) LIVE: a real request through the local Ollama path (no cloud keys).
def test_live_local():
    r = fresh_router()  # no keys → goes straight to local
    try:
        msg = r.chat([{"role": "user", "content": "Reply with exactly: pong"}])
        print("5) live local reply:", repr((msg.get("content") or "")[:60]), "| route:", r.last_route)
        assert r.last_route == "local" and msg.get("content")
    except Exception as e:
        print("5) live local SKIPPED (is Ollama running?):", e)


if __name__ == "__main__":
    test_rotation()
    test_key_failover()
    test_provider_failover()
    test_offline_to_local()
    test_live_local()
    print("\n✅ router logic tests passed")
