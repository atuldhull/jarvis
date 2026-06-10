"""Long-term memory — SQLite for facts + semantic memories.

Short-term memory is the running message list inside the Agent. This is the
*persistent* layer: durable facts about the user, recalled by MEANING via local
embeddings (memory/embed.py) with a keyword fallback when embeddings are
unavailable. Use the process-wide `get_memory()` singleton so every caller shares
ONE connection + lock (the orchestrator captures on a background thread while the
main thread reads).
"""

import json
import sqlite3
import threading
import time

import config
from memory.embed import embed, cosine


class Memory:
    def __init__(self, path: str = None):
        self.db = sqlite3.connect(path or config.MEMORY_DB, check_same_thread=False, timeout=10)
        self._lock = threading.Lock()
        with self._lock:
            self.db.execute("PRAGMA journal_mode=WAL")    # reader + one writer concurrently
            self.db.execute("PRAGMA busy_timeout=5000")   # wait-and-retry instead of failing
            self.db.execute(
                "CREATE TABLE IF NOT EXISTS facts (key TEXT PRIMARY KEY, value TEXT, ts REAL)")
            self.db.execute(
                "CREATE TABLE IF NOT EXISTS turns ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT, content TEXT, ts REAL)")
            self.db.execute(
                "CREATE TABLE IF NOT EXISTS memories ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, text TEXT, kind TEXT, "
                "embedding TEXT, ts REAL)")
            self.db.commit()

    # ── explicit key/value facts (the remember/recall tools) ─────────────────
    def remember(self, key: str, value: str) -> str:
        with self._lock:
            self.db.execute(
                "INSERT INTO facts(key, value, ts) VALUES(?,?,?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value, ts=excluded.ts",
                (key, value, time.time()))
            # Supersede any prior mirror of this key so a stale value can't linger.
            self.db.execute("DELETE FROM memories WHERE kind='fact' AND text LIKE ?", (key + ": %",))
            self.db.commit()
        # Mirror the current value into semantic memory so it's recallable by meaning.
        self.add_memory(f"{key}: {value}", kind="fact")
        return f"Noted, sir — {key}: {value}."

    def recall(self, key: str):
        with self._lock:
            row = self.db.execute("SELECT value FROM facts WHERE key=?", (key,)).fetchone()
        return row[0] if row else None

    def all_facts(self) -> dict:
        with self._lock:
            return dict(self.db.execute("SELECT key, value FROM facts").fetchall())

    # ── semantic memories ────────────────────────────────────────────────────
    def add_memory(self, text: str, kind: str = "fact"):
        """Store a durable memory (skipping near-duplicates). Returns its id."""
        text = (text or "").strip()
        if not text:
            return None
        vec = embed(text)  # network call BEFORE the lock, never under it
        with self._lock:  # dedup-check and insert are atomic (no TOCTOU window)
            rows = self.db.execute("SELECT id, text, embedding FROM memories").fetchall()
            if vec is not None:
                for mid, _t, emb in rows:
                    if emb and cosine(vec, json.loads(emb)) >= getattr(config, "MEMORY_DEDUP_SIM", 0.9):
                        return mid  # already know this
            else:
                for mid, t, _emb in rows:
                    if t == text:
                        return mid
            cur = self.db.execute(
                "INSERT INTO memories(text, kind, embedding, ts) VALUES(?,?,?,?)",
                (text, kind, json.dumps(vec) if vec else None, time.time()))
            self.db.commit()
            return cur.lastrowid

    def search(self, query: str, k: int = 4, min_sim: float = None):
        """Top-k memories relevant to `query` — semantic if possible, else keyword.

        Newer memories win ties (so an updated fact outranks a stale one), and
        memories stored while embeddings were down are still surfaced by keyword.
        """
        query = (query or "").strip()
        if not query:
            return []
        if min_sim is None:
            min_sim = getattr(config, "MEMORY_MIN_SIM", 0.35)
        with self._lock:
            rows = self.db.execute("SELECT text, embedding, ts FROM memories").fetchall()
        if not rows:
            return []
        words = [w for w in query.lower().split() if len(w) > 2]
        qvec = embed(query)
        if qvec is not None and any(emb for _t, emb, _ts in rows):
            scored = [(cosine(qvec, json.loads(emb)), ts, t) for t, emb, ts in rows if emb]
            scored.sort(key=lambda x: (x[0], x[1]), reverse=True)  # similarity, then recency
            out = [t for s, _ts, t in scored[:k] if s >= min_sim]
            # Also surface vectorless rows (captured during an embeddings outage) by keyword.
            for t, emb, _ts in rows:
                if not emb and t not in out and any(w in t.lower() for w in words):
                    out.append(t)
            return out[:k]
        # Keyword fallback (no query vector or no vectorized rows): newest matches first.
        hits = sorted(((ts, t) for t, _emb, ts in rows if any(w in t.lower() for w in words)),
                      reverse=True)
        return [t for _ts, t in hits[:k]]

    def memories(self):
        with self._lock:
            return self.db.execute("SELECT text, kind FROM memories ORDER BY ts").fetchall()

    def log_turn(self, role: str, content: str):
        with self._lock:
            self.db.execute("INSERT INTO turns(role, content, ts) VALUES(?,?,?)",
                            (role, content, time.time()))
            self.db.commit()

    def close(self):
        with self._lock:
            self.db.close()


_shared = None


def get_memory() -> Memory:
    """The process-wide memory store — one connection + lock shared by all callers."""
    global _shared
    if _shared is None:
        _shared = Memory()
    return _shared
