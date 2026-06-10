"""The Model Router — the resource manager of the operation.

One call, `chat(messages, tools, options)`, decides WHICH brain answers:

  * walk the providers in config.PROVIDER_PRIORITY (gemini → groq → openrouter → local);
  * for a cloud provider, pick the least-used healthy key from the pool;
  * on a rate-limit / quota / auth / transient error, bench that key and try the
    next key, then the next provider — never the user;
  * if the internet is unreachable, skip the cloud entirely and use local Ollama;
  * benched keys heal on their own (their cooldown expires) and rejoin the pool.

With no cloud keys configured it simply always lands on `local`, so JARVIS behaves
exactly as it does today until you add keys. Returns one canonical assistant
message (see providers.py) regardless of who answered.
"""

import collections
import sys
import time

import config
from brain import providers
from brain.keystore import KeyStore


class ModelRouter:
    def __init__(self):
        self.store = KeyStore()
        self.provider_cooldown = {}                       # provider -> wall-clock retry time
        self.calls = collections.Counter()                # provider -> successful calls
        self.route_log = collections.deque(maxlen=50)     # recent decisions, for the dashboard
        self.last_route = ""

    # ── helpers ───────────────────────────────────────────────────────────────
    def _log(self, line):
        self.route_log.append(line)
        if getattr(config, "ROUTER_VERBOSE", True):
            print(f"[router] {line}", file=sys.stderr)

    def _provider_ready(self, provider, now):
        return now >= self.provider_cooldown.get(provider, 0)

    def _online_providers(self):
        """Cloud providers in priority order that actually have keys."""
        if not getattr(config, "ROUTER_ENABLED", True):
            return []
        return [p for p in config.PROVIDER_PRIORITY
                if p != "local" and self.store.has(p)]

    # ── the one entry point ─────────────────────────────────────────────────────
    def chat(self, messages, tools=None, options=None):
        opts = dict(options or {})
        models = config.PROVIDER_MODELS
        offline_this_turn = False
        last_err = None

        for provider in config.PROVIDER_PRIORITY:
            now = time.time()

            if provider == "local":
                try:
                    msg, latency, _ = providers.call(
                        "local", models.get("local", config.MODEL), messages, tools, opts, None)
                    self.calls["local"] += 1
                    self.last_route = "local"
                    return msg
                except Exception as e:                    # Ollama itself is down → out of options
                    last_err = e
                    self._log(f"local failed: {e}")
                    continue

            # ── a cloud provider ──
            if not getattr(config, "ROUTER_ENABLED", True):
                continue
            if offline_this_turn or not self._provider_ready(provider, now):
                continue
            if not self.store.has(provider):
                continue

            # Try each key in turn until one works or they're all benched.
            for _ in range(len(self.store._keys.get(provider, []))):
                key = self.store.pick(provider, now)
                if key is None:
                    break  # every key for this provider is on cooldown
                try:
                    msg, latency, tokens = providers.call(
                        provider, models[provider], messages, tools, opts, key.value)
                    key.record_success(latency, tokens)
                    self.calls[provider] += 1
                    self.last_route = key.label
                    if self.last_route != "local":
                        self._log(f"served by {key.label} ({round(latency)}ms)")
                    return msg
                except providers.Offline as e:
                    # No internet → no cloud will work this turn. Drop to local.
                    self.provider_cooldown[provider] = now + config.COOLDOWN_OFFLINE
                    offline_this_turn = True
                    last_err = e
                    self._log(f"{provider} unreachable (offline) → falling back to local")
                    break
                except providers.AuthError as e:
                    key.bench(config.COOLDOWN_AUTH, "auth")
                    last_err = e
                    self._log(f"{key.label} bad key → benched, trying next")
                except providers.QuotaExceeded as e:
                    key.bench(config.COOLDOWN_QUOTA, "quota")
                    last_err = e
                    self._log(f"{key.label} quota exhausted → benched, trying next")
                except providers.RateLimited as e:
                    key.bench(config.COOLDOWN_RATE_LIMIT, "rate-limit")
                    last_err = e
                    self._log(f"{key.label} rate-limited → benched, trying next")
                except providers.Transient as e:
                    key.bench(15, "transient")
                    last_err = e
                    self._log(f"{key.label} transient error → benched, trying next")
                except providers.ProviderError as e:
                    key.bench(60, "error")
                    last_err = e
                    self._log(f"{key.label} error: {str(e)[:80]} → benched, trying next")

        raise RuntimeError(f"All brains failed. Last error: {last_err}")

    # ── for the dashboard / debugging ───────────────────────────────────────────
    def stats(self):
        return {
            "enabled": getattr(config, "ROUTER_ENABLED", True),
            "priority": config.PROVIDER_PRIORITY,
            "calls": dict(self.calls),
            "last_route": self.last_route,
            "keys": self.store.snapshot(),
            "recent": list(self.route_log),
        }


# A single shared router for the whole app.
_router = None


def get_router():
    global _router
    if _router is None:
        _router = ModelRouter()
    return _router


def chat(messages, tools=None, options=None):
    """Drop-in replacement for ollama_client.chat — routed across all brains."""
    return get_router().chat(messages, tools=tools, options=options)
