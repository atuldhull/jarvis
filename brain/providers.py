"""Provider adapters — speak every API in one normalized voice.

Each provider wants a different request shape and returns a different response
shape. These adapters translate a single CANONICAL request (OpenAI-style messages
+ the tool schemas our registry already emits) into each provider's dialect, and
translate the reply back into one canonical assistant message the agent understands:

    {"role": "assistant", "content": str, "tool_calls": [
        {"id": str, "type": "function",
         "function": {"name": str, "arguments": "<json string>"}}]}

Adapters raise TYPED errors so the router knows how to react:
    AuthError      bad / blocked key      -> park the key for a long while
    RateLimited    per-minute rate limit  -> short cooldown, try another key
    QuotaExceeded  daily / quota used up  -> long cooldown
    Transient      5xx / timeout          -> quick retry or next key
    Offline        provider unreachable   -> skip the provider, lean on local
"""

import json
import socket
import threading
import time
import urllib.error
import urllib.request
import uuid

import config
from brain import ollama_client

# Local Ollama holds one model on a 6 GB GPU and serializes generations anyway, so
# we let only one local call run at a time — parallel orchestrator steps queue here
# instead of stacking generations and thrashing VRAM.
_LOCAL_LOCK = threading.Lock()


# ── Typed errors ──────────────────────────────────────────────────────────────
class ProviderError(Exception):
    pass


class AuthError(ProviderError):
    pass


class RateLimited(ProviderError):
    pass


class QuotaExceeded(ProviderError):
    pass


class Transient(ProviderError):
    pass


class Offline(ProviderError):
    pass


def _id():
    return "call_" + uuid.uuid4().hex[:12]


def _loads(s):
    if isinstance(s, dict):
        return s
    try:
        return json.loads(s or "{}")
    except Exception:
        return {}


def _norm_toolcalls(tcs):
    """Coerce a provider's tool_calls into the canonical shape, tolerating gaps."""
    out = []
    for tc in tcs or []:
        fn = tc.get("function") or {}
        out.append({
            "id": tc.get("id") or _id(),
            "type": "function",
            "function": {"name": fn.get("name", ""), "arguments": fn.get("arguments") or "{}"},
        })
    return out


# ── Raw HTTP with error classification ────────────────────────────────────────
def _post(url, headers, body, timeout=90):
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read())
        return payload, (time.time() - start) * 1000
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode("utf-8", "ignore")
        except Exception:
            detail = str(e.reason)
        low = detail.lower()
        key_marker = ("api_key_invalid" in low or "api key not valid" in low
                      or "invalid api key" in low or "unauthenticated" in low)
        if e.code == 401 or key_marker:
            raise AuthError(detail)
        if e.code == 403:
            # 403 can be a bad key OR a region/billing/project block. Don't park a
            # healthy key for a whole day over the latter — rest it like a quota issue.
            if "api key" in low or "api_key" in low or "permission" in low and "key" in low:
                raise AuthError(detail)
            raise QuotaExceeded(detail)
        if e.code == 429:
            if "quota" in low or "daily" in low or "exhaust" in low or "resource_exhausted" in low:
                raise QuotaExceeded(detail)
            raise RateLimited(detail)
        if e.code == 400:
            # Malformed request (bad tool/message shape) is OUR bug, not the key's —
            # treat as transient so we don't bench an otherwise-good key for a day.
            raise Transient(f"400: {detail[:200]}")
        if e.code >= 500:
            raise Transient(f"{e.code}: {detail[:200]}")
        raise ProviderError(f"{e.code}: {detail[:200]}")
    except urllib.error.URLError as e:
        # A connect-phase timeout arrives wrapped here — treat it as transient, not
        # "offline", so we don't bench the whole provider for being merely slow.
        if isinstance(e.reason, (TimeoutError, socket.timeout)):
            raise Transient("connect timeout")
        raise Offline(str(e.reason))  # DNS failure / connection refused / no internet
    except (TimeoutError, socket.timeout):
        raise Transient("timeout")


# ── OpenAI-compatible providers (Groq, OpenRouter) ────────────────────────────
_OPENAI_ENDPOINTS = {
    "groq": "https://api.groq.com/openai/v1/chat/completions",
    "openrouter": "https://openrouter.ai/api/v1/chat/completions",
}


def _to_openai_messages(messages):
    out = []
    for m in messages:
        role = m.get("role")
        if role == "tool":
            out.append({"role": "tool", "tool_call_id": m.get("tool_call_id", ""),
                        "content": m.get("content", "")})
        elif role == "assistant":
            a = {"role": "assistant", "content": m.get("content") or ""}
            if m.get("tool_calls"):
                a["tool_calls"] = m["tool_calls"]
            out.append(a)
        else:  # system / user
            out.append({"role": role, "content": m.get("content", "")})
    return out


