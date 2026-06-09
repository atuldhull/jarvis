"""The Brain — a thin, friendly wrapper around Ollama.

It does just two jobs for now:
  1. Hold the running conversation, so JARVIS remembers what was just said.
  2. Send that conversation to your local model and hand back the reply.

Everything else (voice in, voice out, tools, memory) bolts on around this one
class later — they all flow through `think()`. Keep this the single doorway to
the model and the rest of the project stays simple.
"""

import config
from brain.ollama_client import chat


class Brain:
    def __init__(self, model: str = config.MODEL):
        self.model = model
        # The conversation so far. We seed it with the persona as a "system"
        # message — that's what makes the model talk like JARVIS.
        self.messages = [{"role": "system", "content": config.PERSONA}]

    def think(self, user_text: str) -> str:
        """Take what the user said; return what JARVIS says back."""
        # 1. Remember what the user said.
        self.messages.append({"role": "user", "content": user_text})

        # 2. Ask the local model, giving it the whole conversation for context.
        message = chat(self.model, self.messages, options={"temperature": config.TEMPERATURE})
        reply = (message.get("content") or "").strip()

        # 3. Remember JARVIS's own reply too, so the next turn has memory.
        self.messages.append({"role": "assistant", "content": reply})
        return reply

    def reset(self):
        """Forget the conversation but keep the persona — a clean slate."""
        self.messages = [{"role": "system", "content": config.PERSONA}]
