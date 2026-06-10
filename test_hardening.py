"""Regression tests for the post-review hardening fixes."""

import sys

sys.stdout.reconfigure(encoding="utf-8")

import config
config.ROUTER_VERBOSE = False
config.ORCHESTRATOR_VERBOSE = False

from brain import providers
from brain.keystore import KeyStore, KeyState
from brain.providers import _norm_toolcalls
from brain.router import ModelRouter
from agents.orchestrator import Orchestrator


# Fix: malformed depends_on (unhashable element) must not crash the planner.
def test_unhashable_deps():
    o = Orchestrator()
    bad = '{"steps":[{"id":"s1","agent":"research","task":"a","depends_on":[["s1"]]}]}'
    assert o._parse_plan(bad) is None  # returns None, does not raise TypeError
    print("1) unhashable depends_on → rejected cleanly (no crash)")


# Fix: heuristic no longer false-fires on "vs" / "first" in ordinary asks.
def test_heuristic_precision():
    o = Orchestrator()
    assert not o._looks_complex("tell me the score of india vs australia match today please")
    assert not o._looks_complex("open youtube search lofi beats and play the first video please")
    assert o._looks_complex("research the best laptops and write a summary to a file please")
    print("2) heuristic: 'vs'/'first' no longer trigger planning; real multi-step still does")


# Fix: tool_calls normalization tolerates a missing 'function' key.
def test_norm_toolcalls():
    out = _norm_toolcalls([
        {"id": "x", "function": {"name": "f", "arguments": '{"a":1}'}},
        {"type": "function"},  # malformed: no function key
    ])
    assert out[0]["function"]["name"] == "f"
    assert out[1]["function"]["name"] == "" and out[1]["function"]["arguments"] == "{}"
    print("3) tool_call normalization: missing 'function' handled, no KeyError")


# Fix: load-balancer reserves in-flight picks so concurrent picks fan out.
def test_inflight_fanout():
    ks = KeyStore()
    ks._keys = {"gemini": [KeyState("gemini", "a", 1), KeyState("gemini", "b", 2)]}
    k1 = ks.pick("gemini")
    k2 = ks.pick("gemini")  # without inflight accounting this would pick 'a' again
    assert k1.value != k2.value
    print("4) key pool: two back-to-back picks fan out to different keys")


# Fix: local is an ENFORCED fallback even if removed from PROVIDER_PRIORITY.
def test_enforced_local_fallback():
    r = ModelRouter()
    r.store._keys = {}
    saved = config.PROVIDER_PRIORITY
    config.PROVIDER_PRIORITY = ["gemini", "groq"]  # note: no "local"

    def fake(provider, model, messages, tools, opts, key):
        if provider == "local":
            return {"role": "assistant", "content": "rescued", "tool_calls": []}, 5.0, 0
        raise providers.Offline("no internet")

    real = providers.call
    providers.call = fake
    try:
        msg = r.chat([{"role": "user", "content": "hi"}])
    finally:
        providers.call = real
        config.PROVIDER_PRIORITY = saved
    assert msg["content"] == "rescued" and r.last_route == "local"
    print("5) enforced local fallback: served by local even when not in priority list")


if __name__ == "__main__":
    test_unhashable_deps()
    test_heuristic_precision()
    test_norm_toolcalls()
    test_inflight_fanout()
    test_enforced_local_fallback()
    print("\n✅ hardening regression tests passed")
