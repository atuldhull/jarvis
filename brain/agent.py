"""The agent loop: plan → act → observe → repeat.

One `Agent` runs the loop: it hands the model a menu of tools, and if the model
calls one, we run it, feed the result back, and let the model continue — until it
produces a normal reply. This is the heart of "JARVIS that *does* things."

The same class powers both the everyday assistant AND each specialist "department"
in the orchestrator: pass a custom `system_prompt` and a `tools` subset to scope an
agent to one job (research, coding, …). With no arguments it's the general
assistant with the full toolset, exactly as before.
"""

import json

import config
import safety
from brain.router import chat  # routed across cloud + local brains (falls back to local)
from tools import schemas, dispatch, needs_confirm


class Agent:
    def __init__(self, model: str = config.MODEL, system_prompt: str = None,
                 tools: list = None, name: str = "general", route: str = "conversation"):
        self.name = name
        self.route = route  # task category → its dedicated Gemini key in the router
        # The router picks the model per call (from config.PROVIDER_MODELS); `model`
        # is kept for compatibility but does not select the brain.
        self.model = model
        self.tool_names = tools  # None = the full tool menu; a list = just those tools
        self._ctx_idx = None  # index of the refreshable memory-context system message
        prompt = system_prompt or config.PERSONA
        self.messages = [{"role": "system", "content": prompt + "\n\n" + config.TOOL_GUIDANCE}]

    def set_memory_context(self, text: str):
        """Keep ONE refreshed memory note right after the persona (not in the chat log)."""
        if not text:
            return
        note = {"role": "system", "content": text}
        if self._ctx_idx is None:
            self.messages.insert(1, note)
            self._ctx_idx = 1
        else:
            self.messages[self._ctx_idx] = note

    def _trim(self):
        """Bound history so a long session can't overflow the context window and evict
        the persona/memory note. Keeps the leading system messages + the most recent turns."""
        cap = getattr(config, "MAX_HISTORY_MESSAGES", 30)
        if len(self.messages) <= cap:
            return
        n_sys = 0
        while n_sys < len(self.messages) and self.messages[n_sys]["role"] == "system":
            n_sys += 1
        tail = self.messages[n_sys:][-(cap - n_sys):]
        while tail and tail[0]["role"] == "tool":  # never start the tail with an orphan tool result
            tail = tail[1:]
        self.messages = self.messages[:n_sys] + tail

    def run(self, user_text: str, max_steps: int = 6) -> str:
        """Handle one request, taking tool actions as needed; return the final reply."""
        self.messages.append({"role": "user", "content": user_text})
        self._trim()

        for _ in range(max_steps):
            message = chat(
                self.messages,
                tools=schemas(only=self.tool_names),  # only this department's tools
                options={"temperature": config.TEMPERATURE},
                route=self.route,  # this department's dedicated Gemini key
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
                    try:
                        args = json.loads(args or "{}")
                    except Exception:
                        args = {}
                args = dict(args) if isinstance(args, dict) else {}  # tolerate null/odd args

                if self.tool_names is not None and name not in self.tool_names:
                    # The model reached for a tool outside this department's scope.
                    result = f"({name} isn't available to the {self.name} department)"
                elif needs_confirm(name) and not safety.confirm(name, args, self.name):
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
        self._ctx_idx = None
