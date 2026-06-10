# JARVIS

> My own Iron-Man-style assistant — a multi-agent **personal operating system** that listens,
> talks back, remembers me, and **runs my computer** (browser, apps, WhatsApp, logins,
> multi-step tasks). **Local-first and free**: it runs on my own laptop, works fully offline,
> and uses free cloud brains only when I want the extra speed.

I wanted a real assistant I actually own — one that runs on my machine, keeps my data on my
machine, speaks my languages, and that I can teach new tricks whenever I want. So I built one.
This repo is the whole thing: the orchestrator, the specialist agents, the model router, the
memory, the voice, and the hands.

```powershell
py main.py            # type to JARVIS in the terminal
py jarvis_live.py console   # talk to it — real conversation (turn-taking, interruptions)
py voice_main.py      # hands-free: say "Hey Jarvis", then talk
```

---

## What it does

- **Runs like a company.** A master **orchestrator** (the CEO) takes a request, and either
  answers it itself or splits it across specialist **departments** — research, software, data,
  browser, system — that run **in parallel** and report back. Each agent has its own job, its
  own tools, and its own dedicated brain. See [docs/AGENTS.md](docs/AGENTS.md).
- **Picks the best brain for every task.** A **model router** sends each request across
  **Gemini → Groq → OpenRouter → local Ollama**, with a pool of free API keys, automatic
  failover, and **task-based key routing** (each kind of work draws on its own key so no single
  free-tier limit becomes a bottleneck). Offline? It silently falls back to local. See
  [docs/MODEL_ROUTER.md](docs/MODEL_ROUTER.md).
- **Remembers me.** Long-term **semantic memory** — it recalls facts by *meaning* (not just
  keywords) and quietly learns durable things about me in the background, across restarts. See
  [docs/MEMORY.md](docs/MEMORY.md).
- **Speaks my languages.** **English, Hindi, Kannada, Hinglish, and mixed** — it hears the
  language I spoke and replies in the same one. See [docs/MULTILINGUAL.md](docs/MULTILINGUAL.md).
- **Has a real conversation.** Streaming voice with natural **turn-taking and interruptions**
  (barge-in) — cut it off mid-sentence and it stops and listens.
- **Does things on the computer:** drives the browser (Playwright), sends/reads WhatsApp, opens
  apps and websites, plays YouTube, controls power (lock/sleep/shutdown), manages files, and
  searches the web — through a plan → act → observe tool loop.
- **Talks like a person, not a help-desk bot.** A sharp, dry-witted persona — set entirely in
  [config.py](config.py), no training needed.

It's **local-first**: with no keys it runs entirely on my machine. Add free keys and it gets
faster and smarter, with the heavy/private stuff still able to stay local.

---

## How it works

```
            ┌──────────────────────────────────────────────┐
  you  ───▶ │            ORCHESTRATOR  (the CEO)           │
            │   classify → plan → delegate → aggregate      │
            └───────┬───────────────┬───────────────┬───────┘
                    │ (simple)      │ (complex: parallel task graph)
                    ▼               ▼               ▼
              general          research         software   …  data, browser, system
                    └───────────────┴───────────────┘
                                    ▼
        tools (hands)  +  model router (resource manager)  +  memory (knowledge)
```

Everyday messages take a fast path; complex ones get planned into a task graph and run across
departments. Every "thought" flows through the model router, so the whole org runs on the local
brain offline and upgrades to the cloud brains the moment keys are added. Voice is an I/O
wrapper around the same brain — which is why the whole thing is fully usable by typing.

---

## The stack (all free / open-source; local-first)

| Layer | What I use |
|---|---|
| Brains | **Gemini + Groq + OpenRouter** (free tiers) → **local Ollama**, via the model router |
| Orchestrator + agents | custom multi-agent layer (`agents/`) — departments scoped by prompt + tools |
| Memory | **SQLite** + local **Ollama embeddings** (semantic recall) |
| Ears (speech-to-text) | **Sarvam** (Indian languages) → local **faster-whisper** |
| Voice (text-to-speech) | **Sarvam** (Hindi/Kannada) → local **Piper** → Windows voice |
| Conversational voice | **LiveKit Agents** (turn-taking, interruptions) + **Silero** VAD |
| Wake word | **openWakeWord** ("Hey Jarvis") |
| Browser / apps / WhatsApp | **Playwright** + a persistent logged-in profile |
| Credentials | **keyring** → Windows Credential Manager |

---

## Run it yourself

1. **Install [Ollama](https://ollama.com)** and pull the local brain + embeddings:
   ```powershell
   ollama pull qwen2.5:7b
   ollama pull nomic-embed-text     # for semantic memory
   ```
2. **Python** (3.11+; built on 3.13) + dependencies:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   py -m pip install -r requirements.txt
   playwright install               # one-time, for browser control
   ```
3. **(Optional) Free cloud brains + Indian-language voice** — copy the template and paste keys:
   ```powershell
   copy keys.example.json keys.json   # git-ignored; add Gemini/Groq/OpenRouter/Sarvam keys
   ```
   No keys? It runs fully local. See [docs/MODEL_ROUTER.md](docs/MODEL_ROUTER.md) for where to
   get free keys.
4. **Go:**
   ```powershell
   py main.py                 # text
   py jarvis_live.py console  # conversational voice (local mic, no server)
   py voice_main.py           # wake-word voice loop
   ```

Everything — model, persona, routes, voices, memory — is tuned in one place: [config.py](config.py).

---

## Project layout

```
config.py            every setting in one place
main.py              text entry point
jarvis_live.py       conversational voice (LiveKit: turn-taking + interruptions)
voice_main.py        wake-word voice loop
safety.py            confirm-before-irreversible-action guardrail
brain/               model router, multi-key pool, provider adapters, the agent loop
agents/              the orchestrator (CEO) + the specialist departments
tools/               the actions (time, apps, power, web, files, browser, youtube, whatsapp, memory)
memory/              semantic long-term memory (embeddings + SQLite) + the credential vault
ears/  voice/        speech-to-text and text-to-speech (Sarvam + local)
docs/                architecture, router, agents, memory, multilingual, voice, roadmap, budget
```

---

## Runs on

Built and running on an HP Victus laptop: **RTX 4050 (6 GB VRAM)**, Ryzen 7 8845HS, 16 GB RAM,
Windows 11. Every local model is chosen to fit 6 GB; lighter machines work too — pick a smaller
model in [config.py](config.py).

---

## Cost

**₹0.** Everything is free and open-source — free cloud tiers + local models, no paid models, no
paid datasets, no cloud bills. Details in [docs/BUDGET.md](docs/BUDGET.md).

---

## Docs

- [docs/AGENTS.md](docs/AGENTS.md) — the orchestrator + specialist departments
- [docs/MODEL_ROUTER.md](docs/MODEL_ROUTER.md) — multi-provider routing, key pool, task-based keys
- [docs/MEMORY.md](docs/MEMORY.md) — long-term semantic memory
- [docs/MULTILINGUAL.md](docs/MULTILINGUAL.md) — English / Hindi / Kannada voice
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — how it all fits together
- [docs/CODE_OVERVIEW.md](docs/CODE_OVERVIEW.md) — a map of the code
- [docs/VOICE.md](docs/VOICE.md) · [docs/MODELS_AND_DATASETS.md](docs/MODELS_AND_DATASETS.md) ·
  [docs/ROADMAP.md](docs/ROADMAP.md) · [docs/BUDGET.md](docs/BUDGET.md)
