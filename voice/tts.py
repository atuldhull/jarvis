"""Voice — text-to-speech, bilingual.

Picks the voice by the reply's language: Hindi (Devanagari script) → Indian voice
(config.PIPER_MODEL_HI), everything else → British voice (config.PIPER_MODEL). Falls
back to Windows' built-in speech if Piper fails. More voices at
huggingface.co/rhasspy/piper-voices.
"""

import re
import wave

import config

_voices = {}
_DEVANAGARI = re.compile(r"[ऀ-ॿ]")  # Hindi script range


def _load(path):
    if path not in _voices:
        from piper import PiperVoice

        _voices[path] = PiperVoice.load(path)
    return _voices[path]


def say(text: str):
    try:
        import winsound

        # Hindi script → Indian voice; otherwise the British voice.
        path = config.PIPER_MODEL_HI if _DEVANAGARI.search(text) else config.PIPER_MODEL
        with wave.open("_tts.wav", "wb") as wav_file:
            _load(path).synthesize_wav(text, wav_file)
        winsound.PlaySound("_tts.wav", winsound.SND_FILENAME)  # blocks until done speaking
    except Exception:
        _say_windows(text)  # fall back to the built-in voice if Piper fails


def _say_windows(text: str):
    import subprocess

    safe = text.replace("'", "''")
    subprocess.run([
        "powershell", "-NoProfile", "-Command",
        "Add-Type -AssemblyName System.Speech; "
        f"(New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{safe}')",
    ])
