"""Check qwen3.5:4b: plain chat + tool-calling (the Qwen3.5 parser can be buggy on old Ollama)."""

import json
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

HOST = "http://localhost:11434"
MODEL = "qwen3.5:4b"


def chat(messages, tools=None):
    body = {"model": MODEL, "messages": messages, "stream": False, "options": {"temperature": 0.6}}
    if tools:
        body["tools"] = tools
    req = urllib.request.Request(
        HOST + "/api/chat", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read())["message"]


print("PLAIN:", chat([{"role": "user", "content": "Say hello in one short sentence."}]).get("content"))

tools = [{"type": "function", "function": {
    "name": "get_time", "description": "Get the current local date and time.",
    "parameters": {"type": "object", "properties": {}}}}]
m = chat([{"role": "user", "content": "What time is it right now? Use your tool."}], tools=tools)
calls = m.get("tool_calls")
if calls:
    print("TOOL-CALLING WORKS ✅", json.dumps(calls))
else:
    print("NO TOOL CALL ⚠️ (content:", repr(m.get("content"))[:200], ") — Ollama may need updating")
