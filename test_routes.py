"""Task-based key routing: per-route Gemini key assignment, affinity, spill, fallback."""

import sys

sys.stdout.reconfigure(encoding="utf-8")

import config
config.ROUTER_VERBOSE = False

from brain import providers
from brain.keystore import KeyStore, KeyState
from brain.router import ModelRouter


def ks_with(n):
    ks = KeyStore()
    ks._keys = {"gemini": [KeyState("gemini", f"g{i}", i + 1) for i in range(n)]}
    ks._assign_routes()
    return ks


# 1) Each route is assigned a distinct Gemini key when keys >= routes.
def test_assignment_one_to_one():
    ks = ks_with(7)
    rk = ks.route_key
    assert rk["conversation"] == 0 and rk["coding"] == 3 and rk["system"] == 6
    assert len(set(rk.values())) == 7  # all distinct
    print("1) assignment: 7 routes → 7 distinct keys", rk)


# 2) A route picks its OWN key (affinity); different routes → different keys.
def test_affinity():
    ks = ks_with(7)
    assert ks.pick("gemini", route="coding").value == "g3"
    assert ks.pick("gemini", route="browser").value == "g5"
    assert ks.pick("gemini", route="research").value == "g2"
    print("2) affinity: coding→g3, browser→g5, research→g2")


# 3) Spill: if the route's key is benched, spill to the pool (default) or isolate.
def test_spill():
    ks = ks_with(7)
    ks._keys["gemini"][3].bench(60, "rate-limit")  # coding's key down
    config.GEMINI_SPILL_TO_POOL = True
    got = ks.pick("gemini", route="coding")
    assert got is not None and got.value != "g3"  # spilled to another key
    ks._keys["gemini"][3].cooldown_until = 0  # heal it for the next sub-test
    # strict isolation: assigned key down → None (router would drop to Groq/local)
    ks._keys["gemini"][3].bench(60, "rate-limit")
    config.GEMINI_SPILL_TO_POOL = False
    assert ks.pick("gemini", route="coding") is None
    config.GEMINI_SPILL_TO_POOL = True
    print("3) spill: ON → borrows another key; OFF → isolates (→ next provider)")


# 4) Fewer keys than routes → round-robin (routes share keys, still distributed).
def test_round_robin():
    ks = ks_with(3)
    rk = ks.route_key
    assert rk["conversation"] == 0 and rk["coding"] == 0  # 3 % 3 wrap
    assert rk["research"] == 2 and rk["browser"] == 2
    assert set(rk.values()) == {0, 1, 2}  # all 3 keys used
    print("4) round-robin: 7 routes spread across 3 keys", rk)


# 5) End-to-end: router.chat(route=...) is served by that route's key.
def test_router_uses_route_key():
    r = ModelRouter()
    r.store._keys = {"gemini": [KeyState("gemini", f"g{i}", i + 1) for i in range(7)]}
    r.store._assign_routes()
    seen = {}

    def fake(provider, model, messages, tools, opts, key):
        seen["key"] = key
        return {"role": "assistant", "content": "ok", "tool_calls": []}, 5.0, 0

    real = providers.call
    providers.call = fake
    try:
        r.chat([{"role": "user", "content": "x"}], route="coding")
    finally:
        providers.call = real
    assert seen["key"] == "g3", seen
    print("5) router end-to-end: route='coding' served by its key (g3)")


if __name__ == "__main__":
    test_assignment_one_to_one()
    test_affinity()
    test_spill()
    test_round_robin()
    test_router_uses_route_key()
    print("\n✅ task-based routing tests passed")
