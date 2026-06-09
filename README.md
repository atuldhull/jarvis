# JARVIS

> My own Iron-Man-style assistant — it listens, talks back, and **controls my computer**
> (browser, apps, logins, multi-step tasks). It runs **fully offline and free** on my own
> laptop. No cloud, no API keys, no subscriptions.

I wanted a real assistant I actually own — one that runs on my machine, keeps my data on my
machine, and that I can teach new tricks whenever I want. So I built one. This repo is the
whole thing: the brain, the ears, the voice, the hands, and the memory.

```powershell
# from the jarvis folder, with Ollama running:
py main.py            # type to JARVIS in the terminal
py voice_main.py      # hands-free: say "Hey Jarvis", then talk
```

---

## What it does

- **Talks like a person, not a help-desk bot.** A sharp, dry-witted persona that answers
  straight and gets things done — set entirely in [config.py](config.py), no training needed.
- **Bilingual.** Speak English or Hindi; it auto-detects and replies in the same language —
  a British voice for English, an Indian voice for Hindi.
- **Takes real actions** through a tool-calling loop (plan → act → observe → reply):
  tells the time, reads system info, opens apps and websites, manages files, searches the
  web, and remembers facts across sessions.
- **Drives the browser** with Playwright — opens pages, searches, clicks, and stays logged
  in through a dedicated browser profile.
- **Remembers** long-term facts in a local SQLite database, and stores logins safely in the
  Windows Credential Manager (never in code, never in the repo).
- **Hands-free** with a "Hey Jarvis" wake word, speech-to-text, and a humanized neural voice.

Everything runs locally. Nothing leaves the machine.

---

## How it works

A simple loop:

```
wake word  →  speech-to-text  →  the brain (plans + picks tools)  →  tool runs the action  →  text-to-speech  →  memory
```

The brain thinks in text; voice is just an input/output wrapper around it — which is why you
can use the whole thing by typing, with no microphone at all. Full write-up in
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## The stack (all free / open-source / local)

| Piece | What I use | Notes |
|---|---|---|
| Brain (LLM) | **Ollama** + a small Qwen model | Talks to Ollama's HTTP API using only Python's standard library — the core needs **zero pip packages**. |
| Ears (speech-to-text) | **faster-whisper** | Auto-detects English vs Hindi. |
| Voice (text-to-speech) | **Piper** neural voices | British voice for English, Indian voice for Hindi; falls back to the built-in Windows voice. |
| Wake word | **openWakeWord** | Ships a pre-trained "Hey Jarvis" model. |
| Browser control | **Playwright** | Persistent profile keeps logins alive between runs. |
| Credentials | **keyring** → Windows Credential Manager | Real logins, stored safely outside the codebase. |
| Memory | **SQLite** | Long-term facts that survive restarts. |

---

## Run it yourself

1. **Install [Ollama](https://ollama.com)** and pull a model:
   ```powershell
   ollama pull qwen2.5:7b
   ```
2. **Set up Python** (3.11+; built and tested on 3.13) and the dependencies:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   py -m pip install -r requirements.txt
   playwright install        # one-time, for browser control
   ```
3. **Voice models** (optional — only needed for spoken replies). Drop the Piper voices into
   `voices/` (kept out of the repo because they're large):
   ```powershell
   # English (British) + Hindi voices from huggingface.co/rhasspy/piper-voices
   # save as voices/en_GB-alan-medium.onnx and voices/hi_IN-pratham-medium.onnx
   ```
4. **Go:**
   ```powershell
   py main.py            # text chat
   py voice_main.py      # voice mode (needs a mic)
   ```

Tweak everything — model, persona, voices, wake-word sensitivity — in one place:
[config.py](config.py).

---

## Project layout

```
config.py            every setting in one place (model, persona, voices, thresholds)
main.py              text entry point
voice_main.py        hands-free voice entry point
safety.py            confirm-before-irreversible-action guardrail
brain/               the LLM client + the tool-calling agent loop
tools/               the actions JARVIS can take (time, apps, web, files, memory, browser)
ears/                microphone capture, voice-activity detection, speech-to-text, wake word
voice/               text-to-speech (bilingual voice selection)
memory/              SQLite long-term memory + the credential vault
docs/                architecture, models, voice, roadmap, budget
```

A guided tour of the code is in [docs/CODE_OVERVIEW.md](docs/CODE_OVERVIEW.md).

---

## Runs on

Built and running on an HP Victus laptop: **RTX 4050 (6 GB VRAM)**, Ryzen 7 8845HS, 16 GB
RAM, Windows 11. Every model pick is chosen to fit in 6 GB. It'll run on lighter machines
too — just pick a smaller model in [config.py](config.py).

---

## Cost

**₹0.** Every piece is free and open-source. No paid models, no paid datasets, no cloud bills.
Details in [docs/BUDGET.md](docs/BUDGET.md).

---

## Docs

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — how it all fits together
- [docs/CODE_OVERVIEW.md](docs/CODE_OVERVIEW.md) — a map of the code
- [docs/MODELS_AND_DATASETS.md](docs/MODELS_AND_DATASETS.md) — every model, source, and size
- [docs/VOICE.md](docs/VOICE.md) — speech-to-text and the voices, in depth
- [docs/ROADMAP.md](docs/ROADMAP.md) — the build plan, phase by phase
- [docs/BUDGET.md](docs/BUDGET.md) — every cost (spoiler: zero)
