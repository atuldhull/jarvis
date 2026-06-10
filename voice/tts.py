"""Voice — text-to-speech. Sarvam (Indian languages) first, local Piper fallback.

The reply's language is read from its script: Kannada → kn, Devanagari → hi, else en.
Sarvam (if a key is set) speaks all three naturally — including Kannada, which the local
Piper voices can't. Without Sarvam it falls back to Piper (British for English, Indian for
Hindi) and finally the built-in Windows voice. More Piper voices: huggingface.co/rhasspy/piper-voices.
"""

import re
import wave

import config
from voice import sarvam

_voices = {}
_DEVANAGARI = re.compile(r"[ऀ-ॿ]")   # Hindi
_KANNADA = re.compile(r"[ಀ-೿]")      # Kannada


def _lang_of(text: str) -> str:
    if _KANNADA.search(text):
        return "kn"
    if _DEVANAGARI.search(text):
        return "hi"
    return "en"


def say(text: str):
    if not text:
        return
    lang = _lang_of(text)
    # Sarvam first (natural Indian voices incl. Kannada); else the local stack.
    if sarvam.available():
        audio = sarvam.tts(text, lang)
        if audio:
            _play_bytes(audio)
            return
    _piper(text, lang)


def synth_bytes(text: str):
    """Return WAV bytes for `text` (Sarvam if available, else Piper) WITHOUT playing it.

    Used by the LiveKit pipeline, which wants the audio bytes rather than speaker output.
    Returns None if nothing could synthesize it (e.g. Kannada with no Sarvam key).
    """
    if not text:
        return None
    lang = _lang_of(text)
    if sarvam.available():
        audio = sarvam.tts(text, lang)
        if audio:
            return audio
    if lang == "kn":
        return None  # no local Kannada voice
    try:
        import io
        path = config.PIPER_MODEL_HI if lang == "hi" else config.PIPER_MODEL
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wav_file:
            _load(path).synthesize_wav(text, wav_file)
        return buf.getvalue()
    except Exception:
        return None


def _play_bytes(wav_bytes: bytes):
    import winsound
    with open("_tts.wav", "wb") as f:
        f.write(wav_bytes)
    winsound.PlaySound("_tts.wav", winsound.SND_FILENAME)  # blocks until done


def _load(path):
    if path not in _voices:
        from piper import PiperVoice
        _voices[path] = PiperVoice.load(path)
    return _voices[path]


def _piper(text: str, lang: str):
    # Piper has no Kannada voice, so Kannada without Sarvam goes to the Windows voice.
    if lang == "kn":
        _say_windows(text)
        return
    try:
        import winsound
        path = config.PIPER_MODEL_HI if lang == "hi" else config.PIPER_MODEL
        with wave.open("_tts.wav", "wb") as wav_file:
            _load(path).synthesize_wav(text, wav_file)
        winsound.PlaySound("_tts.wav", winsound.SND_FILENAME)
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
