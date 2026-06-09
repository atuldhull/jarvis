# JARVIS — Minute-Format Build Guide (What Needs To Be Done)

> Every step, every command, every verified gotcha — for **your exact machine**: HP Victus,
> RTX 4050 6 GB, Ryzen 7 8845HS, 16 GB, Windows 11, Python 3.13.2. All facts verified
> 2026-06-07 ([VERIFIED_FINDINGS.md](VERIFIED_FINDINGS.md)). Build **text-first**; voice last.
> Commands are **PowerShell**. Cost: **₹0**.

---

## Phase 0 — Setup (do this once)

### 0.1 Python & a clean environment
- ✅ You already have **Python 3.13.2** via the `py` launcher. Note: plain `python`/`pip` aren't
  on PATH — **always use `py` and `py -m pip`**.
- 🔴 **Recommended:** install **Python 3.11** alongside it and build the project there. The audio
  stack (faster-whisper, ctranslate2, Kokoro) is best-tested on 3.11/3.12, and it sidesteps every
  3.13 edge case. openWakeWord/onnxruntime *do* work on 3.13/Windows, but one pinned interpreter
  saves debugging.
  ```powershell
  winget install Python.Python.3.11
  py -3.11 -m venv C:\Users\atuld\jarvis\.venv
  C:\Users\atuld\jarvis\.venv\Scripts\Activate.ps1
  # if activation is blocked once:  Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
  ```
  (Staying on 3.13 is fine too: `py -3.13 -m venv .venv`.)

### 0.2 Ollama + the brain
```powershell
ollama --version                 # you have 0.24.0 — update from ollama.com/download (Qwen3.5 tool-call fix)
ollama pull qwen3.5:4b           # ~3.4 GB — the primary brain
ollama pull qwen3:4b             # ~2.5 GB — leaner text-only alt (compare latency)
ollama run qwen3.5:4b            # smoke test: say hi, then /bye
```
🔴 **Raise the context** (Ollama defaults to only **4K** under 24 GB VRAM):
```powershell
$env:OLLAMA_CONTEXT_LENGTH="8192"   # set before 'ollama serve'; start at 8192, raise only if speed holds
```
🧪 After loading, run `ollama ps` — if the **PROCESSOR** column shows a big CPU share, context
spilled to RAM (slow); lower it (6144/4096) until it's mostly GPU.

### 0.3 The Python libraries (with the verified Windows/3.13 fixes)
```powershell
py -m pip install ollama playwright keyring sounddevice soundfile numpy
py -m pip install faster-whisper
py -m pip install webrtcvad-wheels          # 🔴 NOT 'webrtcvad' (no 3.13 wheel)
py -m pip install pywinauto
py -m pip install --upgrade comtypes         # 🔴 must be >=1.4.8 or pywinauto crashes on 3.13
py -m pip install openwakeword
py -m playwright install chromium            # or:  py -m playwright install msedge  (reuse Edge)
```
Voice (add when you reach Phase 4): `py -m pip install kokoro` + install **espeak-ng** (.msi).

**Definition of done:** `ollama run qwen3.5:4b` chats with you, and `py -c "import playwright,
faster_whisper, openwakeword"` runs with no error.

### 0.4 Make it a project (recommended)
```powershell
cd C:\Users\atuld\jarvis
git init
```
Create `.gitignore`:
```
.venv/
profile/            # the Playwright login profile (cookies/secrets — never commit)
__pycache__/
*.gguf
models/
*.wav
```

---

## Phase 1 — The Text Brain ⭐ START HERE (≈1 day)

**Goal:** type → the model replies in your terminal, with a JARVIS persona.

- Build `brain/llm.py` (send text to Ollama, get reply) and a `main.py` chat loop.
- Put the **butler persona in the system prompt** (this is your free, no-training persona):
  > *"You are JARVIS, a calm, dry-witted British butler. Address the user as 'sir'. Be
  > concise, deferential, a touch wry. Never break character."*
- Use the `ollama` Python client; keep a running `messages` list for short-term memory.

🔴 **Windows UTF-8 gotcha (verified, bites immediately):** the terminal defaults to cp1252 and
**crashes** the moment JARVIS prints an em-dash or smart quote (`UnicodeEncodeError`). Fix it in
one line at the top of `main.py`: `sys.stdout.reconfigure(encoding="utf-8")`. (Already done in
the code.)

**Done when:** you have a back-and-forth typed conversation with personality. *(Tip: you can do
this today with your already-installed `qwen2.5:7b` while `qwen3.5:4b` downloads.)*

---

## Phase 2 — Tool Calling ⭐ THE BIG CONCEPT (2–3 days)

**Goal:** the brain triggers real Python code.

- Build `brain/agent.py` — the **plan → act → observe → repeat** loop.
- First 3 tools in `tools/`: `system.open_app("notepad")`, `system.get_time()`,
  `web.search("...")`.
- Expose them to Ollama via its **tools=[...] JSON schema** interface; the model returns a
  structured `tool_call` you dispatch.
- 🔴 **Verify tool-calling works** before building further: send a real `tools=[...]` request and
  confirm a structured call comes back (this is exactly what the Ollama update in 0.2 fixes).

**Done when:** "open notepad and tell me the time" actually does both.

---

## Phase 3 — The Browser Agent ⭐ YOUR BIG UNLOCK (3–5 days)

**Goal:** the YouTube/login/multi-step stuff you actually want.

