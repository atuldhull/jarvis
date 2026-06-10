"""Sarvam — optional cloud STT/TTS for Indian languages (Hindi, Kannada, Hinglish).

When a Sarvam key is configured and a call succeeds, JARVIS hears and speaks Indian
languages far better than the local stack. EVERY function returns None on any failure
(no key, offline, bad response), so the caller falls straight back to local
faster-whisper / Piper — Sarvam can never break the voice loop. Stdlib HTTP only.

Key comes from env SARVAM_KEY or keys.json ("sarvam": ["..."]). Get one free at
https://dashboard.sarvam.ai. API shapes follow Sarvam's docs; verify live once you add
a key (a wrong model/speaker name just fails over to local).
"""

import base64
import json
import os
import urllib.error
import urllib.request
import uuid

import config

_API = "https://api.sarvam.ai"
_LANG_CODE = {"en": "en-IN", "hi": "hi-IN", "kn": "kn-IN", "ta": "ta-IN", "te": "te-IN"}
_key_cache = None


def _key():
    global _key_cache
    if _key_cache is None:
        key = os.environ.get("SARVAM_KEY", "").strip()
        if not key:
            path = getattr(config, "KEYS_FILE", "keys.json")
            if os.path.exists(path):
                try:
                    with open(path, encoding="utf-8") as f:
                        arr = json.load(f).get("sarvam", []) or []
                    key = next((k.strip() for k in arr if k and "PASTE_" not in k), "")
                except Exception:
                    key = ""
        _key_cache = key
    return _key_cache or None


def available():
    return getattr(config, "SARVAM_ENABLED", True) and _key() is not None


def stt(wav_path):
    """Transcribe a wav via Sarvam. Returns (text, lang2) or None on any failure."""
    key = _key()
    if not key:
        return None
    try:
        with open(wav_path, "rb") as f:
            audio = f.read()
        boundary = "----jarvis" + uuid.uuid4().hex
        head = []
        for name, value in (("model", getattr(config, "SARVAM_STT_MODEL", "saarika:v2")),
                            ("language_code", "unknown")):  # auto-detect the language
            head.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\""
                        f"\r\n\r\n{value}\r\n".encode())
        head.append((f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
                     f"filename=\"audio.wav\"\r\nContent-Type: audio/wav\r\n\r\n").encode())
        body = b"".join(head) + audio + f"\r\n--{boundary}--\r\n".encode()
        req = urllib.request.Request(_API + "/speech-to-text", data=body, headers={
            "api-subscription-key": key,
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        text = (data.get("transcript") or "").strip()
        lang = (data.get("language_code") or "en-IN").split("-")[0]  # "hi-IN" -> "hi"
        return (text, lang) if text else None
    except Exception:
        return None


def tts(text, lang="en"):
    """Synthesize speech via Sarvam. Returns wav bytes, or None on any failure."""
    key = _key()
    if not key:
        return None
    try:
        body = json.dumps({
            "inputs": [text],
            "target_language_code": _LANG_CODE.get(lang, "en-IN"),
            "speaker": getattr(config, "SARVAM_TTS_SPEAKER", "anushka"),
            "model": getattr(config, "SARVAM_TTS_MODEL", "bulbul:v2"),
        }).encode("utf-8")
        req = urllib.request.Request(_API + "/text-to-speech", data=body, headers={
            "api-subscription-key": key, "Content-Type": "application/json",
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            audios = json.loads(resp.read()).get("audios") or []
        return base64.b64decode(audios[0]) if audios else None
    except Exception:
        return None
