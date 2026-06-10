# JARVIS — The Model Router

The router is JARVIS's "resource manager": every time the brain needs to think, the
router decides **which model answers** — a fast/smart free cloud model when I'm online,
my local Ollama model when I'm not. It load-balances across a pool of free API keys and
fails over the instant one is rate-limited, out of quota, or down — so I never see an error.

With **no keys configured it just uses local Ollama**, exactly like before. Add keys and
the cloud brains switch on automatically. Set `ROUTER_ENABLED = False` in `config.py` to
force 100% local/private.

---

## How it routes

1. Walk the providers in `config.PROVIDER_PRIORITY` — by default `gemini → groq → openrouter → local`.
2. For a cloud provider, pick the **least-used healthy key** from its pool (load-balancing + round-robin).
3. Call it. On success → done.
4. On trouble, **bench that key** and try the next key, then the next provider:
   | Problem | What happens | Cooldown |
   |---|---|---|
   | Per-minute rate limit | bench key, try next | `COOLDOWN_RATE_LIMIT` (60s) |
   | Daily / quota used up | bench key, try next | `COOLDOWN_QUOTA` (1h) |
   | Bad / blocked key | park key | `COOLDOWN_AUTH` (24h) |
   | 5xx / timeout | bench briefly, try next | 15s |
   | No internet | skip all cloud, use local | `COOLDOWN_OFFLINE` (30s) |
5. **Recovery is automatic** — a benched key's cooldown simply expires and it rejoins the
   pool the next time it's picked (no background threads, nothing to restart).
6. `local` is always last in the list, so there's always a brain that answers.

---

## Task-based key routing

Every Gemini free key has its own quota. If all tasks shared one pool, a heavy session
(say lots of browsing) could burn the quota that coding or research needs. So each **task
route** prefers its **own** Gemini key:

| Route | Used by | 
|---|---|
| `conversation` | everyday chat (general agent) |
| `planning` | the orchestrator's planning + aggregation (reasoning) |
| `research` | the research agent |
| `coding` | the software agent |
| `data` | the data agent (incl. document analysis) |
| `browser` | the browser agent (web/Chrome/YouTube/WhatsApp) |
| `system` | the system agent (apps, power, system info) |

Routes are handed to your Gemini keys in the order above (`config.ROUTES`). With **fewer keys
than routes** it wraps around (round-robin), so every key still pulls weight; add more keys for
finer isolation. Pin a route to a specific key with `GEMINI_ROUTE_KEYS` (e.g. `{"coding": 2}`).

**Per-route fallback chain:** assigned Gemini key → *(spill)* the rest of your Gemini keys →
Groq → OpenRouter → local. The spill step (`GEMINI_SPILL_TO_POOL = True`) squeezes the most out
of the free tier; set it `False` for strict isolation (assigned key → Groq → local), walling
off each category's quota. Parallel same-route steps share the route's key (gemini handles
concurrency); when it's exhausted they spill/fail over automatically.

With **zero keys** this whole layer is inert — everything routes to local, as before.

---

## Get your FREE keys (₹0)

All three have genuinely free tiers. Grab one or several from each — **more keys = more
headroom**, because the router spreads load across them and fails over between them.

| Provider | Get a key | Free tier (approx.) | Notes |
|---|---|---|---|
| **Gemini** | <https://aistudio.google.com/apikey> | generous daily limit | Smart, multimodal, priority 1 |
| **Groq** | <https://console.groq.com/keys> | high RPM, free | Stupidly **fast**, priority 2 |
| **OpenRouter** | <https://openrouter.ai/keys> | free `…:free` models | Lots of model choice, priority 3 |

You can make **multiple keys per provider** (e.g. a few Google accounts) — that's the whole
point of the pool. Free tiers reset, so when one key hits its cap the router quietly moves to
the next and comes back to the first later.

---

## Add the keys

**Option A — `keys.json` (simplest):** copy the template and paste your keys.
```powershell
copy keys.example.json keys.json
notepad keys.json
```
```json
{
  "gemini": ["AIza...key1", "AIza...key2"],
  "groq": ["gsk_...key1"],
  "openrouter": ["sk-or-...key1"]
}
```
`keys.json` is **git-ignored** — it never gets committed or pushed. Leave a provider's list
empty (or drop the line) to skip it.

**Option B — environment variables** (numbered, as many as you have):
```powershell
$env:GEMINI_KEY_1 = "AIza...";  $env:GEMINI_KEY_2 = "AIza..."
$env:GROQ_KEY_1   = "gsk_..."
```

Keys from both sources are merged and de-duplicated.

---

## Pick the models

In `config.py → PROVIDER_MODELS`. The defaults are free-tier picks; swap any of them:
```python
PROVIDER_MODELS = {
    "gemini": "gemini-2.0-flash",
    "groq": "llama-3.3-70b-versatile",
    "openrouter": "meta-llama/llama-3.3-70b-instruct:free",
    "local": MODEL,   # your Ollama model
}
```
If a model name is wrong for your account, that provider just errors and the router fails over
— check the provider's model list and update the name.

---

## Watch it work

`ROUTER_VERBOSE = True` (default) prints one line to stderr per decision, e.g.:
```
[router] served by groq#1 (180ms)
[router] gemini#1 rate-limited → benched, trying next
[router] gemini unreachable (offline) → falling back to local
```
For a programmatic view (used later by the dashboard):
```python
from brain.router import get_router
print(get_router().stats())   # per-key requests, errors, latency, cooldowns, recent routes
```

---

## Status & honesty

- **Tested live:** the routing logic (rotation, key + provider failover, offline→local) and
  the **local Ollama** path, end to end — see `test_router.py`.
- **Needs a live key to verify:** the Gemini / Groq / OpenRouter request formats. They're
  built to each provider's spec, but I can't confirm them without a key on the account. If a
  cloud provider misbehaves on the first real call, the router **fails over** to the next one
  (that's the safety net) and the fix is a small tweak in `brain/providers.py`.
- **Privacy:** cloud requests leave the laptop by definition. Anything you want kept fully
  private, keep on `local` (or flip `ROUTER_ENABLED = False`). A per-task "force local for
  sensitive things" switch is a planned follow-up.

---

## The pieces

```
brain/keystore.py    the multi-key pool: load, least-used pick, bench/recover, health snapshot
brain/providers.py   adapters that translate one canonical request to each API and back
brain/router.py      the priority walk + failover + offline detection (the entry point: chat())
```

`brain/llm.py` and `brain/agent.py` both call `brain.router.chat(...)`, so every thought —
plain chat or tool-calling — flows through the router.
