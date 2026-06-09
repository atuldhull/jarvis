"""Minimal Ollama client over the local HTTP API — Python stdlib only.

The official `ollama` pip package is just a thin wrapper around this same HTTP
endpoint. Talking to it with urllib keeps the brain dependency-free, so JARVIS
runs on a fresh machine the moment Ollama itself is installed — no extra pip step.
"""

import json
import re
import time
import urllib.error
import urllib.request

import config


def _clean(message):
    """Strip a thinking model's <think>…</think> block so only the answer remains."""
    if message.get("content"):
        message["content"] = re.sub(
            r"<think>.*?</think>", "", message["content"], flags=re.DOTALL
        ).strip()
    return message


def chat(model, messages, tools=None, options=None, attempts=2):
    """Send one chat request to Ollama; return the assistant message dict.

    The returned dict looks like:
        {"role": "assistant", "content": "...", "tool_calls": [ ... ]}
    (tool_calls is only present when the model decides to call a tool.)

    On a 6 GB GPU, Ollama can briefly return a 500 while swapping models in/out of
    VRAM, so we retry once after a short pause before giving up.
    """
    opts = {"num_ctx": config.NUM_CTX}
    if options:
        opts.update(options)
    body = {"model": model, "messages": messages, "stream": False, "options": opts,
            "keep_alive": getattr(config, "KEEP_ALIVE", "5m")}
    if not getattr(config, "THINK", True):
        body["think"] = False  # Ollama's proper switch to stop the model "thinking out loud"
    if tools:
        body["tools"] = tools

    req = urllib.request.Request(
        config.OLLAMA_HOST + "/api/chat",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                return _clean(json.loads(resp.read())["message"])
        except urllib.error.HTTPError as e:
            # 5xx is usually a transient VRAM/model-load hiccup → wait and retry once.
            if e.code >= 500 and attempt + 1 < attempts:
                time.sleep(2)
                continue
            raise RuntimeError(f"Ollama error {e.code}: {e.reason}")
        except urllib.error.URLError as e:
            raise RuntimeError(
                f"Could not reach Ollama at {config.OLLAMA_HOST} — is it running? ({e.reason})"
            )
