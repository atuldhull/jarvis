"""Quick offline self-checks — no model, no network needed.

Verifies the wiring that doesn't depend on Ollama: the tool registry, tool schemas,
a pure tool (get_time), and the SQLite memory round-trip.

Run:  py test_jarvis.py
"""

import sys

import tools
from memory.store import Memory

sys.stdout.reconfigure(encoding="utf-8")  # Windows cp1252 → UTF-8 so emoji/em-dashes don't crash


def main():
    names = tools.names()
    print("tools registered:", names)
    for expected in ("get_time", "open_app", "web_search", "remember_fact", "browser_open"):
        assert expected in names, f"missing tool: {expected}"

    # Every schema must be a well-formed function definition.
    for s in tools.schemas():
        assert s["type"] == "function" and "name" in s["function"], s
    print("schemas OK:", len(tools.schemas()), "tools")

    # A pure tool runs and returns a string.
    now = tools.dispatch("get_time", {})
    print("get_time ->", now)
    assert isinstance(now, str) and now

    # Memory round-trips in an isolated in-memory DB.
    m = Memory(":memory:")
    m.remember("name", "Atul")
    assert m.recall("name") == "Atul"
    assert m.recall("unknown") is None
    print("memory OK ->", m.all_facts())

    print("\nALL OFFLINE CHECKS PASSED ✅")


if __name__ == "__main__":
    main()