def _openai_compat(provider, model, messages, tools, opts, key):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
    if provider == "openrouter":
        headers["HTTP-Referer"] = "http://localhost"   # OpenRouter asks for these
        headers["X-Title"] = "JARVIS"
    body = {
        "model": model,
        "messages": _to_openai_messages(messages),
        "temperature": opts.get("temperature", config.TEMPERATURE),
    }
    if tools:
        body["tools"] = tools
        body["tool_choice"] = "auto"
    payload, latency = _post(_OPENAI_ENDPOINTS[provider], headers, body)
    choices = payload.get("choices") or []
    if not choices:  # a 200 with an empty/odd body → fail over, don't crash
        raise Transient("no choices in response: " + json.dumps(payload)[:200])
    choice = choices[0].get("message") or {}
    msg = {
        "role": "assistant",
        "content": choice.get("content") or "",
        "tool_calls": _norm_toolcalls(choice.get("tool_calls")),
    }
    tokens = (payload.get("usage") or {}).get("total_tokens", 0)
    return msg, latency, tokens


# ── Gemini (native generateContent + function calling) ────────────────────────
def _gemini(model, messages, tools, opts, key):
    system_text = "\n\n".join(
        m.get("content", "") for m in messages if m.get("role") == "system"
    )
    contents = []
    for m in messages:
        role = m.get("role")
        if role == "system":
            continue
        if role == "user":
            contents.append({"role": "user", "parts": [{"text": m.get("content", "")}]})
        elif role == "assistant":
            parts = []
            if m.get("content"):
                parts.append({"text": m["content"]})
            for tc in m.get("tool_calls", []):
                fn = tc.get("function") or {}
                parts.append({"functionCall": {"name": fn.get("name", ""),
                                               "args": _loads(fn.get("arguments"))}})
            contents.append({"role": "model", "parts": parts or [{"text": ""}]})
        elif role == "tool":
            contents.append({"role": "user", "parts": [{
                "functionResponse": {
                    "name": m.get("name", "tool"),
                    "response": {"result": m.get("content", "")},
                }
            }]})

    body = {"contents": contents, "generationConfig": {
        "temperature": opts.get("temperature", config.TEMPERATURE)}}
    if system_text:
        body["system_instruction"] = {"parts": [{"text": system_text}]}
    if tools:
        body["tools"] = [{"function_declarations": [t["function"] for t in tools]}]

    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:generateContent?key={key}")
    payload, latency = _post(url, {"Content-Type": "application/json"}, body)

    candidates = payload.get("candidates") or []
    if not candidates:
        # Blocked by a safety filter or empty — let the router fail over.
        raise ProviderError("gemini returned no candidates: " + json.dumps(payload)[:200])
    parts = candidates[0].get("content", {}).get("parts", []) or []
    text, tool_calls = "", []
    for p in parts:
        if "text" in p:
            text += p["text"]
        if "functionCall" in p:
            fc = p["functionCall"]
            tool_calls.append({"id": _id(), "type": "function", "function": {
                "name": fc.get("name", ""),
                "arguments": json.dumps(fc.get("args", {})),
            }})
    msg = {"role": "assistant", "content": text, "tool_calls": tool_calls}
    tokens = (payload.get("usageMetadata") or {}).get("totalTokenCount", 0)
    return msg, latency, tokens


# ── Local Ollama (reuses the existing stdlib client, kept dependency-free) ─────
def _to_ollama_messages(messages):
    out = []
    for m in messages:
        role = m.get("role")
        if role == "assistant":
            a = {"role": "assistant", "content": m.get("content") or ""}
            if m.get("tool_calls"):
                a["tool_calls"] = [{"function": {
                    "name": (tc.get("function") or {}).get("name", ""),
                    "arguments": _loads((tc.get("function") or {}).get("arguments")),
                }} for tc in m["tool_calls"]]
            out.append(a)
        elif role == "tool":
            out.append({"role": "tool", "content": m.get("content", ""),
                        "tool_name": m.get("name", "")})
        else:
            out.append({"role": role, "content": m.get("content", "")})
    return out


def _ollama(model, messages, tools, opts, key=None):
    start = time.time()
    with _LOCAL_LOCK:  # one local generation at a time (single 6 GB GPU)
        raw = ollama_client.chat(model, _to_ollama_messages(messages), tools=tools, options=opts)
    latency = (time.time() - start) * 1000
    tool_calls = []
    for tc in raw.get("tool_calls") or []:
        fn = tc.get("function", {})
        args = fn.get("arguments", {})
        tool_calls.append({"id": _id(), "type": "function", "function": {
            "name": fn.get("name", ""),
            "arguments": args if isinstance(args, str) else json.dumps(args),
        }})
    msg = {"role": "assistant", "content": raw.get("content") or "", "tool_calls": tool_calls}
    return msg, latency, 0


# ── Dispatch ──────────────────────────────────────────────────────────────────
def call(provider, model, messages, tools, opts, key):
    """Run one completion on `provider`. Returns (canonical_message, latency_ms, tokens)."""
    if provider in _OPENAI_ENDPOINTS:
        return _openai_compat(provider, model, messages, tools, opts, key)
    if provider == "gemini":
        return _gemini(model, messages, tools, opts, key)
    if provider == "local":
        return _ollama(model, messages, tools, opts)
    raise ProviderError(f"unknown provider: {provider}")