🔴 **Architecture (verified, important):** write **hand-written Playwright "tool" functions** the
4B model *selects by name* — `open_url`, `search_youtube`, `click_text`, `type_into`, `login`.
**Do NOT** rely on full-autonomous `browser-use` with a local 4B (its own docs warn small models
emit bad action schemas). Keep `browser-use` as an optional experiment only.

- **Stay logged in** with a persistent profile on a **separate empty folder** (🔴 never Chrome's
  real profile — recent Chrome blocks automating it):
  ```python
  ctx = p.chromium.launch_persistent_context(
      r"C:\Users\atuld\jarvis\profile", channel="msedge", headless=False)
  ```
  Log in by hand **once** in that window; cookies persist for every later run.
- Prefer `get_by_role()` / `get_by_text()` selectors over brittle CSS.
- ⚠️ One instance per profile folder (it locks). ⚠️ `pywinauto` can't drive an **elevated** app
  from a non-elevated script (UIPI) — match integrity levels.

**Done when:** "open YouTube, search lo-fi beats, play the first video, skip 30s ahead" works
end-to-end, by typing.

---

## Phase 4 — Add Voice (2–3 days)

**Goal:** speak to it, hear it back.

- `ears/stt.py` — faster-whisper. Start pick: `deepdml/faster-whisper-large-v3-turbo-ct2`
  (int8). Hinglish accuracy pick: convert **Oriserve Whisper-Hindi2Hinglish-Apex** to CT2 int8:
  ```powershell
  py -m pip install ctranslate2 transformers
  ct2-transformers-converter --model Oriserve/Whisper-Hindi2Hinglish-Apex `
    --output_dir hinglish-apex-ct2 --copy_files tokenizer.json preprocessor_config.json `
    --quantization int8
  ```
- `voice/tts.py` — **Kokoro `bm_george` on CPU** (0 VRAM) — see
  [TRAINING_AND_CLONING.md §5](TRAINING_AND_CLONING.md).
- Mic capture: `sounddevice` (16 kHz mono). "Stopped talking": `webrtcvad-wheels`, or start
  simple with **push-to-talk / a fixed 5 s window**.
- 🧪 **VRAM coexistence:** if brain + STT-on-GPU exceeds 6 GB at your context, run **STT on CPU**
  (`device="cpu", compute_type="int8"` — your Ryzen handles it). Keep TTS + wake word on CPU.

**Done when:** you *speak* a command and *hear* the reply, no typing.

---

## Phase 5 — Wake Word + Always-On (1–2 days)

**Goal:** hands-free "Hey Jarvis."

- `ears/wakeword.py` — openWakeWord's pre-made `hey_jarvis` (CPU, 0 VRAM):
  ```python
  import numpy as np, sounddevice as sd
  from openwakeword.model import Model
  oww = Model(wakeword_models=["hey_jarvis"])
  with sd.InputStream(samplerate=16000, channels=1, dtype="int16") as s:
      while True:
          audio, _ = s.read(1280)                    # 80 ms frames
          if oww.predict(audio.flatten())["hey_jarvis"] > 0.5:
              print("WAKE!"); oww.reset()
  ```
- First run downloads models: `import openwakeword; openwakeword.utils.download_models()`.
- Tune the `0.5` threshold up (0.6–0.7) if it false-fires. ⚠️ `pip show openwakeword` should say
  **0.6.0** (not 0.4.0).

**Done when:** "Hey Jarvis" across the room wakes it and it listens.

---

## Phase 6 — Memory, Credentials & Safety (2–3 days) — NOT optional

🔴 Build the safety layer **alongside** the browser agent, not after.

- `memory/store.py` — SQLite (conversation + long-term facts); upgrade to Chroma later.
- `memory/vault.py` — `keyring` → Windows Credential Manager (never plaintext). **Prefer the
  cookie/persistent-profile login over storing+typing passwords** — far lower blast radius.
- `safety.py` — **confirm before irreversible actions** (delete / send / buy / post / any
  password entry): print the intended action, require a typed `yes`. Routine actions (open,
  search, play) run freely.

**Done when:** it reuses a saved login, recalls a fact from yesterday, and asks "are you sure?"
before anything destructive.

---

## Phase 7 — Grow Skills Forever (ongoing)

Add one file per skill in `tools/`: media control, weather, news, reminders, Gmail/Calendar
APIs, WhatsApp Web, file search, OCR, system stats. **Advanced & optional:**
- Vision clicking only as a last resort — and remember `qwen3.5:4b` is **already multimodal**, so
  try the brain-as-grounder first (screenshot → ask for x,y) before loading a separate VLM
  (Holo2-4B), which must **swap** with the brain on 6 GB.
- Fine-tune a custom persona — see [TRAINING_AND_CLONING.md](TRAINING_AND_CLONING.md).

**Done when:** never — this is the fun part.

---

## The 6 GB VRAM budget (keep this in your head)

| Component | Runs on | VRAM |
|---|---|---|
| Brain (qwen3.5:4b) | **GPU** | ~2.5–4 GB (+ context) |
| STT (whisper turbo int8) | GPU *in bursts*, or **CPU** | ~1.5 GB (0 on CPU) |
| TTS (Kokoro/Piper) | **CPU** | ~0 |
| Wake word (openWakeWord) | **CPU** | ~0 |
| Vision (Holo2-4B) — only when needed | **GPU (swap with brain)** | ~3.5–4.5 GB |

Rule: brain on GPU; TTS + wake word on CPU; STT on CPU if context is high; never co-host a
separate vision model with the brain.
