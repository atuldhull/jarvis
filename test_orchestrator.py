"""Orchestrator tests: classification heuristic, plan parsing, parallel execution
with dependency/context passing (mocked), and one LIVE complex run on the local brain.
"""

import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

import config
import agents.orchestrator as orch
from agents.orchestrator import Orchestrator, _extract_json
from agents.roster import DEPARTMENTS, make_agent

config.ORCHESTRATOR_VERBOSE = False
config.ROUTER_VERBOSE = False


# 1) The simple/complex heuristic.
def test_heuristic():
    o = Orchestrator()
    simple = ["hi", "what time is it", "lock my pc", "open youtube and play lofi",
              "write me a python script that renames files"]
    complex_ = ["research the best budget laptops in india and save a summary to laptops.txt",
                "compare kokoro and piper and summarize the differences for me",
                "find my csv files, analyze them, and then write me the SQL"]
    for t in simple:
        assert not o._looks_complex(t), f"should be simple: {t}"
    for t in complex_:
        assert o._looks_complex(t), f"should be complex: {t}"
    print("1) heuristic: simple/complex split correct")


# 2) JSON extraction tolerates code fences + prose.
def test_extract_json():
    messy = 'Sure! Here you go:\n```json\n{"steps":[{"id":"s1","agent":"research","task":"go","depends_on":[]}]}\n```\nhope that helps'
    data = _extract_json(messy)
    assert data and data["steps"][0]["id"] == "s1"
    print("2) json extraction: pulled clean JSON out of fenced/prose reply")


# 3) Plan validation rejects forward/cyclic dependencies.
def test_plan_validation():
    o = Orchestrator()
    good = '{"steps":[{"id":"s1","agent":"research","task":"a","depends_on":[]},{"id":"s2","agent":"software","task":"b","depends_on":["s1"]}]}'
    bad = '{"steps":[{"id":"s1","agent":"research","task":"a","depends_on":["s2"]},{"id":"s2","agent":"software","task":"b","depends_on":[]}]}'
    assert o._parse_plan(good) and len(o._parse_plan(good)) == 2
    assert o._parse_plan(bad) is None  # s1 depends on a later step → invalid
    print("3) plan validation: accepts valid DAG, rejects forward/cyclic deps")


# 4) Parallel execution + dependency context passing (mocked agents, no LLM).
def test_execute_parallel():
    o = Orchestrator()
    o.workers = 3
    started = {}
    received = {}

    class Fake:
        def __init__(self, name):
            self.name = name

        def run(self, task, max_steps=6):
            started[self.name] = time.time()
            received[self.name] = task
            time.sleep(0.3)  # simulate work to observe parallelism
            return f"output-of-{self.name}"

    # s1 and s2 are independent; s3 depends on both.
    steps = [
        {"id": "s1", "agent": "research", "task": "do one", "depends_on": []},
        {"id": "s2", "agent": "data", "task": "do two", "depends_on": []},
        {"id": "s3", "agent": "software", "task": "combine", "depends_on": ["s1", "s2"]},
    ]
    orig = orch.make_agent
    orch.make_agent = lambda name: Fake(name)
    try:
        t0 = time.time()
        results = o._execute(steps)
        elapsed = time.time() - t0
    finally:
        orch.make_agent = orig

    out = {sid: text for sid, _agent, text in results}
    # s1 & s2 ran in parallel → total < 3 * 0.3 (would be 0.9 if serial); ~0.6 here.
    print(f"4) parallel execution: finished in {elapsed:.2f}s (serial would be ~0.9s)")
    assert elapsed < 0.8, f"steps did not run in parallel ({elapsed:.2f}s)"
    # s3 received s1 & s2 outputs as context.
    assert "output-of-research" in received["software"] and "output-of-data" in received["software"]
    assert out["s3"] == "output-of-software"
    print("   dependency context passed into the dependent step ✓")


# 5) Roster builds scoped agents with the right tool subsets.
def test_roster():
    a = make_agent("research")
    assert a.name == "research" and "web_search" in a.tool_names and "shutdown_pc" not in a.tool_names
    g = make_agent("general")
    assert g.name == "general" and g.tool_names is None  # full toolset
    print("5) roster: department agents scoped to their tools; general gets all")


# 6) LIVE: a real complex request planned + executed + aggregated on the local brain.
def test_live_complex():
    o = Orchestrator()
    req = ("Write a short two-line poem about coffee and save it to coffee.txt, "
           "and also tell me the current date and time.")
    try:
        t0 = time.time()
        reply = o.handle(req)
        print(f"\n6) LIVE complex run [{time.time()-t0:.1f}s]:\n   plan = "
              f"{[(s['id'], s['agent']) for s in (o.last_plan or [])]}\n   reply = {reply[:240]!r}")
        import os
        if os.path.exists("coffee.txt"):
            print("   coffee.txt written ✓")
            os.remove("coffee.txt")
    except Exception as e:
        print("6) LIVE complex run SKIPPED (is Ollama running?):", e)


if __name__ == "__main__":
    test_heuristic()
    test_extract_json()
    test_plan_validation()
    test_execute_parallel()
    test_roster()
    test_live_complex()
    print("\n✅ orchestrator tests passed")
