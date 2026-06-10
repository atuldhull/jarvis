# JARVIS OS — The Agent Layer

JARVIS runs like a small company: a **CEO (the orchestrator)** takes a request, and
either answers it himself or delegates to **departments (specialist agents)**, who use
**tools (the employees)** and a **shared memory + model router (the infrastructure)**.

```
            ┌──────────────────────────────────────────────┐
  you  ───▶ │           ORCHESTRATOR  (the CEO)            │
            │   classify → plan → delegate → aggregate      │
            └───────┬───────────────┬───────────────┬───────┘
                    │ (simple)      │ (complex: task graph)
                    ▼               ▼               ▼
              ┌──────────┐   ┌──────────┐    ┌──────────┐
              │ general  │   │ research │    │ software │  …  data, automation
              └────┬─────┘   └────┬─────┘    └────┬─────┘
                   └──────────────┴───────────────┘
                                  ▼
                    tools (registry)  +  model router  +  memory
```

Everything thinks through the **[model router](MODEL_ROUTER.md)**, so the whole org runs on
the local brain today and upgrades to the fast cloud brains the moment you add keys.

---

## The flow

1. **Classify (fast).** A cheap heuristic decides if a message is *simple* (one short
   answer / one tool) or *complex* (multiple dependent steps or several specialists).
   It **biases hard toward simple**, so everyday chat stays instant — no planning overhead.
2. **Simple → general agent.** The everyday assistant (full persona, all tools) answers
   directly. This is the same fast path you've always had.
3. **Complex → plan.** The planner (an LLM call) turns the request into a **task graph**:
   a list of steps, each assigned to a department, each with `depends_on`. Independent
   steps have no dependencies; dependent steps name the steps they need.
4. **Execute in parallel.** Steps whose dependencies are done run **concurrently on worker
   threads** (`config.ORCH_MAX_WORKERS`); dependent steps are handed their prerequisites'
   outputs as context. A step that fails is captured, not fatal — the rest carry on.
5. **Aggregate.** All step results + the original request go to the aggregator (one LLM
   call), which fuses them into a single reply in JARVIS's voice. Reply language is forced
   to match the language you wrote in (English unless you wrote Hindi).

> Planning and aggregation quality scale with the brain. On the local 6 GB model they're
> *okay*; with a cloud key (Gemini/Groq) they get much sharper. The fast simple-path is
> unaffected either way.

---

## The departments

| Department | Handles | Key tools |
|---|---|---|
| **general** | everyday chat + simple single-tool requests | all tools |
| **research** | web/browser investigation, fact-checking, market/competitor analysis | browser_*, web_search, find/read files, memory |
| **software** | write/debug/refactor code, design architecture/APIs/schemas/Docker | file read/write, find, web_search, memory |
| **data** | SQL, data/document analysis, report/chart specs, ETL design (output as text) | file read/write, find, web_search, memory |
| **browser** | web/Chrome actions, YouTube/media, WhatsApp messaging | browser_*, youtube_*, whatsapp_*, web_search |
| **system** | open desktop apps, time/system info, PC power control | open_app, get_time/info, lock/sleep/shutdown/restart |

Each department is the same `Agent` class scoped to a **system prompt**, a **tool subset**, and
a **task route** (its dedicated Gemini key) — so the research agent literally cannot fire
`shutdown_pc`, and browsing draws from a different free-tier key than coding. Defined in
[agents/roster.py](../agents/roster.py); see [task-based routing](MODEL_ROUTER.md#task-based-key-routing).

Confirm-gated tools (`whatsapp_send`, `shutdown_pc`, `restart_pc`, `delete_file`) still ask
before firing, even inside a delegated step.

---

## Using it

It's already wired into `main.py` — just run JARVIS and talk:

```powershell
py main.py
you> what time is it                          # simple → instant
you> research the best free TTS voices and save a summary to tts.txt   # complex → plan+execute
```

You'll see the org working (set `ORCHESTRATOR_VERBOSE = False` to silence it):
```
[orchestrator] complex request → planning…
[orchestrator] running 2 steps across research, software
[orchestrator] s1 (research) done
[orchestrator] s2 (software) done
[orchestrator] aggregating results…
```

### Config knobs ([config.py](../config.py))
- `ORCHESTRATOR_ENABLED` — `False` falls back to the plain single agent.
- `ORCH_MAX_WORKERS` — how many steps run at once (keep 2–4 on local; cloud handles more).
- `ORCHESTRATOR_VERBOSE` — show/hide the orchestration log.

---

## The pieces

```
agents/orchestrator.py   classify → plan → parallel execute → aggregate (the CEO)
agents/roster.py         the departments: system prompt + tool subset each
brain/agent.py           the plan→act→observe tool loop (scopable to a tool subset)
```

It builds on the existing tool registry, the [model router](MODEL_ROUTER.md), and the
SQLite memory — nothing was thrown away; the orchestrator sits on top.

---

## What's next on the OS

- A light **local dashboard** (agents active, model/key usage, quota, latency).
- More departments as needed (PM, DevOps, UI/UX, QA, Security) — each is just another
  roster entry.
- A "force local for sensitive tasks" routing switch.
