"""Dependency-free check of Ollama + the model + tool-calling (stdlib only).

Talks to the local Ollama HTTP API directly with urllib, so it works even before
`pip install ollama`. Confirms: the server is up, config.MODEL responds, and it
emits a tool_call when given a tool.

Run:  py test_raw_ollama.py
"""

import json
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

import config

HOST = config.OLLAMA_HOST


def chat(messages, tools=None):
    body = {"model": config.MODEL, "messages": messages, "stream": False,
            "options": {"temperature": config.TEMPERATURE}}
    if tools:
        body["tools"] = tools
    req = urllib.request.Request(
        HOST + "/api/chat",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read())


def main():
    print("=== PLAIN CHAT ===")
    r = chat([{"role": "user", "content": "Say hello in one short sentence."}])
    print("reply:", r["message"]["content"])

    print("\n=== TOOL-CALLING ===")
    tools = [{
        "type": "function",
        "function": {
            "name": "get_time",
            "description": "Get the current local date and time.",
            "parameters": {"type": "object", "properties": {}},
        },
    }]
    r = chat([{"role": "user", "content": "What time is it right now? Use your tool."}], tools=tools)
    msg = r["message"]
    calls = msg.get("tool_calls")
    if calls:
        print("tool_calls:", json.dumps(calls, indent=2))
        print("RESULT: model correctly requested a tool ✅")
    else:
        print("no tool_calls; content:", msg.get("content"))
        print("RESULT: model did NOT call the tool ⚠️")


if __name__ == "__main__":
    main()
