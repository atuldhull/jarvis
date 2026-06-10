"""The agent loop: plan → act → observe → repeat.

Where Brain.think() just chats, the Agent hands the model a menu of tools. If the
model decides to call one, we run it, feed the result back, and let the model
continue — looping until it produces a normal reply for the user. This loop is the
heart of "JARVIS that *does* things."
"""

import json

import config
import safety
from brain.router import chat  # routed across cloud + local brains (falls back to local)
from tools import schemas, dispatch, needs_confirm


class Agent:
    def __init__(self, model: str = config.MODEL):
        self.model = model
        self.messages = [
            {"role": "system", "content": config.PERSONA + "\n\n" + config.TOOL_GUIDANCE}
        ]

    def run(self, user_text: str, max_steps: int = 6) -> str:
        """Handle one user request, taking tool actions as needed."""
        self.messages.append({"role": "user", "content": user_text})

        for _ in range(max_steps):
            message = chat(
                self.messages,
                tools=schemas(),
                options={"temperature": config.TEMPERATURE},
            )
            self.messages.append(message)  # remember what the model said/decided

            tool_calls = message.get("tool_calls")
            if not tool_calls:
                # No tool wanted → this is the final reply for the user.
                return (message.get("content") or "").strip()

            # Run each tool the model asked for, and feed the results back.
            for call in tool_calls:
                name = call["function"]["name"]
                args = call["function"]["arguments"]
                if isinstance(args, str):
                    args = json.loads(args or "{}")
                args = dict(args)

                if needs_confirm(name) and not safety.confirm(name, args):
                    result = "(action cancelled by the user)"
                else:
                    try:
                        result = dispatch(name, args)
                    except Exception as e:
                        result = f"(tool error: {e})"

                # Canonical tool result: tool_call_id (for OpenAI-style providers)
                # and name (for Gemini/Ollama) so the loop works on any brain.
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": call.get("id", ""),
                    "name": name,
                    "content": str(result),
                })

        return "I appear to be going in circles, sir — perhaps a simpler request?"

    def reset(self):
        """Forget the conversation, keep the persona + tool guidance."""
        self.messages = self.messages[:1]
