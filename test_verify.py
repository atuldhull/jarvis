"""Live verification of the configured keys + per-route routing. Prints labels only,
never the secret key values. Makes a few small real calls to check auth + failover.
"""

import sys

sys.stdout.reconfigure(encoding="utf-8")

import config
config.ROUTER_VERBOSE = True  # show the [router] failover decisions on stderr

from brain.router import get_router

r = get_router()

# 1) What loaded (counts + route→key mapping; NO secret values).
snap = r.store.snapshot()
print("Keys loaded per provider:")
for prov, keys in snap.items():
    print(f"  {prov:11} {len(keys)} key(s)")
print("\nTask route → assigned Gemini key:")
for route, idx in r.store.route_key.items():
    print(f"  {route:13} -> gemini#{idx + 1}")

# 2) A few tiny live calls on different routes — who actually serves them?
print("\nLive calls (tiny prompts):")
for route in ["conversation", "coding", "research"]:
    try:
        msg = r.chat([{"role": "user", "content": "Reply with exactly: ok"}], route=route)
        reply = (msg.get("content") or "").strip().replace("\n", " ")[:40]
        print(f"  route={route:13} served by {r.last_route:10} | reply={reply!r}")
    except Exception as e:
        print(f"  route={route:13} FAILED: {e}")
