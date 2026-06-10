"""Memory tests: embeddings, semantic store/search, dedup, recall injection, capture parse."""

import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

import config
config.ROUTER_VERBOSE = False
config.ORCHESTRATOR_VERBOSE = False
config.MEMORY_DB = "_test_memory.db"  # isolate from the real jarvis.db (set BEFORE imports below)
if os.path.exists(config.MEMORY_DB):
    os.remove(config.MEMORY_DB)

from memory.embed import embed
from memory.store import Memory
from memory.manager import MemoryManager


def test_embed():
    v = embed("the user has an RTX 4050 GPU")
    print("1) embeddings:", f"vector of {len(v)} dims ✓" if v else "UNAVAILABLE → keyword fallback")
    return v is not None


def test_semantic_search():
    m = Memory()
    m.add_memory("The user's name is Atul.")
    m.add_memory("The user's GPU is an RTX 4050 with 6GB VRAM.")
    m.add_memory("The user loves spicy food.")
    hits = m.search("what graphics card does he have", k=2)
    print("2) semantic search 'graphics card' ->", hits)
    assert any("RTX 4050" in h for h in hits), hits
    m.close()


def test_dedup():
    m = Memory()
    a = m.add_memory("The user is building a JARVIS assistant.")
    b = m.add_memory("The user is building a JARVIS assistant.")  # exact duplicate
    print(f"3) dedup: exact duplicate returns same id ({a} == {b})")
    assert a == b
    m.close()


def test_recall_context():
    mm = MemoryManager()
    mm.store.add_memory("The user's favorite programming language is Python.")
    ctx = mm.recall_context("which language should I write this in")
    print("4) recall_context ->", repr(ctx[:90]))
    assert "Python" in ctx
    mm.store.close()


def test_capture_parse():
    facts = MemoryManager._parse(
        'Here: {"facts": ["The user lives in India.", "The user codes in Python."]}')
    print("5) capture parse ->", facts)
    assert facts == ["The user lives in India.", "The user codes in Python."]


def test_agent_slot():
    from brain.agent import Agent
    a = Agent()
    a.set_memory_context("MEM-ONE")
    assert a.messages[1]["content"] == "MEM-ONE" and a._ctx_idx == 1
    a.set_memory_context("MEM-TWO")  # refresh in place, not append
    systems = [m for m in a.messages if m["role"] == "system"]
    assert a.messages[1]["content"] == "MEM-TWO" and len(systems) == 2
    print("6) agent memory slot refreshes in place (no accumulation)")


if __name__ == "__main__":
    test_embed()
    test_semantic_search()
    test_dedup()
    test_recall_context()
    test_capture_parse()
    test_agent_slot()
    try:  # best-effort cleanup (Windows holds the file while connections are open)
        os.remove(config.MEMORY_DB)
    except OSError:
        pass
    print("\n✅ memory tests passed")
