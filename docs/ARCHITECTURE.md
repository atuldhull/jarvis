# JARVIS — Architecture

How the whole thing works, end to end. Read this once and the project stops feeling
like magic.

---

## 1. The core loop (the soul of JARVIS)

Strip away the movie and JARVIS is a **5-step loop**:

```
┌─────────────────────────────────────────────────────────────┐
│                         YOU (voice / text)                    │
└───────────────┬───────────────────────────┬──────────────────┘
                │ speak                        ▲ hears reply
                ▼                              │
        ┌──────────────┐               ┌──────────────┐
        │  WAKE WORD   │               │     TTS      │  ← Piper / Kokoro (local)
        │ "Hey Jarvis" │               │  (the voice) │
        └──────┬───────┘               └──────▲───────┘
               ▼                              │
        ┌──────────────┐                      │
        │  STT (ears)  │  ← faster-whisper    │
        └──────┬───────┘     (local)          │
               ▼ text                         │ text reply
        ╔══════════════════════════════════════════════╗
        ║              THE BRAIN  (local LLM)            ║
        ║        Ollama: Qwen3.5 4B (free, downloaded)   ║
        ║   - understands what you meant                 ║
        ║   - PLANS multi-step tasks                     ║
        ║   - picks which tool to use                    ║
        ║   - reads the result, decides the next step    ║
        ╚════════════════════╦═══════════════════════════╝
                             │ "tool calls" (function calling)
              ┌──────────────┼───────────────┬───────────────┐
              ▼              ▼               ▼               ▼
       ┌───────────┐  ┌───────────┐  ┌────────────┐  ┌────────────┐
       │  SYSTEM   │  │  BROWSER  │  │ GUI/SCREEN │  │   APIs &   │
       │  CONTROL  │  │ (Playwright)│ │  CONTROL   │  │  SERVICES  │
       └───────────┘  └───────────┘  └────────────┘  └────────────┘
                             ▼
                ┌──────────────────────────┐
                │  MEMORY + CREDENTIAL VAULT │
                │   (SQLite + keyring)       │
                └──────────────────────────┘
```

The 5 steps:
1. **Hear you** — wake word + microphone + speech-to-text
2. **Understand & decide** — the LLM brain figures out intent and the plan
3. **Do the thing** — the tool layer actually performs the action
4. **Talk back** — text-to-speech speaks the reply
5. **Remember** — short-term + long-term memory, plus your credentials

> 🔑 **Key insight:** the brain works in **text**. Voice is just a wrapper —
> speech-to-text on the way in, text-to-speech on the way out. So I build and test
> everything by **typing first**, and bolt voice on later. This is why the roadmap
> starts text-only.

---

## 2. How JARVIS actually controls the computer (the crucial part)

There is no single "do anything" trick. There's a **spectrum** of control methods,
from rock-solid to magical-but-fragile. A real JARVIS uses **all of them** and picks
the best one per task.

| Level | Method | Tool | Best for | Trade-off |
|---|---|---|---|---|
| **1. API / Service** | Talk directly to a service's official API | `requests`, SDKs | Weather, email, music | Most reliable — but only where an API exists |
| **2. Browser automation** | Drive a real browser via the page's HTML | **Playwright** | "open YouTube, search, log in, play, skip ahead" — **all web tasks** | Reliable; can log in and **stay** logged in |
| **3. OS / app control** | Launch apps, files, volume, keystrokes | `subprocess`, `pyautogui`, `pywinauto` | Opening programs, desktop apps | Solid for launching; raw clicks can be brittle |
| **4. Vision ("computer use")** | Screenshot → a vision model looks → decides where to click | Moondream / Qwen-VL + `pyautogui` | Literally anything a human can see and click | Most general, but slow + error-prone + heavy |

**For your goal ("open YouTube, type this, forward the video, log in with my id/pass"):**
that is **Level 2 — Playwright browser automation.** It's your workhorse. You add
Level 1 (APIs) where they exist for reliability, Level 3 for desktop apps, and Level 4
later as the "fallback that can do anything." Building in that order is what makes the
project *succeed* instead of stalling.

