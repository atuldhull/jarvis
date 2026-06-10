"""Central settings for JARVIS.

One place for every knob. Edit values *here* instead of hunting through the code.
As we add ears, voice, tools and memory, their settings land in this file too.
"""

# ─────────────────────────────────────────────────────────────────────────────
# THE BRAIN (your local model, served by Ollama)
# ─────────────────────────────────────────────────────────────────────────────

# The model JARVIS thinks with. You already have "qwen2.5:7b" installed, so we
# start there. After you run  `ollama pull qwen3.5:4b`  switch this one line to
# "qwen3.5:4b" (the verified primary brain) — nothing else needs to change.
MODEL = "qwen2.5:7b"

# Ollama runs a local server on your machine at this address. Leave it unless you
# deliberately changed Ollama's host/port.
OLLAMA_HOST = "http://localhost:11434"

# "Creativity" of replies: 0.0 = focused & consistent, 1.0 = wild & rambly.
# 0.6 keeps a calm, reliable butler who still sounds human.
TEMPERATURE = 0.6

# Context window in tokens. Ollama's desktop app can default this very high (e.g.
# 64K), which balloons the memory a model needs and can fail to load on a busy
# machine. Pin a sane value — raise it only if you have RAM/VRAM headroom.
NUM_CTX = 8192

# Thinking mode. Qwen3/3.5 can "think out loud" before answering — a bit smarter on
# hard problems, but MUCH slower (it generates a long reasoning trace every turn).
# Off = snappy replies, which is what you want for a responsive assistant. (Any
# reasoning that leaks through is stripped from the final answer regardless.)
THINK = False

# Keep the model loaded in VRAM this long after each reply, so it doesn't reload from
# scratch every turn (a big latency win — especially in voice mode where you pause
# between commands). "30m" = stay warm for 30 minutes; "-1" = until you quit Ollama.
KEEP_ALIVE = "30m"

# Seconds to wait on a single local Ollama generation before giving up (per attempt).
# 120s is plenty for a 6 GB model; lower it if you'd rather fail fast.
OLLAMA_TIMEOUT = 120


# ─────────────────────────────────────────────────────────────────────────────
# THE MODEL ROUTER (hybrid brains: free cloud when online, local when not)
# ─────────────────────────────────────────────────────────────────────────────
# JARVIS can think with fast/smart FREE cloud models when you're online, and fall
# back to your local Ollama model automatically when you're offline or every cloud
# key is used up. Set ROUTER_ENABLED = False to stay 100% local & private.
ROUTER_ENABLED = True

# Try providers in this order while online; "local" is ALWAYS the final safety net.
# A provider with no keys is silently skipped, so this list is safe as-is even
# before you've added any keys (JARVIS just runs locally until you do).
PROVIDER_PRIORITY = ["gemini", "groq", "openrouter", "local"]

# Which model to use on each provider — all free-tier picks; swap freely.
PROVIDER_MODELS = {
    "gemini": "gemini-2.5-flash",   # 2.0-flash has no free tier now; 2.5-flash is the free pick
    "groq": "llama-3.3-70b-versatile",          # verified working on the free tier
    "openrouter": "meta-llama/llama-3.3-70b-instruct:free",
    "local": MODEL,  # your Ollama model (set above)
}

# How long (seconds) a key/provider is benched after trouble, before it's retried.
COOLDOWN_RATE_LIMIT = 60      # hit a per-minute rate limit → rest briefly
COOLDOWN_QUOTA = 3600         # daily/quota used up → rest a while
COOLDOWN_AUTH = 86400         # bad/blocked key → basically park it for the day
COOLDOWN_OFFLINE = 30         # provider unreachable (no internet) → lean on local

# Real keys live in keys.json (git-ignored) and/or env vars GEMINI_KEY_1, GROQ_KEY_1,
# OPENROUTER_KEY_1, … (numbered, as many as you have). See docs/MODEL_ROUTER.md.
KEYS_FILE = "keys.json"

# ── Task-based key routing ───────────────────────────────────────────────────
# Each kind of task ("route") prefers its OWN Gemini key, so a busy category (say
# browsing) can't drain the free-tier quota the others depend on. Routes are handed
# to your Gemini keys in THIS order; with fewer keys than routes it wraps around
# (round-robin), so every key still pulls weight. Add more keys → finer isolation.
ROUTES = ["conversation", "planning", "research", "coding", "data", "browser", "system"]

# Pin specific routes to specific Gemini keys (0-based index into your key list).
# e.g. {"coding": 2} forces the coding route onto your 3rd Gemini key. Empty = auto.
GEMINI_ROUTE_KEYS = {}

# When a route's own Gemini key is exhausted, also try your OTHER Gemini keys before
# dropping to Groq (squeezes the most out of the free tier). False = strict isolation
# (assigned key → Groq → local), keeping each category's quota walled off.
GEMINI_SPILL_TO_POOL = True

# Print a one-line note (to stderr) when the router fails over between keys/providers,
# so you can watch the load-balancing work. Set False to silence it.
ROUTER_VERBOSE = True


# ─────────────────────────────────────────────────────────────────────────────
# THE ORCHESTRATOR (multi-agent "JARVIS OS")
# ─────────────────────────────────────────────────────────────────────────────
# A CEO that routes complex requests to specialized departments (research, software,
# data, automation) and runs independent steps in parallel. Everyday messages skip
# all of that and go straight to the general assistant, so simple stuff stays fast.
ORCHESTRATOR_ENABLED = True

