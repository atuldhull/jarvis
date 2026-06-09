# JARVIS — Build Roadmap (Phase by Phase)

The exact order to build in, so you never feel stuck. Each phase has a clear goal, the
tools used, and a **"definition of done"** — when that's true, move on.

> ⏳ Golden rule: **build text-first.** Voice is added late. The brain works in text;
> voice is just an input/output wrapper. Testing by typing is 10× faster than by
> talking, so we keep it text-only until the brain is smart.

---

## Phase 0 — Setup (½ day)
**Goal:** tools installed, nothing built yet.

- [ ] Install Python 3.11+ → <https://python.org>
- [ ] Install Ollama (current build) → <https://ollama.com> → `ollama pull qwen3.5:4b`
- [ ] Create the project folder + a Python virtual environment
- [ ] `pip install`: ollama, faster-whisper, piper-tts, openwakeword, playwright,
      pyautogui, pywinauto, pygetwindow, keyring, sounddevice
- [ ] `playwright install`

**Done when:** `ollama run qwen3.5:4b` chats with you in the terminal.

---

## Phase 1 — The Text Brain (1 day) ⭐ START HERE
**Goal:** type a message → the model replies in your terminal. A conversation loop.

- Tools: Ollama + Python
- Build `brain/llm.py` (send text to Ollama, get reply) and a basic `main.py` loop.
- Add the **persona** system prompt ("You are Jarvis, a calm, witty British assistant…").

**Done when:** you can have a back-and-forth typed conversation with a personality.

---

## Phase 2 — Giving it Hands: Tool Calling (2–3 days) ⭐ THE BIG CONCEPT
**Goal:** the brain can *trigger real code* — this is the heart of everything.

- Build `brain/agent.py` — the **plan → act → observe → repeat** loop.
- Add your first 3 tools in `tools/`:
  - `system.open_app("chrome")`
  - `web.search("...")`
  - `system.get_time()`
- Teach the model the tools exist (function-calling / JSON tool schema).

**Done when:** you type "open notepad and tell me the time" and it actually does both.

---

## Phase 3 — The Browser Agent: "do anything on the web" (3–5 days) ⭐ YOUR BIG UNLOCK
**Goal:** the YouTube/login/multi-step stuff you actually want.

- Build `tools/browser.py` with Playwright:
  - open a site, type into fields, click, read the page, scroll, go to a video timestamp
- Use a **persistent browser profile** so logins stick.
- Wire it into the agent loop so the brain can chain steps.

**Done when:** "open YouTube, search lo-fi beats, play the first video, skip 30s ahead"
works end to end, by typing.

---

## Phase 4 — Add the Voice (2–3 days)
**Goal:** talk to it and hear it — wrap the working brain in voice.

- `ears/stt.py` — faster-whisper turns your speech into text.
- `voice/tts.py` — Piper speaks the replies.
- Add microphone capture + "stopped talking" detection.

**Done when:** you *speak* a command and *hear* the reply, no typing.

---

## Phase 5 — Wake Word + Always-On (1–2 days)
**Goal:** hands-free "Hey Jarvis," running quietly in the background.

- `ears/wakeword.py` — openWakeWord's pre-made `hey_jarvis` model.
- Make it run as a background process / start with Windows.

**Done when:** you say "Hey Jarvis" across the room and it wakes up and listens.

---

## Phase 6 — Memory, Credentials & Safety (2–3 days)
**Goal:** it remembers you, can log in for you, and won't do anything catastrophic.

- `memory/store.py` — SQLite for conversation + long-term facts.
- `memory/vault.py` — store your logins in Windows Credential Manager via `keyring`.
- `safety.py` — confirm before irreversible actions (delete, send, buy, post).

**Done when:** it logs into a site using stored creds, remembers a fact you told it
yesterday, and asks "are you sure?" before deleting anything.

---

## Phase 7 — Grow Skills Forever (ongoing)
**Goal:** keep adding `tools/` — each new file = a new superpower.

Ideas, in rough difficulty order:
- Spotify / media control · weather · news · reminders & alarms
- Gmail / Calendar (Google APIs) · WhatsApp Web automation
- File search & organization · screenshots & screen reading (OCR)
- Smart-home (Home Assistant) · system stats · app macros
- **Advanced:** vision-based clicking (Moondream) for apps with no API
- **Advanced:** fine-tune a custom personality (free Colab + Unsloth)

**Done when:** never — this is the fun part you do forever.

---

## Suggested pace
Weekends only? Phases 1–3 in ~3–4 weekends gets you a *typing* JARVIS that controls
your browser and PC — the genuinely impressive milestone. Voice (Phases 4–5) is a
satisfying weekend on top. Everything after is gravy.

## Cost across all phases: ₹0. See [BUDGET.md](BUDGET.md).