---

## 3. A real multi-step command, traced

> *"Hey Jarvis, open YouTube, search lo-fi beats, and play the first one."*

```
wake word ("Hey Jarvis")  →  STT turns speech into text
        ↓
BRAIN plans the steps:
   step 1: browser.open("youtube.com")          → Playwright
   step 2: browser.type_search("lo-fi beats")   → Playwright
   step 3: browser.read_results()               → brain reads the page
   step 4: browser.click(first_video)           → Playwright
   step 5: verify it's playing                  → brain checks
        ↓
TTS: "Now playing lo-fi beats, sir."
```

That **plan → act → observe → decide-next-step → repeat** cycle is called an
**agent loop** (ReAct pattern). Get it right and every new ability becomes easy to add.

---

## 4. Project structure (modules you'll build)

```
jarvis/
├── main.py                # the loop: listen → think → act → speak
├── config.py              # settings + persona ("You are Jarvis, calm, witty...")
├── brain/
│   ├── llm.py             #   talks to Ollama
│   └── agent.py           #   the plan→act→observe loop + tool dispatch
├── ears/
│   ├── wakeword.py        #   "Hey Jarvis" detection
│   └── stt.py             #   faster-whisper speech-to-text
├── voice/
│   └── tts.py             #   Piper / Kokoro speech-out
├── memory/
│   ├── store.py           #   conversation + long-term facts (SQLite)
│   └── vault.py           #   credentials via keyring (Windows Credential Manager)
├── tools/                 # ← you grow this FOREVER (each file = one skill)
│   ├── system.py          #   open apps, files, volume, screenshots
│   ├── browser.py         #   Playwright: open, type, click, login
│   ├── gui.py             #   pyautogui fallback (desktop apps)
│   ├── web.py             #   search, weather, fetch a page
│   └── apps.py            #   spotify, gmail, calendar, ...
└── safety.py              # confirm-before-risky-action rules
```

Each file in `tools/` is one "skill." Adding abilities = adding a file here and
telling the brain it exists. That's the part that grows forever.

---

## 5. Memory & credentials

- **Short-term memory:** the running conversation (kept in RAM, trimmed to fit the
  model's context window).
- **Long-term memory:** facts about you and your preferences — start with a simple
  SQLite file; upgrade to a vector database (Chroma) later for "remember everything."
- **Credential vault:** passwords go into **Windows Credential Manager** via the
  `keyring` library (encrypted by the OS — never plain text in a file).
- **Smarter trick:** a **persistent browser profile** in Playwright means JARVIS logs
  in *once*, and stays logged in — so it rarely needs to retype passwords at all.

---

## 6. Safety guardrails (part of the design, not optional)

Because this agent can click anything and use your logins, the architecture includes a
`safety.py` that forces a **confirmation step before irreversible actions**:
deleting files, sending money, posting publicly, buying things, emailing people.
One rule, and it saves you from expensive accidents. Everything routine (open app,
search, play video) runs without nagging you.

---

## 7. The tech stack at a glance (all free, all local)

| Layer | Tool | Why |
|---|---|---|
| Brain | **Ollama + Qwen3.5 4B** | Free, strong at tool-calling, fits 6GB |
| Ears | **faster-whisper** | Free, accurate, GPU-accelerated |
| Voice | **Piper** (or **Kokoro**) | Free, fast, natural, British voices available |
| Wake word | **openWakeWord** ("hey jarvis") | Free, pre-made "Hey Jarvis" model exists |
| Browser | **Playwright** | The workhorse for "do anything on the web" |
| OS control | **pyautogui / pywinauto / subprocess** | Apps, files, keys, windows |
| Memory | **SQLite → Chroma** | Simple now, scalable later |
| Secrets | **keyring** | OS-encrypted credential storage |
| Glue | **Python** | Best ecosystem for all of the above |

Exact versions, sizes, and download links → [MODELS_AND_DATASETS.md](MODELS_AND_DATASETS.md)
