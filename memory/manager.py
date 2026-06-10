"""Memory manager — surfaces relevant memories into context, captures new ones.

Two jobs, both invisible to the user:
  * recall_context(user_text): pull the few memories relevant to this turn so the
    assistant naturally "remembers" the user.
  * capture_async(user_text, reply): after a turn, extract durable facts worth
    keeping — on a BACKGROUND thread, so it never adds latency to the reply.
"""

import threading

import config
from brain.router import chat
from brain.jsonutil import extract_json
from memory.store import get_memory


CAPTURE_PROMPT = """You extract durable, long-term facts about the USER from one conversation turn — things worth remembering for months: their name, location, job/role, preferences and dislikes, people/pets, ongoing projects, important decisions, recurring needs. IGNORE transient or trivial chit-chat, one-off task details, and anything about the assistant itself.

Return STRICT JSON only, no prose, no markdown:
{"facts": ["The user's name is Atul.", "The user is building a local AI assistant called JARVIS."]}
Each fact is a short, standalone sentence in the third person. Return {"facts": []} if there is nothing worth keeping."""


class MemoryManager:
    def __init__(self):
        self.store = get_memory()
        self._capture_lock = threading.Lock()

    def recall_context(self, user_text: str) -> str:
        """A short note of relevant memories to inject into the turn (or '')."""
        if not getattr(config, "MEMORY_ENABLED", True):
            return ""
        hits = self.store.search(user_text, k=getattr(config, "MEMORY_RECALL_K", 4))
        if not hits:
            return ""
        bullets = "\n".join(f"- {h}" for h in hits)
        return ("What you remember about the user (use it naturally when relevant; "
                "never recite it as a list):\n" + bullets)

    def capture_async(self, user_text: str, reply: str):
        """Kick off fact extraction in the background (non-blocking)."""
        if not getattr(config, "MEMORY_CAPTURE", True):
            return
        if len(user_text.split()) < 3:
            return  # trivial one-liners rarely carry durable facts
        threading.Thread(target=self._capture, args=(user_text, reply), daemon=True).start()

    def _capture(self, user_text: str, reply: str):
        if not self._capture_lock.acquire(blocking=False):
            return  # a capture is already in flight — skip to avoid pile-up
        try:
            msg = chat(
                [{"role": "system", "content": CAPTURE_PROMPT},
                 {"role": "user", "content": f"USER: {user_text}\nASSISTANT: {reply}"}],
                options={"temperature": 0.0}, route="memory")
            for fact in self._parse(msg.get("content") or ""):
                self.store.add_memory(fact, kind="auto")
        except Exception:
            pass  # memory is best-effort; never break the main turn
        finally:
            self._capture_lock.release()

    @staticmethod
    def _parse(text: str):
        data = extract_json(text) or {}
        facts = data.get("facts", []) if isinstance(data, dict) else []
        return [f.strip() for f in facts if isinstance(f, str) and f.strip()][:5]
