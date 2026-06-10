# JARVIS — Code Overview (the foundation)

> A map of the original foundation code. The project has since grown a full OS layer on
> top — the orchestrator + specialist departments, the model router, semantic memory, and
> the voice stack. For the current architecture see [AGENTS.md](AGENTS.md),
> [MODEL_ROUTER.md](MODEL_ROUTER.md), [MEMORY.md](MEMORY.md), and [MULTILINGUAL.md](MULTILINGUAL.md).
> This file still describes the core loop everything is built on, which hasn't changed.

## Run it

```powershell
.venv\Scripts\Activate.ps1     # use the project venv (Python in C:\Users\atuld\jarvis\.venv)
py main.py                     # chat with JARVIS in the terminal
```
Type to talk. `exit` / `quit` / `bye` (or Ctrl+C) leaves. The brain is whatever
`config.MODEL` points at (currently `qwen2.5:7b`; switch to `qwen3.5:4b` once pulled).

## The files

```
jarvis/
├── config.py            One place for every setting: MODEL, PERSONA, TEMPERATURE,
│                        TOOL_GUIDANCE, BROWSER_PROFILE, MEMORY_DB, KEYRING_SERVICE.
├── main.py              The terminal chat loop. Uses Agent (so JARVIS has hands).
├── safety.py            confirm() — the "are you sure?" gate for sensitive tools.
│
├── brain/
│   ├── ollama_client.py stdlib (urllib) client for Ollama's HTTP API — so the
│   │                    brain needs NO pip package. Just Ollama + a pulled model.
│   ├── llm.py           Brain: plain chat — holds the conversation, calls Ollama.
│   └── agent.py         Agent: the plan→act→observe loop. Hands the model the tool
│                        menu, runs whatever it calls, feeds results back, repeats.
│
├── tools/               JARVIS's hands. Add a skill = add an @tool function here.
│   ├── registry.py      @tool decorator + schemas()/dispatch()/needs_confirm().
│   ├── system.py        get_time, open_app.
│   ├── web.py           open_website, web_search (default browser).
│   ├── memory_tools.py  remember_fact, recall_fact (wraps memory/store.py).
│   └── browser.py       Phase 3: Playwright skills — browser_open/click/type/read,
│                        youtube_search, youtube_play_first. Lazy-imports Playwright.
│
├── memory/
│   ├── store.py         Memory: SQLite facts + turn log (jarvis.db).
│   └── vault.py         keyring wrapper → Windows Credential Manager.
│
├── ears/                Phase 4/5 — hearing you.
│   ├── wakeword.py      WakeWord: openWakeWord 'hey_jarvis' (CPU, offline).
│   ├── mic.py           record_to_wav: microphone capture (sounddevice).
│   └── stt.py           STT: faster-whisper speech-to-text.
├── voice/
│   └── tts.py           say(): Windows built-in speech (Kokoro/Piper = upgrades).
└── voice_main.py        Voice loop: wake → listen → think → speak.
```

## How a turn flows (Agent loop)

1. `main.py` reads your text → `Agent.run(text)`.
2. `Agent` sends `messages` + `tools=schemas()` to Ollama.
3. If the model returns **tool_calls** → for each, `safety.confirm()` (if the tool is
   sensitive), then `tools.dispatch(name, args)`; the result is appended as a `tool`
   message and the loop continues.
4. If the model returns plain text → that's the reply; the loop ends.
5. Hard cap of `max_steps=6` so it can't loop forever.

## Adding a new skill (the pattern you repeat forever)

```python
# in tools/system.py (or a new module imported by tools/__init__.py)
from .registry import tool

@tool("set_volume", "Set system volume 0-100.",
      {"type": "object", "properties": {"level": {"type": "integer"}}, "required": ["level"]},
      confirm=False)
def set_volume(level):
    ...                      # do the thing
    return f"Volume set to {level}."
```
That's it — the model now sees `set_volume` on its menu and can call it. Mark
`confirm=True` for anything irreversible (delete/send/buy/post/login).

## Status & next

- ✅ **Phase 1** (text brain) — **verified live** on `qwen2.5:7b`.
- ✅ **Phase 2** (tool-calling) — **verified live**: full plan→act→observe→reply loop
  (asked the time → model called `get_time` → replied in character).
- ✅ Offline checks pass (`py test_jarvis.py`): 12 tools, schemas, memory round-trip.
- ✅ Core needs **no pip packages** — `py main.py` runs now (with Ollama running).
- ✅ **Phase 3** (browser) — **verified**: Playwright drove Edge (headless) and loaded a page.
  Run the YouTube skills via `main.py` when you want a window (uses a persistent profile).
- ✅ **Phase 6** (memory + vault + safety) — **verified**: SQLite facts + a Windows Credential
  Manager round-trip.
- ✅ **Phase 4/5** (voice) — **verified** (`py test_voice.py`): faster-whisper STT loaded,
  openWakeWord `hey_jarvis` loaded (onnxruntime on Windows), TTS imports. The mic→speak loop
  is `voice_main.py` (run with a mic + speakers). TTS defaults to Windows' built-in speech (no
  install); Kokoro/Piper are quality upgrades.
- ⏭ Next: try `voice_main.py` end-to-end with a mic, then upgrade STT to the turbo/Hinglish
  model and TTS to a British voice. See [VOICE.md](VOICE.md) + [BUILD_GUIDE_MINUTE.md](BUILD_GUIDE_MINUTE.md).

## Quick tests

```powershell
py test_jarvis.py        # offline: tools + memory (no model needed)
py test_raw_ollama.py    # checks Ollama + model + tool-calling over raw HTTP
py test_llm.py           # full Brain + Agent integration (needs Ollama running)
```
