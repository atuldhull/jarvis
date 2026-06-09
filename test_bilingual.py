"""Test bilingual: brain replies in the user's language; TTS picks the matching voice."""

import re
import sys
import wave

sys.stdout.reconfigure(encoding="utf-8")

import config
from brain.agent import Agent
from voice.tts import _DEVANAGARI, _load

# --- Brain: should reply in Hindi when spoken to in Hindi ---
a = Agent()
print("EN:", a.run("yo what's up bro"))
a.reset()
hi = a.run("भाई तू कैसा है? एक लाइन में बता।")  # "bro how are you? tell in one line"
print("HI:", hi)
print("HI reply is in Devanagari script:", bool(re.search(r"[ऀ-ॿ]", hi)))

# --- TTS: should pick Hindi voice for Devanagari, British for English ---
print("\nVoice selection:")
for txt in ["All systems operational, sir.", "सब कुछ ठीक है सर।"]:
    path = config.PIPER_MODEL_HI if _DEVANAGARI.search(txt) else config.PIPER_MODEL
    with wave.open("_t.wav", "wb") as f:
        _load(path).synthesize_wav(txt, f)
    print(f"  {txt[:20]!r:24} -> {path}")
