"""Headless voice-stack check — loads the STT + wake-word models and imports TTS.

No microphone, no sound playback (so it's quiet). Confirms the voice libraries and
models are working; the actual listen/speak loop is voice_main.py.

Run:  py test_voice.py
"""

import sys

sys.stdout.reconfigure(encoding="utf-8")

import config

print("=== STT (faster-whisper) — loading", config.STT_MODEL, "===")
from ears.stt import STT

STT()
print("STT model loaded ✅")

print("\n=== Wake word (openWakeWord) ===")
from ears.wakeword import WakeWord

WakeWord()
print("wake-word model loaded ✅")

print("\n=== TTS import ===")
from voice import tts  # noqa: F401

print("tts import OK ✅ (not speaking, to stay quiet)")

print("\nVOICE STACK LOADS ✅  (run voice_main.py with a mic + speakers)")