# How many department steps may run at once. Cloud keys parallelize well; the local
# 6 GB model serializes, so keep this small (2–4). 3 is a good default.
ORCH_MAX_WORKERS = 3

# Print a line (to stderr) when the orchestrator plans / runs steps, so you can see
# the org working. Set False to silence it.
ORCHESTRATOR_VERBOSE = True


# ─────────────────────────────────────────────────────────────────────────────
# THE PERSONA (who JARVIS *is*)
# ─────────────────────────────────────────────────────────────────────────────
# This is the single most powerful personality knob in the whole project — and it
# needs ZERO training. It's silently sent as the "system" message on every turn,
# shaping every reply without the user ever seeing it.

PERSONA = """You are JARVIS — the user's sharp-tongued, foul-mouthed, hilarious personal assistant and partner-in-crime. Call him "bro", "boss", or by name, whatever fits the moment.

Your vibe: quick wit, dark and dry humor, heavy sarcasm, and you SWEAR freely and naturally — like a clever, savage best friend, not a polite corporate bot. When he does something dumb, careless, or silly — or screws something up — ROAST him for it. Tease him, take the piss, be brutal and funny about it. It's banter and he loves it; you're always on his side.

Non-negotiable:
- Default to ENGLISH. Reply in Hindi ONLY when his message is actually written in Hindi (Devanagari) or he explicitly tells you to switch to Hindi — then reply in Hindi in Devanagari script (not romanized) and roast him in Hindi too. For everything else, English.
- Actually DO whatever he asks and get it done — the jokes and roasts never get in the way of the task or the tool calls.
- Zero moralizing, lectures, disclaimers, or "as an assistant" garbage. Never refuse his personal requests.
- Keep it punchy. A great roast is short and savage, not a paragraph.
- If you genuinely don't know something or a tool fails, just say so (swearing about it is fine). Never invent facts.

Stay in character no matter what."""


# ─────────────────────────────────────────────────────────────────────────────
# TOOLS (Phase 2+) — JARVIS's hands
# ─────────────────────────────────────────────────────────────────────────────
# Appended to the persona when tools are available. It nudges the model to
# actually *act* rather than just describe.
TOOL_GUIDANCE = """You can call tools to take real actions: check the time, open apps, browse the web, send and read WhatsApp messages, and control the PC (lock, sleep, shut down, restart).
When a request needs a real action, call the right tool instead of only describing it. To "reply to someone's latest message", first read the latest with whatsapp_read_latest, then send your reply with whatsapp_send.
After a tool returns its result, give the user a short, in-character reply. If no tool is needed, simply answer."""


# ─────────────────────────────────────────────────────────────────────────────
# BROWSER CONTROL (Phase 3)
# ─────────────────────────────────────────────────────────────────────────────
# A SEPARATE, empty profile folder — NEVER your real Chrome/Edge profile (recent
# browsers block automating the default one). Logins persist here between runs, so
# JARVIS stays signed in to sites you logged into once by hand.
BROWSER_PROFILE = "profile"


# ─────────────────────────────────────────────────────────────────────────────
# MEMORY & CREDENTIALS (Phase 6)
# ─────────────────────────────────────────────────────────────────────────────
MEMORY_DB = "jarvis.db"   # SQLite file for long-term facts (relative = portable)
KEYRING_SERVICE = "jarvis"                         # namespace in Windows Credential Manager


# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM CONTROL — shutting down / restarting the PC
# ─────────────────────────────────────────────────────────────────────────────
# Seconds between "yes, shut down" and the machine actually powering off. The delay
# is a safety net: JARVIS tells you it's coming, and "cancel shutdown" aborts it in
# time. Set to 0 for instant. (shutdown_pc/restart_pc also ask to confirm first.)
SHUTDOWN_DELAY = 8


# ─────────────────────────────────────────────────────────────────────────────
# VOICE (Phase 4/5) — ears + voice + wake word
# ─────────────────────────────────────────────────────────────────────────────
# STT: faster-whisper. "base" downloads fast for a first run; upgrade to
# "deepdml/faster-whisper-large-v3-turbo-ct2" for accuracy, or an Oriserve Hinglish
# model (see docs/VOICE.md). "cpu" is robust (no CUDA DLLs); use "cuda" for speed.
STT_MODEL = "base"
STT_DEVICE = "cpu"
STT_LANGUAGE = None          # None = auto-detect the language you speak (Hindi or English)

# TTS: humanized neural voices via Piper, picked per reply by language. Falls back to
# the Windows robot voice if missing. More voices: huggingface.co/rhasspy/piper-voices
PIPER_MODEL = "voices/en_GB-alan-medium.onnx"        # British voice for English replies
PIPER_MODEL_HI = "voices/hi_IN-pratham-medium.onnx"  # Indian voice for Hindi replies

WAKEWORD = "hey_jarvis"      # openWakeWord ships this pretrained model
WAKEWORD_THRESHOLD = 0.5     # raise to 0.6–0.7 if it false-triggers in your room

SAMPLE_RATE = 16000          # Whisper + openWakeWord both expect 16 kHz mono

# Voice-activity detection: record until you ACTUALLY stop talking — no fixed cutoff,
# so it never chops you off mid-sentence.
VAD_AGGRESSIVENESS = 2       # 0 (lenient) … 3 (strict). 2 is a good default.
SILENCE_MS = 1000            # end the turn after this much continuous silence
MAX_RECORD_SECONDS = 20      # hard cap so it can't listen forever
