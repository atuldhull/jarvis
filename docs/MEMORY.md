# JARVIS — Long-Term Memory

JARVIS remembers durable facts about you and recalls them **by meaning**, not just by
exact keys — so it genuinely "remembers you" across restarts, without you having to ask it
to memorize anything.

```
you talk  ──▶  recall: pull the few relevant memories into this turn's context
          ──▶  reply (now memory-aware)
          ──▶  capture (background): extract durable facts, store them for next time
```

Everything is **local and free**: embeddings come from a local Ollama model, memories live
in the same SQLite file as before. If embeddings aren't available it degrades to keyword
search — still works, just coarser.

---

## How it works

- **Semantic store** ([memory/store.py](../memory/store.py)) — a `memories` table holds each
  fact's text + an embedding vector. Search embeds your query and ranks memories by cosine
  similarity (so *"what graphics card do I have"* finds *"the user's GPU is an RTX 4050"*
  even with no shared words). Near-duplicates are skipped on insert.
- **Embeddings** ([memory/embed.py](../memory/embed.py)) — local Ollama (`nomic-embed-text`).
  Returns `None` if unavailable → the store falls back to keyword matching automatically.
- **Auto-recall** — every turn, the orchestrator pulls the top-K relevant memories and
  injects them into the assistant's context as a single, refreshed note (it never piles up
  in the chat log). The model uses them naturally; it doesn't recite them.
- **Auto-capture** ([memory/manager.py](../memory/manager.py)) — after each reply, a
  **background thread** asks the model to extract durable facts (name, preferences, projects,
  people…) and stores them. It's best-effort and never blocks or slows your reply.
- **Explicit tools** — `remember_fact` / `recall_fact` (exact key) and `search_memory`
  (by meaning) are still available to every agent. Explicit facts are also mirrored into
  semantic memory.

The `memory` task route gets its own Gemini key (capture runs on it), so background
remembering never eats the quota your live conversation needs.

---

## Config ([config.py](../config.py))

| Setting | Meaning |
|---|---|
| `MEMORY_ENABLED` | master switch |
| `EMBED_MODEL` | local embedding model (`ollama pull nomic-embed-text`) |
| `MEMORY_RECALL_K` | how many memories to surface per turn (default 4) |
| `MEMORY_CAPTURE` | auto-extract facts in the background |
| `MEMORY_MIN_SIM` | ignore recalled memories below this similarity (0–1) |
| `MEMORY_DEDUP_SIM` | treat a new fact this similar to an existing one as a duplicate |

Memories persist in `jarvis.db` (git-ignored). Delete that file to wipe everything JARVIS
knows about you.

---

## Setup

```powershell
ollama pull nomic-embed-text   # one-time, ~270 MB — enables semantic recall
```
That's it — it's wired into `main.py` already. Verified by [test_memory.py](../test_memory.py)
(semantic search, dedup, recall, capture) plus a live cross-session recall test.

---

## The pieces

```
memory/store.py     SQLite: facts + semantic memories (thread-safe, keyword fallback)
memory/embed.py     local Ollama embeddings + cosine similarity
memory/manager.py   recall_context (inject) + capture_async (background fact extraction)
```
