"""Long-term memory — a tiny SQLite store for facts and conversation history.

Short-term memory is just the running message list inside the Agent. This is the
*persistent* layer: facts JARVIS should keep across restarts ("my name is…", "my
city is…") and a log of past turns. Upgrade to a vector database (Chroma) later
for fuzzy recall; plain SQLite is plenty to begin with.
"""

import sqlite3
import time

import config


class Memory:
    def __init__(self, path: str = None):
        self.db = sqlite3.connect(path or config.MEMORY_DB)
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS facts (key TEXT PRIMARY KEY, value TEXT, ts REAL)"
        )
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS turns ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT, content TEXT, ts REAL)"
        )
        self.db.commit()

    def remember(self, key: str, value: str) -> str:
        self.db.execute(
            "INSERT INTO facts(key, value, ts) VALUES(?,?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value, ts=excluded.ts",
            (key, value, time.time()),
        )
        self.db.commit()
        return f"Noted, sir — {key}: {value}."

    def recall(self, key: str):
        row = self.db.execute("SELECT value FROM facts WHERE key=?", (key,)).fetchone()
        return row[0] if row else None

    def all_facts(self) -> dict:
        return dict(self.db.execute("SELECT key, value FROM facts").fetchall())

    def log_turn(self, role: str, content: str):
        self.db.execute(
            "INSERT INTO turns(role, content, ts) VALUES(?,?,?)",
            (role, content, time.time()),
        )
        self.db.commit()

    def close(self):
        self.db.close()
